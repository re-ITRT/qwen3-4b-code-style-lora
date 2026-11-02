# 开源记录与发布指南

本仓库已按下面的方案发布：

| 平台 | 地址 | 放什么 |
| --- | --- | --- |
| GitHub | [re-ITRT/qwen3-4b-code-style-lora](https://github.com/re-ITRT/qwen3-4b-code-style-lora) | 训练 / 推理 / 评测代码、`train/train.json`、对比报告 |
| Hugging Face | [postel-MaoZhiqin/qwen3-4b-code-style-lora](https://huggingface.co/postel-MaoZhiqin/qwen3-4b-code-style-lora) | LoRA adapter + 模型卡 |
| ModelScope（可选） | 同上镜像 | 国内下载加速，需实名认证后手动同步 |

## 1. 协议

| 组件 | 协议 | 理由 |
| --- | --- | --- |
| 代码（训练/推理/评测） | **Apache-2.0** | 自带专利授权与商标条款，与基座一致 |
| LoRA adapter 权重 | **Apache-2.0** | Qwen3-4B 本身是 Apache-2.0，衍生物用同协议最省事，商用也不受限 |
| 训练数据 `train.json` | **CC BY 4.0** | 自己写的 129 条样本，署名即可复用 |
| 文档 | 随仓库（Apache-2.0） | 无需单独协议 |

不要用的：

- **GPL / AGPL**：会传导给使用者，与 HF 模型生态也不匹配。
- **自定义"仅限研究"协议**：Apache-2.0 的衍生物**不能再附加限制条款**。

## 2. 发布前检查清单（已完成）

- [x] `.env` 没有进过 git 历史（`git log --all -- .env` 为空）
- [x] `models/`（8GB 基座）已忽略，不会误传
- [x] `sft-minimal-output/` 已忽略，adapter 只走 HF
- [x] `train/` 放行 `train.json`：`.gitignore` 用 `train/*` + `!train/train.json`（目录级忽略无法用 `!` 撤销）
- [x] `.env.example` 放行：`.env.*` 会连模板一起吞掉，已加 `!.env.example`
- [x] 仓库名不用 `post-trainning-learning`（拼写有误），发布名 `qwen3-4b-code-style-lora`
- [x] `LICENSE`（Apache-2.0）与 `NOTICE`（标注 Qwen3-4B 来源）已补
- [x] 训练入口 `sft_tain.py` → `sft_train.py`（`git mv` 保留历史）
- [x] model card 写清 `base_model`，见 [MODEL_CARD.md](MODEL_CARD.md)
- [x] 提交前 `git add -n .` 通读一遍，确认没有模型权重或密钥混进去

## 3. 复现发布

```bash
# GitHub
git remote add origin https://github.com/re-ITRT/qwen3-4b-code-style-lora.git
git push -u origin main

# Hugging Face（国内网络需把 endpoint 指向镜像）
pip install -U huggingface_hub
HF_ENDPOINT=https://hf-mirror.com huggingface-cli upload \
  postel-MaoZhiqin/qwen3-4b-code-style-lora sft-minimal-output . --repo-type model
```

## 4. 合规要点

1. **保留版权声明**：Apache-2.0 要求保留 LICENSE 与 NOTICE，模型卡注明 `base_model: Qwen/Qwen3-4B`。
2. **不要重传基座权重**：只传 adapter，既省空间也避免让人误以为基座是自己训的。
3. **数据来源**：129 条需求与答案均为自建；如果后续用别的模型生成答案，注意其服务条款是否允许再分发。
4. **商用**：Apache-2.0 允许商用，不要在协议里额外加限制；建议在 model card 里写清能力与局限。
