import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 基础调用：带 system prompt 的单轮对话
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    system="你是一个专门帮助数据科学家的 AI 助手，回答简洁、实用，用中文回答。",
    messages=[
        {"role": "user", "content": "你好！你擅长帮助数据科学家做什么？"}
    ]
)

print(response.content[0].text)
print(f"\n── Token 用量 ──")
print(f"输入：{response.usage.input_tokens} tokens")
print(f"输出：{response.usage.output_tokens} tokens")
