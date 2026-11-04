# Qwen3-4B Code Style LoRA

Qwen3-4B 的 LoRA 适配器，把 Python / C++ / Kotlin / C# 四种语言的代码输出统一到同一套风格：

- 先用一句中文说明函数做什么，再给出一个 Markdown 代码块；
- 参数用最贴切的抽象类型，返回值用具体类型；
- 空输入、除零、负数等边界条件显式处理。

训练数据 516 条 `(question, answer)` 对，覆盖四种语言。适配器权重发布在
[Hugging Face](https://huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora)。

适配器只统一格式与标注习惯，不提升基座的代码能力，具体反例见[已知问题](#已知问题)。

## 效果

基座与适配器使用相同 prompt、贪心解码、相同 token 上限，唯一变量是是否挂载 adapter。

### 多语言（9 条 prompt）

| 语言 | 条数 | 语言标签正确 | 平均 token（基座 → 适配器） | 编译/解析 |
| --- | --- | --- | --- | --- |
| Python | 3 | 3/3 | 466 → 226 | `ast.parse` 两侧均通过 |
| C++ | 2 | 2/2 | 407 → 224 | `g++ -fsyntax-only` 两侧均通过 |
| Kotlin | 2 | 2/2 | 451 → 240 | 本机无 kotlinc，未验证 |
| C# | 2 | 2/2 | 507 → 138 | 本机无 csc/dotnet，未验证 |

18 次生成里代码块语言标签全部正确，没有出现跨语言语法混用；平均输出从 459 降到 209 token。

### Python 细项（6 条 prompt）

| 指标 | Qwen3-4B | + LoRA |
| --- | --- | --- |
| 只输出一个代码块（无导语） | 0 / 6 | 0 / 6 |
| 达到 `max_new_tokens` 上限被截断 | 2 / 6 | 1 / 6 |
| 代码可被 `ast.parse` 解析 | 5 / 5 | 4 / 4 |
| 参数与返回值均带类型标注的函数 | 0 / 9 | 4 / 4 |
| 平均输出长度 | 528 token | 325 token |

两版的导语长度差别明显：基座平均 350+ 字符，适配器约 120 字符。适配器的目标格式是
「一句说明 + 一个代码块」，而不是零导语。

复现：

```bash
python eval/compare_langs.py   # 9 条多语言 prompt
python eval/compare_style.py   # 6 条 Python prompt
```

逐条原始输出见 [`eval/results/langs/comparison.md`](eval/results/langs/comparison.md) 与
[`eval/results/python/comparison.md`](eval/results/python/comparison.md)。

### 示例

输入：

```text
用 C++ 写一个按分隔符切分字符串的函数，返回 vector<string>，空输入返回空 vector。
```

Qwen3-4B（428 token，节选）：先复述需求，给实现，再补 `int main` 演示和一段「说明」。

```cpp
#include <iostream>
#include <vector>
#include <string>
#include <cctype>  // for std::is...
```

适配器（245 token）：同样一句引导语 + `### 示例代码：` + 单个代码块，函数签名和主逻辑不变。

```cpp
std::vector<std::string> split(const std::string& input, char delimiter) {
    std::vector<std::string> parts;
    std::string current;
    for (char symbol : input) {
        if (symbol == delimiter) {
            if (!current.empty()) {
                parts.push_back(current);
                current.clear();
            }
        } else {
            current.push_back(symbol);
        }
    }
    if (!current.empty()) {
        parts.push_back(current);
    }
    return parts;
}
```

## 数据

```
data/
├── questions.json      # 516 条中文需求（user 侧）
├── style_answers.json  # 516 条目标风格答案（assistant 侧，按索引对应）
├── samples/            # 同一道 KNN 在 Python / C++ / Kotlin / C# 下的风格参考
└── README.md           # 格式、流水线与许可
```

数据流水线：`questions` →（`scripts/generate_raw.py`）→ 基座原始回答 → 风格化改写 →
`style_answers` →（`sft_train.py`）→ adapter。原始回答只落在 `outputs/generated/`，不进仓库。

风格化改写的原则是**只改代码**：题面和解释文字沿用基座模型自己的输出，只把代码块重写成目标
风格。这样训练的是「同一段回答里代码该怎么写」，而不是让模型重新学怎么解释问题。

数据集以 CC BY 4.0 发布。

## 训练

```bash
pip install -r requirements.txt
python sft_train.py
```

参数在 `config.json`，脚本不写死超参：

| 项目 | 值 |
| --- | --- |
| LoRA | r=16, alpha=32, dropout=0.05, targets q/k/v/o |
| epoch | 5（258 步/epoch，共 1290 个优化步） |
| batch | per_device 1 × gradient_accumulation 2 |
| learning rate | 2e-4 |
| max_length | 2048 |
| loss | assistant-only |
| 框架 | transformers 5.x / peft 0.21 / trl 1.17 |
| 硬件 | AMD Radeon RX 7900 XT（ROCm） |

## 使用

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "Qwen/Qwen3-4B"
tokenizer = AutoTokenizer.from_pretrained(base_id)
model = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype="auto", device_map="auto")
model = PeftModel.from_pretrained(
    model, "postel-MaoZhiqin/qwen3-4b-code-style-lora"
).merge_and_unload()
model.eval()

messages = [{"role": "user", "content": "用 Kotlin 写一个把秒数转成 HH:MM:SS 的函数。"}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
output_ids = model.generate(
    **inputs, max_new_tokens=700, do_sample=False, pad_token_id=tokenizer.pad_token_id
)
print(tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

命令行交互：`python test.py`。推理和训练共用 `config.json` 的 `generate` 段。

## 目录

```
.
├── config.json         # 模型、数据、生成、LoRA、SFT 配置
├── config.py           # 配置读取、路径解析、generate 参数派生
├── load_model.py       # 模型下载与加载（models/ 本地缓存优先）
├── sft_train.py        # LoRA SFT 训练
├── test.py             # 命令行推理
├── scripts/
│   └── generate_raw.py # 用基座批量生成原始回答（数据流水线第一步）
├── data/               # 训练数据、风格参考与数据说明
├── eval/               # 两套对比脚本、prompt 与结果
├── outputs/            # 训练产物、生成结果（git 忽略）
└── docs/               # 模型卡、开源记录
```

`outputs/` 与 `models/` 不进版本库：前者放 adapter 和批量生成结果，后者是 8GB 基座缓存。

## 已知问题

- **类级别任务仍会失败**：让它写 sklearn 兼容的随机森林时，适配器输出会撞到 600 token 上限被截断
  （基座同样如此），这类题不在训练分布内。
- **C# 有时只给片段**：会输出缺 `using System;` 的静态方法，不能直接编译；基座版本反而带了完整类。
- **Kotlin / C# 未做编译验证**：本机没有 `kotlinc` 与 `csc`，只做了括号平衡和关键词检查。
- **没有 dev 划分**：训练配置未设 `eval_strategy`，5 epoch 是经验值，没有早停。
- **仅在中文 prompt 上验证**。

## 许可

- 代码与适配器：[Apache-2.0](LICENSE)，基座 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) 同为 Apache-2.0，见 [NOTICE](NOTICE)。
- 数据集 `data/`：CC BY 4.0。

## 作者

毛治钦（Leo Postel）· [GitHub](https://github.com/re-ITRT) · [Hugging Face](https://huggingface.co/postel-MaoZhiqin)

基于 Qwen3-4B（Alibaba Cloud, Apache-2.0）训练。
