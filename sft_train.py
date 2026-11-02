from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

from config import load_config
from load_model import get_model

config = load_config()


def sft_train():
    data = load_dataset("json", data_files=config["data_path"])["train"]
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
    save_dir = config["sft"]["output_dir"]
    trainer.save_model(save_dir)
    print(f"LoRA adapter saved to {save_dir}")


if __name__ == "__main__":
    sft_train()
