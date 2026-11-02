from peft import PeftModel

from config import generation_kwargs, load_config
from load_model import get_model

config = load_config()

# 基座模型 + LoRA 适配器
tokenizer, base_model = get_model(config["model_id"])
model = PeftModel.from_pretrained(base_model, config["sft"]["output_dir"])
model.eval()

# 生成参数全部来自 config.json 的 generate 段
gen_kwargs = generation_kwargs(config, tokenizer)


def chat(messages) -> str:
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    output_ids = model.generate(**inputs, **gen_kwargs)
    new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_ids, skip_special_tokens=True)


if __name__ == "__main__":
    messages = []
    print("开始对话（输入 quit 退出）")
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        reply = chat(messages)
        print(f"模型: {reply}\n")
        messages.append({"role": "assistant", "content": reply})
