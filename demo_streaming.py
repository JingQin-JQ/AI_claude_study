import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with client.messages.stream(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    messages=[{"role": "user", "content": "用中文介绍一下RAG技术，100字以内"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    message = stream.get_final_message()

print()
print(f"\n── Token 用量 ──")
print(f"输入：{message.usage.input_tokens} tokens")
print(f"输出：{message.usage.output_tokens} tokens")
print(f"预估费用：${(message.usage.input_tokens * 0.00000025 + message.usage.output_tokens * 0.00000125):.6f}")
