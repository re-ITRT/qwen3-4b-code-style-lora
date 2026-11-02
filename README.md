# Qwen3-4B 代码风格微调（LoRA SFT）

[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Base model](https://img.shields.io/badge/base-Qwen3--4B-6f42c1)](https://huggingface.co/Qwen/Qwen3-4B)
[![Method](https://img.shields.io/badge/method-LoRA%20SFT-orange)]()
[![GitHub](https://img.shields.io/badge/github-re--ITRT%2Fqwen3--4b--code--style--lora-black)](https://github.com/re-ITRT/qwen3-4b-code-style-lora)
[![HF Model](https://img.shields.io/badge/%F0%9F%A4%97-qwen3--4b--code--style--lora-yellow)](https://huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora)

用 **129 条自建样本** + **单卡 3 分钟**，把 Qwen3-4B 的代码输出风格克隆成
「只输出一个代码块 + 宽进严出的类型标注」的写法。

> 这不是能力增强，是**风格迁移**：模型不会因为这次微调变得更会写代码，
> 但会稳定地按指定格式和标注习惯输出。

## 效果预览

同一批 prompt、同一个基座、greedy 解码，只差一个 LoRA adapter：

### 指标

6 条固定 prompt（同分布 2 条 / 留出 2 条 / 分布外 2 条），greedy 解码，两侧 token 上限相同：

| 指标 | 基座 Qwen3-4B | + LoRA |
| --- | --- | --- |
| 只输出一个代码块 | 0 / 6 | **6 / 6** |
| 撞到 token 上限被截断 | 2 / 6 | **0 / 6** |
| 输出可解析为合法 Python | 5 / 5 | 5 / 6 |
| 参数与返回值全注解的函数 | 0 / 9 | **9 / 9** |
| 平均输出长度 | 528 token | **251 token**（−52%） |

基座侧 6 条里有 1 条完全没有代码块；微调侧有 1 条语法错误（见下面的反例）。

### 示例 1：同分布 prompt

> 帮我写一个把秒数转成时分秒字符串的函数，秒数接受任意实数并向下取整，负数返回 00:00:00。

**基座**（431 token：先解释、再给代码、再举 5 个例子，函数没有任何类型标注）

````text
当然可以！下面是一个将秒数转换为 `HH:MM:SS` 格式字符串的函数。这个函数会：

- 接受任意实数（如 `123.45`）作为输入。
- 先对秒数进行 **向下取整**（即 `floor`）。
- 如果秒数为负数，返回 `00:00:00`。

下面是 Python 实现：

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

### 示例：
...（后面还有 5 个 print 示例和一句“需要其他语言版本也可以告诉我”）
````

**微调**（167 token：只有代码块，入参用 `Real`，返回 `str`，边界条件显式处理）

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

### 示例 2：留出题型（训练集里完全没有网络编程）

> 帮我写一个带重试的 HTTP 请求函数，最多重试 3 次，失败时抛异常。

基座：先用一段话推荐 `requests` + `tenacity`，再给一个装饰器写法，函数无标注。
微调：直接一个代码块，`Callable[[], T] -> T`、`max_retries: int`、`delay: float` 全部标注，
还自己补了个 `SessionContext` 上下文管理器 —— **格式学到位了，但逻辑是否真对另说**
（`return T()` 这种写法就是它自己发挥的，不能直接用）。

### 反例：它也会翻车

让它写 `sklearn` 兼容的随机森林时，微调后的模型格式对了（单代码块、类风格），
但签名写错了，整段代码无法编译：

```python
    def predict(
        self, X: Sequence[Sequence[Real]] -> Sequence[int]
    ) -> np.ndarray:
```

`-> Sequence[int]` 被塞进了参数列表。这就是「风格迁移 ≠ 能力增强」最直接的证据。

完整的逐题对照（含原始输出）见 [eval/results/comparison.md](eval/results/comparison.md)。

## 风格长什么样

微调后的目标风格（来自训练集，`宽进严出`）：

```python
from collections.abc import Iterable
from numbers import Real


def safe_divide(a: Real, b: Real, default: Real = 0.0) -> float:
    """安全除法，除数为 0 时返回默认值。"""
    if b == 0:
        return float(default)
    return float(a) / float(b)
```

三条规则：

1. 只输出一个 ` ```python ` 代码块，不夹带解释文字；
2. 入参用最弱的抽象类型（`Iterable` / `Mapping` / `Real`），返回值用最具体的实现类型
   （`list` / `dict` / `float` / `Path`）；
3. 空输入、除零、负数这些边界条件显式处理，并写 `"""docstring"""`。

## 目录结构

```
.
├── config.json           # 唯一配置源：模型 / 生成 / LoRA / SFT
├── config.py             # 配置加载与生成参数派生
├── load_model.py         # 本地优先的模型下载与加载
├── sft_train.py          # LoRA SFT 训练入口
├── test.py               # 命令行对话推理
├── requirements.txt
├── .env.example          # HF_TOKEN / HF_ENDPOINT 模板
├── LICENSE  NOTICE       # Apache-2.0 + Qwen3-4B 来源声明
├── train/
│   └── train.json        # 129 条 SFT 样本（user 中文需求 + assistant 代码块）
├── eval/
│   ├── prompts.json      # 固定评测 prompt（同分布 / 留出 / 分布外）
│   ├── compare_style.py  # 基座 vs 微调 的自动对比（--reuse 只重算指标）
│   └── results/          # comparison.md / summary.md / comparison.json
└── docs/
    ├── MODEL_CARD.md     # 可直接上传 Hugging Face 的模型卡
    └── OPENSOURCE.md     # 开源发布与协议建议
```

## 快速开始

### 环境

```bash
git clone https://github.com/re-ITRT/qwen3-4b-code-style-lora.git
cd qwen3-4b-code-style-lora
python -m venv .venv && source .venv/bin/activate

# torch 按显卡单独装（这里是 ROCm 的例子）
pip install torch --index-url https://download.pytorch.org/whl/rocm6.2
pip install -r requirements.txt

cp .env.example .env    # 填 HF_TOKEN；国内可改 HF_ENDPOINT 为镜像
```

模型默认落在 `./models/<org>--<name>`，已存在就直接复用，不会重复下载。

### 推理

```bash
./.venv/bin/python test.py
```

````text
开始对话（输入 quit 退出）
你: 帮我写一个把秒数转成时分秒字符串的函数。
模型: ```python
from numbers import Real
...
```
````

### 训练

```bash
./.venv/bin/python sft_train.py
```

训练完成后 adapter 落在 `config.json` 里的 `sft.output_dir`（默认 `./sft-minimal-output`）。
在 RX 7900 XT 上 5 epoch（325 步）大约 3 分钟。

### 评测（复现前后对比）

```bash
./.venv/bin/python eval/compare_style.py
```

会在 `eval/results/` 下生成 `comparison.md`（逐题左右对照）、`summary.md`（指标汇总）
和 `comparison.json`（原始数据）。

## 配置说明

所有可调项都在 [config.json](config.json)，脚本不写死任何超参：

| 段 | 作用 |
| --- | --- |
| `model_id` / `data_path` | 基座模型与训练数据 |
| `generate` | 原样展开给 `model.generate()`；`pad_token_id: null` 表示用 tokenizer 自己的值 |
| `peft` | 原样展开给 `LoraConfig` |
| `sft` | 原样展开给 `SFTConfig` |

```json
"generate": {
  "max_new_tokens": 1024,
  "do_sample": true,
  "temperature": 0.7,
  "top_p": 0.8,
  "pad_token_id": null
}
```

## 已知局限

- 训练集只有 129 条，全是**小工具函数**。类、网络请求、算法题属于分布外，会退化甚至编造 API
  （比如让它写 sklearn 随机森林，它会引用并不存在的 `BaseForest` / `_get_n_features`）。
- 没有 dev 划分，过拟合程度无法量化；实践上 3~5 epoch 是安全区间，10 epoch 基本开始背诵。
- 只提升了格式一致性，**不提升代码正确性**。

## 路线图

- [ ] 补 dev 集与 `eval_strategy`，把 epoch 数从"经验值"变成"看曲线"
- [ ] 扩充题型：类 / 上下文管理器 / 异步 / 网络
- [ ] 加一个极简 CLI（`--prompt` 单次生成，方便脚本调用）

## 开源与许可

- 代码仓库：[github.com/re-ITRT/qwen3-4b-code-style-lora](https://github.com/re-ITRT/qwen3-4b-code-style-lora)
- LoRA adapter：[huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora](https://huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora)（国内可用 [hf-mirror](https://hf-mirror.com/postel-MaoZhiqin/qwen3-4b-code-style-lora) 加速）
- 协议：[Apache-2.0](LICENSE)，基座 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) 同为 Apache-2.0，见 [NOTICE](NOTICE)
- 数据集 `train/train.json`：CC BY 4.0
- 发布流程与检查清单：[docs/OPENSOURCE.md](docs/OPENSOURCE.md) · 模型卡：[docs/MODEL_CARD.md](docs/MODEL_CARD.md)

## 作者

毛治钦（Leo Postel）· GitHub [@re-ITRT](https://github.com/re-ITRT) · Hugging Face [@postel-MaoZhiqin](https://huggingface.co/postel-MaoZhiqin)

## 致谢

基于 [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)（Alibaba Cloud, Apache-2.0）训练。
