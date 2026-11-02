---
license: apache-2.0
base_model: Qwen/Qwen3-4B
library_name: peft
language:
  - zh
  - en
tags:
  - code-generation
  - lora
  - sft
  - qwen3
pipeline_tag: text-generation
---

# Qwen3-4B Code Style LoRA

## 模型描述

在 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) 上用 129 条自建样本做 LoRA SFT，
把一个特定的 Python 代码风格克隆到模型上：

- 只输出**一个** ` ```python ` 代码块，不夹带任何解释文字；
- 参数用「宽进严出」的类型标注：入参用最弱的抽象类型（`Iterable` / `Mapping` / `Real`），
  返回值用最具体的实现类型（`list` / `dict` / `float` / `Path`）；
- 每个函数带 `"""docstring"""`，边界条件（空输入、除零、负数）显式处理。

> 注意：这是**风格迁移**，不是能力增强。基座不会因为这次微调变得更会写代码。

## 训练数据

- 129 条 `messages` 格式样本：`user` 一句中文需求，`assistant` 一个完整可运行的 Python 文件
- 题型覆盖：字符串/路径处理、可迭代对象工具、数值计算、JSON/JSONL 读写、scikit-learn 风格 estimator
- 数据格式与内容见训练仓库的 `train/train.json`

## 训练配置

| 项目 | 值 |
| --- | --- |
| LoRA | r=16, alpha=32, dropout=0.05 |
| target_modules | q_proj, k_proj, v_proj, o_proj |
| epochs | 5（129 条 × 5 = 645 个样本，325 个优化步） |
| batch | per_device=1, gradient_accumulation=2 |
| learning_rate | 2e-4 |
| max_length | 2048 |
| loss | assistant-only（只对 assistant 回复算 loss） |
| 框架 | transformers 5.x + peft 0.21 + trl 1.17 |
| 硬件 | AMD Radeon RX 7900 XT（ROCm），单卡约 3 分钟 |

## 使用方法

```python
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "Qwen/Qwen3-4B"
tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype="auto", device_map="auto")
model = PeftModel.from_pretrained(base, "postel-MaoZhiqin/qwen3-4b-code-style-lora").merge_and_unload()
model.eval()

prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": "帮我写一个把秒数转成时分秒字符串的函数。"}],
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=600, do_sample=False)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

## 局限

- 只在小工具函数上训练；类、网络、算法题属于分布外，会退化甚至编造 API。已知例子：让它写
  `sklearn` 兼容的随机森林时会引用 `BaseForest`、`_get_n_features` 等并不存在的接口。
- 只提升了格式与风格的一致性，**不提升代码正确性**。
- 训练集只有 129 条且没有 dev 划分，无法量化过拟合；超过 5 epoch 容易变成背诵训练答案。
- 仅在中文 prompt 上验证过。

## 作者

毛治钦（Leo Postel）· GitHub [@re-ITRT](https://github.com/re-ITRT)

## 致谢

基于 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)（Alibaba Cloud, Apache-2.0）。
