import os
from pathlib import Path

import dotenv

dotenv.load_dotenv()

from huggingface_hub import snapshot_download  # noqa: E402

HF_TOKEN = os.getenv("HF_TOKEN")

# 基座模型本地缓存目录，仓库内固定位置，不受执行目录影响
MODELS_DIR = Path(__file__).resolve().parent / "models"


def get_model_path(model_id: str = "Qwen/Qwen3-4B") -> Path:
    """本地已有模型就直接返回路径，否则下载到 models/。"""
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


def get_model(model_id: str = "Qwen/Qwen3-4B"):
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
