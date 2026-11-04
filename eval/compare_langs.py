"""多语言风格对比：基座 Qwen3-4B vs 重训后的 LoRA 适配器。

同一批 prompt（Python / C++ / Kotlin / C#），greedy 解码，两侧参数完全一致。

用法：
    ./.venv/bin/python eval/compare_langs.py
    ./.venv/bin/python eval/compare_langs.py --reuse   # 只用已有输出重算指标

产物（默认写到 eval/results/langs/）：
    comparison.json  原始输出 + 指标
    comparison.md    逐题对照
    summary.md       汇总
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
from peft import PeftModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import load_config, resolve  # noqa: E402
from load_model import get_model  # noqa: E402

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)

ALIASES = {
    "python": {"python", "py", "python3"},
    "cpp": {"cpp", "c++", "cc", "cxx"},
    "kotlin": {"kotlin", "kt"},
    "csharp": {"csharp", "c#", "cs"},
}

# 用于判断“输出到底是不是这个语言”
MARKERS = {
    "python": ("def ", "import ", "self."),
    "cpp": ("#include", "std::", "int main"),
    "kotlin": ("fun ", "val ", "var ", "println("),
    "csharp": ("using System", "namespace", "Console.", "static void Main"),
}

CPP_COMPILERS = ("g++", "clang++")


def render_prompt(tokenizer, user: str) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


@torch.no_grad()
def generate(model, tokenizer, prompt: str, max_new_tokens: int) -> str:
    inputs = tokenizer(render_prompt(tokenizer, prompt), return_tensors="pt").to(
        model.device
    )
    output_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
    )
    new_ids = output_ids[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_ids, skip_special_tokens=True).strip()


def cpp_syntax_ok(code: str) -> tuple[bool | None, str]:
    """用 g++/clang++ 做语法检查；编译器不可用时返回 None。"""
    for cc in CPP_COMPILERS:
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".cpp", delete=False) as f:
                f.write(code)
                path = f.name
            proc = subprocess.run(
                [cc, "-std=c++17", "-fsyntax-only", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            Path(path).unlink(missing_ok=True)
            if proc.returncode == 0:
                return True, ""
            msg = (proc.stderr or "").strip().splitlines()
            return False, (msg[0] if msg else "编译失败")[:160]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None, "本机无 C++ 编译器"


def analyze(text: str, lang: str, tokenizer) -> dict:
    fences = FENCE_RE.findall(text)
    blocks = [(info.lower().strip(), body) for info, body in fences]
    expected = ALIASES[lang]

    tagged = [b for info, b in blocks if info in expected]
    code = "\n\n".join(tagged) if tagged else (blocks[0][1] if blocks else "")
    prose = FENCE_RE.sub("", text).strip()
    truncated = text.count("```") % 2 == 1

    first_tag = blocks[0][0] if blocks else ""
    lang_match = first_tag in expected

    # 用标记词判断实际写的是不是这个语言
    marks = [m for m in MARKERS[lang] if m in code]
    marker_hits = len(marks)

    others = {k: v for k, v in MARKERS.items() if k != lang}
    foreign = [k for k, ms in others.items() if sum(m in code for m in ms) >= 2]

    balanced = code.count("{") == code.count("}") and code.count("(") == code.count(")")

    compiles: bool | None = None
    compile_msg = ""
    if code and lang == "python":
        try:
            ast.parse(code)
            compiles = True
        except SyntaxError as e:
            compiles = False
            compile_msg = f"line {e.lineno}: {e.msg}"
    elif code and lang == "cpp":
        compiles, compile_msg = cpp_syntax_ok(code)
    else:
        compile_msg = "本机无编译器" if code else ""

    return {
        "tokens": len(tokenizer(text, add_special_tokens=False)["input_ids"]),
        "fence_tag": first_tag or "（无标签）",
        "lang_match": lang_match,
        "single_block": len(blocks) == 1 and not prose and not truncated,
        "truncated": truncated,
        "prose_chars": len(prose),
        "marker_hits": marker_hits,
        "foreign_lang": ",".join(foreign) or "",
        "balanced": balanced,
        "compiles": compiles,
        "compile_msg": compile_msg,
    }


def fmt(m: dict) -> str:
    comp = "—" if m["compiles"] is None else ("通过" if m["compiles"] else "失败")
    comp += f"（{m['compile_msg']}）" if m["compile_msg"] and not m["compiles"] else ""
    return (
        f"标签={m['fence_tag']} | 语言匹配={m['lang_match']} | 单代码块={m['single_block']}"
        f" | 截断={m['truncated']} | 括号平衡={m['balanced']} | 风格标记={m['marker_hits']}"
        f" | 编译/解析={comp} | {m['tokens']} token"
        + (f" | 混入其他语言={m['foreign_lang']}" if m["foreign_lang"] else "")
    )


def wrap(text: str) -> str:
    return "````text\n" + text + "\n````\n"


def write_reports(results: list[dict], meta: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "comparison.json").write_text(
        json.dumps({"meta": meta, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 多语言对比：基座 Qwen3-4B vs LoRA 适配器",
        "",
        f"- 基座：`{meta['model_id']}`；适配器：`{meta['adapter']}`",
        f"- 解码：greedy，max_new_tokens={meta['max_new_tokens']}",
        "",
        "---",
        "",
    ]
    for r in results:
        lines += [
            f"## {r['id']}（{r['lang']}）",
            "",
            f"> {r['prompt']}",
            "",
            f"- 基座：{fmt(r['base_metrics'])}",
            f"- 适配器：{fmt(r['tuned_metrics'])}",
            "",
            "### 基座输出",
            "",
            wrap(r["base"]),
            "",
            "### 适配器输出",
            "",
            wrap(r["tuned"]),
            "",
            "---",
            "",
        ]
    (out_dir / "comparison.md").write_text("\n".join(lines), encoding="utf-8")

    summary = [
        "# 汇总",
        "",
        "| prompt | 语言 | 侧 | 语言匹配 | 单代码块 | 截断 | 括号平衡 | 编译/解析 | token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        for side, name in (("base_metrics", "基座"), ("tuned_metrics", "适配器")):
            m = r[side]
            comp = "—" if m["compiles"] is None else ("通过" if m["compiles"] else "失败")
            summary.append(
                f"| {r['id']} | {r['lang']} | {name} | {m['lang_match']} | "
                f"{m['single_block']} | {m['truncated']} | {m['balanced']} | {comp} | {m['tokens']} |"
            )
    (out_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def reuse(out_dir: Path) -> None:
    from transformers import AutoTokenizer

    from load_model import get_model_path

    config = load_config()
    data = json.loads((out_dir / "comparison.json").read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(get_model_path(config["model_id"]))
    for item in data["results"]:
        for side in ("base", "tuned"):
            item[f"{side}_metrics"] = analyze(item[side], item["lang"], tokenizer)
    write_reports(data["results"], data["meta"], out_dir)
    print(f"已重算指标：{out_dir}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", default=str(ROOT / "eval/prompts_langs.json"))
    parser.add_argument("--out", default=str(ROOT / "eval/results/langs"))
    parser.add_argument("--max-new-tokens", type=int, default=700)
    parser.add_argument("--adapter", default=None)
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    out_dir = Path(args.out)

    if args.reuse:
        reuse(out_dir)
        return

    config = load_config()
    adapter_dir = args.adapter or str(resolve(config["sft"]["output_dir"]))
    prompts = json.loads(Path(args.prompts).read_text(encoding="utf-8"))

    tokenizer, base_model = get_model(config["model_id"])
    base_model.eval()

    results = []
    for item in prompts:
        text = generate(base_model, tokenizer, item["prompt"], args.max_new_tokens)
        results.append(
            {**item, "base": text, "base_metrics": analyze(text, item["lang"], tokenizer)}
        )
        print(f"[base ] {item['id']}: ok", flush=True)

    tuned = PeftModel.from_pretrained(base_model, adapter_dir).merge_and_unload()
    tuned.eval()
    for item in results:
        text = generate(tuned, tokenizer, item["prompt"], args.max_new_tokens)
        item["tuned"] = text
        item["tuned_metrics"] = analyze(text, item["lang"], tokenizer)
        print(f"[tuned] {item['id']}: ok", flush=True)

    meta = {
        "model_id": config["model_id"],
        "adapter": adapter_dir,
        "max_new_tokens": args.max_new_tokens,
        "decoding": "greedy",
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "python": platform.python_version(),
    }
    write_reports(results, meta, out_dir)
    print(f"报告已写入 {out_dir}", flush=True)


if __name__ == "__main__":
    main()
