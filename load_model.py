import dotenv
dotenv.load_dotenv()
import os
from pathlib import Path

from huggingface_hub import snapshot_download

HF_TOKEN = os.getenv("HF_TOKEN")

# 本地缓存根目录：./models/<org>--<name>
MODELS_DIR = Path("./models")


def get_model_path(model_id: str = "Qwen/Qwen-3.5-4B") -> Path:
    """本地已有模型就直接返回路径，否则下载到 ./models。"""
    local_dir = MODELS_DIR / model_id.replace("/", "--")

    if (local_dir / "config.json").exists():
        print(f"本地已有模型，直接使用: {local_dir}")
        return local_dir

    print(f"本地未找到，开始下载 {model_id} -> {local_dir}")
    snapshot_download(
        repo_id=model_id,
        local_dir=str(local_dir),
        token=HF_TOKEN,
    )
    return local_dir


def get_model(model_id: str = "Qwen/Qwen-3.5-4B"):
    """下载/复用本地模型，返回 (tokenizer, model)。"""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_path = get_model_path(model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto"
    )
    return tokenizer, model


if __name__ == "__main__":
    tokenizer, model = get_model()
    print("模型加载完成")
