import anthropic
import json
import os
from datetime import date

from health_tools import read_csv, get_statistics, get_trend, get_bmi, get_waist_hip_ratio
import doc_tools as rag_demo

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
DOC_PATH = "/Users/jingqin/AI/Interview prepare.txt"
MEMORY_PATH = "/Users/jingqin/AI/学习计划/memory.json"

# ── 记忆：读写本地文件 ────────────────────────────────────────

def load_memory() -> dict:
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"facts": {}, "sessions": []}

def save_memory(memory: dict) -> None:
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def build_system_prompt(memory: dict) -> str:
    prompt = "你是一个私人助手，可以查询用户的身体健康数据和面试准备文档。用中文回答。当用户提到身高、体重目标、名字等个人固定信息时，立刻调用 save_fact 工具保存，不需要征得用户同意。"

    if memory["facts"]:
        facts_str = "、".join(f"{k}：{v}" for k, v in memory["facts"].items())
        prompt += f"\n\n已知用户信息：{facts_str}"

    if memory["sessions"]:
        last = memory["sessions"][-1]
        prompt += f"\n\n上次对话（{last['date']}）：{last['summary']}"

    return prompt

def summarize_session(messages: list) -> str:
    conversation = "\n".join(
        f"{'用户' if m['role'] == 'user' and isinstance(m['content'], str) else 'Assistant' if m['role'] == 'assistant' else ''}: "
        f"{m['content'] if isinstance(m['content'], str) else '[工具调用]'}"
        for m in messages
        if isinstance(m.get("content"), str)
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"用一句话（30字以内）总结以下对话的主要内容：\n{conversation}"
        }]
    )
    return response.content[0].text.strip()

# ── 工具列表：Claude 能用的所有工具 ──────────────────────────

tools = [
    {
        "name": "get_bmi",
        "description": "计算BMI，从CSV读取最新体重，身高可由用户提供",
        "input_schema": {
            "type": "object",
            "properties": {
                "height_cm": {"type": "number", "description": "用户身高（厘米），不提供则从CSV读取"}
            },
            "required": []
        }
    },
    {
        "name": "get_statistics",
        "description": "获取某个身体指标的统计数据：最新值、最小值、最大值、平均值、总变化",
        "input_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "列名，如：体重、腰围（最细）、臀围、大腿等"}
            },
            "required": ["column"]
        }
    },
    {
        "name": "get_trend",
        "description": "获取某个身体指标最近5条记录的变化趋势",
        "input_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "列名"}
            },
            "required": ["column"]
        }
    },
    {
        "name": "get_waist_hip_ratio",
        "description": "计算腰臀比",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_csv",
        "description": "查看健康数据CSV有哪些列，以及数据的时间范围",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_document",
        "description": "搜索面试准备文档，回答关于工作经历、项目经验、技能等问题",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索的问题或关键词"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_fact",
        "description": "保存用户告知的固定信息，如身高、减肥目标、名字等",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "信息名称，如：身高、目标体重"},
                "value": {"type": "string", "description": "信息内容，如：166cm、55kg"}
            },
            "required": ["key", "value"]
        }
    }
]

# ── 执行工具 ─────────────────────────────────────────────────

def run_tool(name: str, inputs: dict, memory: dict) -> dict:
    if name == "get_bmi":
        return get_bmi(inputs.get("height_cm"))
    elif name == "get_statistics":
        return get_statistics(inputs["column"])
    elif name == "get_trend":
        return get_trend(inputs["column"])
    elif name == "get_waist_hip_ratio":
        return get_waist_hip_ratio()
    elif name == "read_csv":
        return read_csv()
    elif name == "search_document":
        text = rag_demo.load_document(DOC_PATH)
        chunks = rag_demo.chunk_document(text)
        relevant = rag_demo.retrieve(inputs["query"], chunks)
        return {"content": "\n\n".join(relevant)}
    elif name == "save_fact":
        memory["facts"][inputs["key"]] = inputs["value"]
        save_memory(memory)
        return {"status": "已保存", "key": inputs["key"], "value": inputs["value"]}

# ── Agent 循环 ───────────────────────────────────────────────

messages = []

def chat(user_message: str, memory: dict) -> None:
    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=tools,
            system=build_system_prompt(memory),
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → 调用工具：{block.name} {block.input}")
                    result = run_tool(block.name, block.input, memory)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\n{block.text}\n")
            print(f"[token：输入 {response.usage.input_tokens} / 输出 {response.usage.output_tokens}]")
            messages.append({"role": "assistant", "content": response.content})
            break

# ── 主程序 ───────────────────────────────────────────────────

def main():
    memory = load_memory()
    print("Agent 已就绪，输入 q 退出\n")

    while True:
        query = input("你：").strip()
        if query.lower() in {"q", "quit", "exit"}:
            break
        chat(query, memory)

    # 退出时保存本次会话摘要
    if messages:
        print("\n正在保存本次对话摘要...")
        summary = summarize_session(messages)
        memory["sessions"].append({
            "date": date.today().isoformat(),
            "summary": summary
        })
        memory["sessions"] = memory["sessions"][-5:]  # 只保留最近5次
        save_memory(memory)
        print(f"已保存：{summary}")

if __name__ == "__main__":
    main()
