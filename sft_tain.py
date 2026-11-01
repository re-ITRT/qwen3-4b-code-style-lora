from load_model import get_model
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
import json

config = json.load(open("./config.json"))
model_id = config["model_id"]
data_path = config["data_path"]


data = load_dataset("json", data_files=data_path)["train"]

peft_config = LoraConfig(**config["peft"])

sft_config = SFTConfig(**config["sft"])


def sft_train():
    tokenizer, model = get_model(model_id)

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=data,
        peft_config=peft_config,
        tokenizer=tokenizer,
    )

    trainer.train()
    save_dir = config["sft"]["output_dir"]
    trainer.save_model(save_dir)
    print(f"LoRA adapter saved to {save_dir}")
if __name__ == "__main__":
    sft_train()