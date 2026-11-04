"""配置加载与派生：所有脚本统一从这里读 config.json。

config.json 各段用途：
- model_id：基座模型
- data：训练数据（questions 为 user 侧，answers 为 assistant 侧，按索引对应）
- generate：原样展开给 model.generate(**kwargs)
- peft / sft：原样展开给 LoraConfig / SFTConfig

JSON 没有注释，这里约定 generate.pad_token_id 写 null 表示
"用 tokenizer 自己的 pad_token_id"。
"""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


def load_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """读取配置文件；默认读本文件同目录的 config.json。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve(path: str | Path) -> Path:
    """把配置里的相对路径解析成仓库内绝对路径，不受执行目录影响。"""
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p).resolve()


def generation_kwargs(config: dict[str, Any], tokenizer: Any) -> dict[str, Any]:
    """把 config["generate"] 转成 model.generate() 的关键字参数。"""
    kwargs: dict[str, Any] = dict(config.get("generate") or {})
    if kwargs.get("pad_token_id") is None:
        kwargs["pad_token_id"] = tokenizer.pad_token_id
    return kwargs
