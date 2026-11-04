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
- `style_answers.json` 是改写后的目标风格答案，不是基座模型的原始输出。

## 流水线

```text
data/questions.json
      │  scripts/generate_raw.py（基座模型批量作答）
      ▼
outputs/generated/raw_answers.json
      │  人工 / 规范化改写
      ▼
data/style_answers.json
      │  sft_train.py（按索引合并成 messages）
      ▼
outputs/adapter（LoRA 权重，发布到 Hugging Face，不进 git）
```

## 许可

数据集以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 发布。
