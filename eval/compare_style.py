"""基座模型 vs LoRA 微调模型：同一批 prompt 的风格对比。

用法：
    ./.venv/bin/python eval/compare_style.py            # 完整跑一遍（要加载模型）
    ./.venv/bin/python eval/compare_style.py --reuse    # 只用已有输出重算指标

产物（默认写到 eval/results/）：
    comparison.json  完整结果，含两侧原始输出与指标
    comparison.md    逐题左右对照，便于贴到 README
    summary.md       汇总指标表

解码统一 greedy（do_sample=False），保证同一台机器上可复现。
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
import re
import sys
from pathlib import Path

import torch
from peft import PeftModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import load_config, resolve  # noqa: E402
from load_model import get_model  # noqa: E402

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)

# 训练集里高频出现的“风格指纹” import
STYLE_IMPORTS = (
    "from collections.abc import",
    "from numbers import",
    "from typing import",
    "from pathlib import Path",
    "from sklearn.base import",
)


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


def analyze(text: str, tokenizer) -> dict:
    """把一段回复拆成可比较的风格指标。"""
    fences = FENCE_RE.findall(text)
    code_blocks = [body for lang, body in fences if lang == "python"]
    code = "\n\n".join(code_blocks)
    prose = FENCE_RE.sub("", text).strip()
    truncated = text.count("```") % 2 == 1  # 代码块没闭合 = 撞到 token 上限被切断

    compiles: bool | None = None
    annotated: int | None = None
    n_funcs = 0
    if code:
        try:
            tree = ast.parse(code)
            compiles = True
        except SyntaxError:
            tree, compiles = None, False
        if tree is not None:
            funcs: list = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
            annotated = 0
            for node in funcs:
                args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                params_ok = all(
                    a.annotation is not None
                    for a in args
                    if a.arg not in {"self", "cls"}
                )
                annotated += params_ok and node.returns is not None
            n_funcs = len(funcs)
        else:
            n_funcs = len(re.findall(r"^\s*def \w+\(", code, re.M))

    return {
        "tokens": len(tokenizer(text, add_special_tokens=False)["input_ids"]),
        "has_code_block": bool(code_blocks),
        "n_fences": len(fences),
        "truncated": truncated,
        "single_code_block": (
            len(fences) == 1 and len(code_blocks) == 1 and not prose and not truncated
        ),
        "prose_chars": len(prose),
        "compiles": compiles,
        "n_funcs": n_funcs,
        "annotated_funcs": annotated,
        "has_style_import": any(s in code for s in STYLE_IMPORTS),
    }


def fmt_metrics(m: dict) -> str:
    ann = "—" if m["annotated_funcs"] is None else f"{m['annotated_funcs']}/{m['n_funcs']}"
    compiles = "—" if m["compiles"] is None else m["compiles"]
    return (
        f"单代码块={m['single_code_block']} | 可编译={compiles} | "
        f"全注解函数={ann} | 风格 import={m['has_style_import']} | "
        f"散文 {m['prose_chars']} 字符 | {m['tokens']} token"
        + (" | **截断**" if m["truncated"] else "")
    )


def wrap(text: str) -> str:
    return "````text\n" + text + "\n````\n"


def write_reports(results: list[dict], out_dir: Path, meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "comparison.json").write_text(
        json.dumps({"meta": meta, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 风格对比：基座 Qwen3-4B vs LoRA 微调",
        "",
        f"- 基座：`{meta['model_id']}`（未挂 adapter）",
        f"- 微调：`{meta['model_id']}` + LoRA `{meta['adapter']}`",
        "- 解码：greedy（`do_sample=False`），两侧完全相同的 prompt 与 token 上限",
        "",
        "---",
        "",
    ]
    for r in results:
        lines += [
            f"## {r['id']}（{r['tag']}）",
            "",
            f"> {r['prompt']}",
            "",
            "| | 指标 |",
            "| --- | --- |",
            f"| 基座 | {fmt_metrics(r['base_metrics'])} |",
            f"| 微调 | {fmt_metrics(r['tuned_metrics'])} |",
            "",
            "### 基座输出",
            "",
            wrap(r["base"]),
            "",
            "### 微调输出",
            "",
            wrap(r["tuned"]),
            "",
            "---",
            "",
        ]
    (out_dir / "comparison.md").write_text("\n".join(lines), encoding="utf-8")

    summary = [
        "# 汇总指标",
        "",
        "| prompt | 侧 | 单代码块 | 截断 | 可编译 | 全注解函数 | 风格 import | token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        for side in ("base", "tuned"):
            m = r[f"{side}_metrics"]
            ann = (
                "—"
                if m["annotated_funcs"] is None
                else f"{m['annotated_funcs']}/{m['n_funcs']}"
            )
            summary.append(
                f"| {r['id']} | {side} | {m['single_code_block']} | {m['truncated']} | "
                f"{m['compiles'] if m['compiles'] is not None else '—'} | {ann} | "
                f"{m['has_style_import']} | {m['tokens']} |"
            )
    (out_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def reuse(out_dir: Path) -> None:
    """只用已有 comparison.json 重算指标并重写报告（不加载模型）。"""
    from transformers import AutoTokenizer

    from load_model import get_model_path

    config = load_config()
    data = json.loads((out_dir / "comparison.json").read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(get_model_path(config["model_id"]))
    for item in data["results"]:
        for side in ("base", "tuned"):
            item[f"{side}_metrics"] = analyze(item[side], tokenizer)
    write_reports(data["results"], out_dir, data["meta"])
    print(f"已用已有输出重算指标：{out_dir}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", default=str(ROOT / "eval/prompts_style.json"))
    parser.add_argument("--out", default=str(ROOT / "eval/results/python"))
    parser.add_argument("--max-new-tokens", type=int, default=600)
    parser.add_argument("--adapter", default=None)
    parser.add_argument(
        "--reuse", action="store_true", help="不重新生成，只用已有输出重算指标"
    )
    args = parser.parse_args()
    out_dir = Path(args.out)

    if args.reuse:
        reuse(out_dir)
        return

    config = load_config()
    adapter_dir = args.adapter or str(resolve(config["sft"]["output_dir"]))
    prompts = json.loads(Path(args.prompts).read_text(encoding="utf-8"))
    max_new_tokens = args.max_new_tokens

    tokenizer, base_model = get_model(config["model_id"])
    base_model.eval()

    results = []
    for item in prompts:
        text = generate(base_model, tokenizer, item["prompt"], max_new_tokens)
        results.append(
            {
                **item,
                "base": text,
                "base_metrics": analyze(text, tokenizer),
            }
        )
        print(f"[base ] {item['id']}: ok", flush=True)

    # 挂 LoRA 并合并进基座权重，推理更快且没有额外 forward 开销
    tuned_model = PeftModel.from_pretrained(base_model, adapter_dir)
    tuned_model = tuned_model.merge_and_unload()
    tuned_model.eval()

    for item in results:
        text = generate(tuned_model, tokenizer, item["prompt"], max_new_tokens)
        item["tuned"] = text
        item["tuned_metrics"] = analyze(text, tokenizer)
        print(f"[tuned] {item['id']}: ok", flush=True)

    meta = {
        "model_id": config["model_id"],
        "adapter": adapter_dir,
        "max_new_tokens": max_new_tokens,
        "decoding": "greedy",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    write_reports(results, out_dir, meta)
    print(f"报告已写入 {out_dir}", flush=True)


if __name__ == "__main__":
    main()
