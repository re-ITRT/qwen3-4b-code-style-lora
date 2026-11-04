# 数据

## 文件

| 文件 | 内容 |
| --- | --- |
| `questions.json` | 516 条中文需求，作为 SFT 的 user 侧 |
| `style_answers.json` | 516 条目标风格答案，作为 SFT 的 assistant 侧，与 `questions.json` 按索引一一对应 |
| `samples/` | 同一道 KNN 题在 Python / C++ / Kotlin / C# 下的风格参考 |

## 格式

两个文件都是 JSON 字符串数组，长度必须相同（训练时校验）。`sft_train.py` 会把
`questions[i]` 与 `style_answers[i]` 拼成一条 `messages` 记录：

```json
{
  "messages": [
    {"role": "user", "content": "<questions[i]>"},
    {"role": "assistant", "content": "<style_answers[i]>"}
  ]
}
```

## 语料构成

- 覆盖 Python、C++、Kotlin、C# 四种语言；
- 题型以小工具函数为主（字符串处理、数值计算、可迭代对象、文件 IO），另有少量
  scikit-learn 风格 estimator 与类；
- `style_answers.json` 是在基座原始回答基础上只重写代码块得到的答案，解释文字沿用基座输出。

## 流水线

```text
data/questions.json
      │  scripts/generate_raw.py（基座模型批量作答）
      ▼
outputs/generated/raw_answers.json
      │  风格化改写：代码块按目标风格重写，其余文字保留
      ▼
data/style_answers.json
      │  sft_train.py（按索引合并成 messages）
      ▼
outputs/adapter（LoRA 权重，发布到 Hugging Face，不进 git）
```

## 标注方法

这次微调的目标是**只改变代码风格**，不改答案内容，所以数据集的构造分两步：

1. 让基座模型直接回答 `questions.json`，得到 `raw_answers`——题面、解释文字、代码块都由基座生成；
2. 在基座回答的基础上做风格化改写：**只重写代码块**，让它符合目标风格（一句说明 + 单个代码块、
   抽象入参类型 + 具体返回类型、边界条件显式处理），代码块以外的文字尽量保持模型原样。

这样训练信号集中在「同一段回答里代码该怎么写」上，而不是让模型重新学怎么解释问题。

## 许可

数据集以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 发布。
