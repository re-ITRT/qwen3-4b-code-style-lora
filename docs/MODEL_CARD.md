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
  - cpp
  - kotlin
  - csharp
pipeline_tag: text-generation
---

# Qwen3-4B Code Style LoRA

## 模型描述

在 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) 上用 516 条自建样本做 LoRA SFT，
把 Python / C++ / Kotlin / C# 四种语言的代码输出统一到同一套风格：

- 先用一句中文说明函数做什么，再给**一个** Markdown 代码块；
- 参数使用最贴切的抽象类型（Python 用 `collections.abc` / `numbers`，其余语言用原生类型），
  返回值使用具体类型；
- 空输入、除零、负数等边界条件显式处理，Python 输出附 docstring。

适配器只统一格式与标注习惯，不提升基座本身的代码能力。

## 训练数据

- 516 条 `(question, answer)` 对：user 为中文需求，assistant 为改写后的目标风格答案；
- 覆盖 Python、C++、Kotlin、C# 四种语言，以字符串、数值、可迭代对象、文件 IO 等小工具函数为主；
- 数据流水线与许可见训练仓库的 `data/` 目录。

## 训练配置

| 项目 | 值 |
| --- | --- |
| LoRA | r=16, alpha=32, dropout=0.05 |
| target_modules | q_proj, k_proj, v_proj, o_proj |
| epochs | 5（258 步/epoch，共 1290 个优化步） |
| batch | per_device=1, gradient_accumulation=2 |
| learning_rate | 2e-4 |
| max_length | 2048 |
| loss | assistant-only |
| 框架 | transformers 5.x + peft 0.21 + trl 1.17 |
| 硬件 | AMD Radeon RX 7900 XT（ROCm） |

## 使用方法

```python
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "Qwen/Qwen3-4B"
tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype="auto", device_map="auto")
model = PeftModel.from_pretrained(
    base, "postel-MaoZhiqin/qwen3-4b-code-style-lora"
).merge_and_unload()
model.eval()

prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": "用 C++ 写一个按分隔符切分字符串的函数，返回 vector<string>。"}],
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=700, do_sample=False)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

## 评测

基座与适配器在同一批 prompt 上的对比（含 Python / C++ / Kotlin / C# 四种语言）见
训练仓库的 `eval/results/`，复现命令：

```bash
python eval/compare_langs.py
python eval/compare_style.py
```

## 局限

- 训练集覆盖的是小工具函数；类、异步、网络请求、算法题属于分布外，会退化甚至编造 API。
- 只统一格式，不提升代码正确性；C# 输出有时是缺 `using` 的片段而非可编译文件。
- 没有 dev 划分，5 epoch 是经验值，未做早停或最优 checkpoint 选择。
- 仅在中文 prompt 上验证。

## 作者

毛治钦（Leo Postel）· GitHub [@re-ITRT](https://github.com/re-ITRT)

基于 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)（Alibaba Cloud, Apache-2.0）训练。
