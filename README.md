# Qwen3-4B Code Style LoRA

Qwen3-4B 的 LoRA 适配器，用于统一模型输出 Python 代码时的格式与类型标注习惯。训练后的输出具备以下特征：

- 只输出一个 Markdown 代码块，不附加解释性文字；
- 入参使用 `collections.abc`、`numbers` 中的抽象类型，返回值使用具体实现类型；
- 空输入、除零、负数等边界条件显式处理，并附 docstring。

适配器权重发布在 [Hugging Face](https://huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora)。训练数据 129 条，在单卡 RX 7900 XT 上训练 5 个 epoch（325 个优化步），耗时约 3 分钟。

适配器只改变输出格式，不提升代码正确性——这一点在[已知问题](#已知问题)中有具体例子。

## 效果

评测使用 6 条固定 prompt：2 条与训练集同分布，2 条为同族但训练集未覆盖的主题，2 条为分布外提问。基座与适配器使用相同的 prompt、贪心解码和相同的 token 上限。

| 指标 | Qwen3-4B | + LoRA |
| --- | --- | --- |
| 只输出一个代码块 | 0 / 6 | 6 / 6 |
| 达到 `max_new_tokens` 上限被截断 | 2 / 6 | 0 / 6 |
| 输出可被 `ast.parse` 解析 | 5 / 5 | 5 / 6 |
| 参数与返回值均带类型标注的函数 | 0 / 9 | 9 / 9 |
| 平均输出长度 | 528 token | 251 token |

基座 6 条回答中有 1 条不含代码块，因此可解析性按 5 条统计；适配器有 1 条语法错误，按 6 条统计。

复现：

```bash
python eval/compare_style.py
```

完整输出见 [`eval/results/comparison.md`](eval/results/comparison.md)。

### 示例

输入：

```text
帮我写一个把秒数转成时分秒字符串的函数，秒数接受任意实数并向下取整，负数返回 00:00:00。
```

Qwen3-4B（431 token，节选）：先复述需求，再给出无类型标注的实现，最后附 5 个调用示例。

```python
def seconds_to_hms(seconds):
    if seconds < 0:
        return "00:00:00"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
```

+ LoRA（167 token，完整输出）：

```python
from numbers import Real


def seconds_to_hms(total: Real) -> str:
    """把秒数转成 00:00:00 形式，负数返回 00:00:00。"""
    seconds = int(total)
    if seconds <= 0:
        return '00:00:00'
    hours = seconds // 3600
    remainder = seconds % 3600
    minutes = remainder // 60
    return f'{hours:02d}:{minutes:02d}:{seconds % 60:02d}'


if __name__ == '__main__':
    print(seconds_to_hms(3661))
    print(seconds_to_hms(-5))
```

## 训练数据

`train/train.json`，129 条 `messages` 记录，每条包含一轮 user / assistant 对话：

- user：一句中文需求描述；
- assistant：一个完整可运行的 Python 文件，整体放在一个 python 代码块里。

覆盖字符串与路径处理、可迭代对象工具函数、数值计算、JSON/JSONL 读写、scikit-learn 风格 estimator。未覆盖类、异步、网络请求与算法题。

## 训练

```bash
pip install -r requirements.txt
python sft_train.py
```

全部参数在 `config.json`，脚本不写死超参：

| 项目 | 值 |
| --- | --- |
| LoRA | r=16, alpha=32, dropout=0.05, targets q/k/v/o |
| epoch | 5（325 个优化步） |
| batch | per_device 1 × gradient_accumulation 2 |
| learning rate | 2e-4 |
| max_length | 2048 |
| loss | assistant-only |
| 框架 | transformers 5.x / peft 0.21 / trl 1.17 |
| 硬件 | AMD Radeon RX 7900 XT（ROCm），约 3 分钟 |

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

messages = [{"role": "user", "content": "帮我写一个把秒数转成时分秒字符串的函数。"}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
output_ids = model.generate(
    **inputs, max_new_tokens=1024, do_sample=False, pad_token_id=tokenizer.pad_token_id
)
print(tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

命令行交互：`python test.py`。推理和训练共用 `config.json` 的 `generate` 段。

## 评测

```bash
python eval/compare_style.py          # 重新生成两侧输出并计算指标
python eval/compare_style.py --reuse  # 不加载模型，只用已有输出重算指标
```

评测 prompt 固定在 `eval/prompts.json`，结果写入 `eval/results/`：`comparison.md` 为逐题对照，`summary.md` 为指标汇总，`comparison.json` 为原始输出。

## 目录

```
.
├── config.json         # 模型、生成、LoRA、SFT 配置
├── config.py           # 配置读取与 generate 参数派生
├── load_model.py       # 模型下载与加载（本地缓存优先）
├── sft_train.py        # LoRA SFT 训练
├── test.py             # 命令行推理
├── train/train.json    # 训练样本
├── eval/               # 评测脚本、prompt 与结果
└── docs/               # 模型卡、发布记录
```

## 已知问题

- **分布外退化**。训练集不含类，让它写 sklearn 兼容的随机森林时，适配器会把签名写成
  `self, X: Sequence[Sequence[Real]] -> Sequence[int]`，箭头混入参数列表，代码无法编译。
- **风格溢出**。非代码问题（例如"解释一下 GIL"）也会被回答成代码块，而不是解释文字。
- **没有 dev 划分**。训练配置为 `save_strategy: "no"` 且未设 `eval_strategy`，因此没有损失曲线，5 epoch 是经验值而非实测最优。
- **仅验证中文 prompt**，英文输入未测。

## 后续工作
优化数据集生成方式:
- 不再由上游agent通过提示词生成代码，而是在模型原始输出中将代码替换code style，作为训练样本，以达到只优化模型代码风格的目标。
- 添加更多场景，不同编程语言的代码生成，参照google风格guide。


## 许可

- 代码与适配器：[Apache-2.0](LICENSE)，基座 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) 同为 Apache-2.0，见 [NOTICE](NOTICE)。
- 数据集 `train/train.json`：CC BY 4.0。

## 作者

毛治钦（Leo Postel）· [GitHub](https://github.com/re-ITRT) · [Hugging Face](https://huggingface.co/postel-MaoZhiqin)

基于 Qwen3-4B（Alibaba Cloud, Apache-2.0）训练。
