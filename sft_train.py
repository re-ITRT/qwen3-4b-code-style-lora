"""LoRA SFT 训练入口。

数据来自 config.json 的 data 段：questions[i] 作为 user，answers[i] 作为 assistant，
按索引一一对应。训练产物写到 sft.output_dir。
"""

import json

from datasets import Dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

from config import load_config, resolve
from load_model import get_model

config = load_config()


def build_dataset(questions_path, answers_path) -> Dataset:
    """把并行的 (question, answer) 两个列表拼成 messages 格式数据集。"""
    with open(questions_path, encoding="utf-8") as f:
        questions = json.load(f)
    with open(answers_path, encoding="utf-8") as f:
        answers = json.load(f)

    if len(questions) != len(answers):
        raise ValueError(
            f"questions({len(questions)}) 与 answers({len(answers)}) 条数不一致"
        )

    return Dataset.from_list(
        [
            {
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ]
            }
            for question, answer in zip(questions, answers)
        ]
    )


def sft_train():
    data = build_dataset(
        resolve(config["data"]["questions"]),
        resolve(config["data"]["answers"]),
    )
    print(f"训练样本: {len(data)} 条")

    peft_config = LoraConfig(**config["peft"])
    sft_config = SFTConfig(**config["sft"])
    tokenizer, model = get_model(config["model_id"])

    # TRL >= 0.12 起 tokenizer 关键字改名为 processing_class
    # （旧版 TRL 用 tokenizer=，新版直接传会报 unexpected keyword argument）
    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=data,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    trainer.train()
    save_dir = resolve(config["sft"]["output_dir"])
    trainer.save_model(str(save_dir))
    print(f"LoRA adapter saved to {save_dir}")


if __name__ == "__main__":
    sft_train()
