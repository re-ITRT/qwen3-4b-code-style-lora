"""用基座模型批量回答 data/questions.json，产出未做风格化的原始回答。

这是数据流水线的第一步：questions -> raw answers，之后在此基础上只重写代码块，
得到 data/style_answers.json 用于 SFT。

用法：
    ./.venv/bin/python scripts/generate_raw.py [--limit 5]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from config import generation_kwargs, load_config, resolve  # noqa: E402
from load_model import get_model  # noqa: E402

config = load_config()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 条，便于抽样")
    parser.add_argument(
        "--out", default="./outputs/generated/raw_answers.json", help="输出路径"
    )
    args = parser.parse_args()

    questions = json.loads(
        resolve(config["data"]["questions"]).read_text(encoding="utf-8")
    )
    if args.limit:
        questions = questions[: args.limit]

    tokenizer, model = get_model(config["model_id"])
    model.eval()
    gen_kwargs = generation_kwargs(config, tokenizer)

    answers = []
    with torch.no_grad():
        for i, question in enumerate(questions, 1):
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": question}],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = tokenizer(text, return_tensors="pt").to(model.device)
            output_ids = model.generate(**inputs, **gen_kwargs)
            new_ids = output_ids[0][inputs["input_ids"].shape[1] :]
            answers.append(tokenizer.decode(new_ids, skip_special_tokens=True))
            print(f"[{i}/{len(questions)}] {question[:40]}", flush=True)

    out_path = resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已写入 {out_path}")


if __name__ == "__main__":
    main()
