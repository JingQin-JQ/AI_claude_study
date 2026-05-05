import json
import os

import anthropic
import streamlit as st

from v2_agent import build_system_prompt, load_memory, run_tool, tools

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── 页面配置 ─────────────────────────────────────────────────

st.set_page_config(page_title="私人助手", page_icon="🤖")
st.title("私人助手")

# ── session_state 初始化 ──────────────────────────────────────
# 这里是 Streamlit 的关键：每次用户操作脚本都会重新执行
# 用 session_state 保存需要跨越多次执行的数据

if "messages" not in st.session_state:
    st.session_state.messages = []   # 对话历史

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()  # 从文件读取记忆

# ── 显示历史对话 ──────────────────────────────────────────────
# 每次重新执行时把之前的对话重新渲染出来

for msg in st.session_state.messages:
    if msg["role"] == "user" and isinstance(msg["content"], str):
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        for block in msg["content"]:
            if hasattr(block, "text"):
                with st.chat_message("assistant"):
                    st.write(block.text)

# ── 接收用户输入 ──────────────────────────────────────────────

if prompt := st.chat_input("输入问题..."):

    # 立刻显示用户消息
    with st.chat_message("user"):
        st.write(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    # ── Agent 循环 ────────────────────────────────────────────
    tool_calls_log = []

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):

            while True:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    tools=tools,
                    system=build_system_prompt(st.session_state.memory),
                    messages=st.session_state.messages
                )

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_calls_log.append(f"{block.name}  {block.input}")
                            result = run_tool(block.name, block.input, st.session_state.memory)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False)
                            })
                    st.session_state.messages.append({"role": "assistant", "content": response.content})
                    st.session_state.messages.append({"role": "user", "content": tool_results})

                else:
                    # 最终回答
                    answer = next((b.text for b in response.content if hasattr(b, "text")), "")
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": response.content})
                    break

        # 工具调用详情（可折叠）
        if tool_calls_log:
            with st.expander(f"调用了 {len(tool_calls_log)} 个工具"):
                for call in tool_calls_log:
                    st.code(call)

        # token 用量
        st.caption(f"token：输入 {response.usage.input_tokens} / 输出 {response.usage.output_tokens}")
