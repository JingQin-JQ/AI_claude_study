import base64
import io
import json
import os

import anthropic
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pandas as pd
import streamlit as st

from v2_agent import build_system_prompt, load_memory, run_tool, tools

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="私人助手", page_icon="🤖")
st.title("私人助手")

# ── Session state ─────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()
if "chart_fig_bytes" not in st.session_state:
    st.session_state.chart_fig_bytes = None
if "chart_analysis" not in st.session_state:
    st.session_state.chart_analysis = ""
if "chart_qa" not in st.session_state:
    st.session_state.chart_qa = []
if "chart_data_summary" not in st.session_state:
    st.session_state.chart_data_summary = ""

# ── Chart helpers ─────────────────────────────────────────────

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]
COL_EN = {
    "体重": "Weight", "腰围（最细）": "Waist", "腰围(最细)": "Waist",
    "肚脐": "Navel", "胸围": "Chest", "臀围": "Hip",
    "大腿": "Thigh", "小腿": "Calf", "大臂": "Upper Arm",
}

def load_df(uploaded_file=None):
    if uploaded_file:
        return pd.read_csv(uploaded_file, sep=";", skiprows=1, encoding="utf-8")
    real_csv = "/Users/jingqin/AI/减肥.csv"
    sample_csv = os.path.join(os.path.dirname(__file__), "sample_health.csv")
    path = real_csv if os.path.exists(real_csv) else sample_csv
    return pd.read_csv(path, sep=";", skiprows=1, encoding="utf-8")

def make_chart_bytes(df, columns):
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, col in enumerate(columns):
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        dates = df.iloc[series.index, 0]
        ax.plot(dates, series, marker="o", linewidth=2,
                color=COLORS[i % len(COLORS)], label=COL_EN.get(col, col))
    title = " vs ".join(COL_EN.get(c, c) for c in columns)
    ax.set_title(f"{title} Trend", fontsize=16)
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=72)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def get_data_summary(df, columns):
    lines = []
    for col in columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        dates = df.iloc[series.index, 0]
        lines.append(
            f"- {col}（{COL_EN.get(col, col)}）："
            f"起始值={series.iloc[0]:.1f}（{dates.iloc[0]}），"
            f"最新值={series.iloc[-1]:.1f}（{dates.iloc[-1]}），"
            f"总变化={series.iloc[-1] - series.iloc[0]:+.1f}，"
            f"最小={series.min():.1f}，最大={series.max():.1f}"
        )
    return "\n".join(lines)

def ask_claude_chart(img_bytes, question, data_summary="", chart_only=False):
    image_data = base64.standard_b64encode(img_bytes).decode("utf-8")
    note = "图中的视觉形状反映趋势，具体数值以下方数据为准。" if not chart_only else "请根据图中趋势作答。"
    text = question
    if data_summary:
        text += f"\n\n实际数据：\n{data_summary}\n\n{note}"
    if not chart_only:
        text += "\n\n你可以结合以上数据和你的健康知识来回答。"
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
        {"type": "text", "text": text}
    ]
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}]
    )
    return response.content[0].text

# ── Tabs ──────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["💬 对话助手", "📊 图表分析"])

# ── Tab 1: Chat ───────────────────────────────────────────────

with tab1:
    for msg in st.session_state.messages:
        if msg["role"] == "user" and isinstance(msg["content"], str):
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            for block in msg["content"]:
                if hasattr(block, "text"):
                    with st.chat_message("assistant"):
                        st.write(block.text)

    if prompt := st.chat_input("输入问题..."):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
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
                        answer = next((b.text for b in response.content if hasattr(b, "text")), "")
                        st.write(answer)
                        st.session_state.messages.append({"role": "assistant", "content": response.content})
                        break
            if tool_calls_log:
                with st.expander(f"调用了 {len(tool_calls_log)} 个工具"):
                    for call in tool_calls_log:
                        st.code(call)
            st.caption(f"token：输入 {response.usage.input_tokens} / 输出 {response.usage.output_tokens}")

# ── Tab 2: Charts ─────────────────────────────────────────────

with tab2:
    real_csv = "/Users/jingqin/AI/减肥.csv"
    if os.path.exists(real_csv):
        uploaded = None
    else:
        uploaded = st.file_uploader("上传健康数据 CSV（分号分隔，第一行为标题行之前的说明）", type="csv")
        if not uploaded:
            st.info("未上传文件，当前显示示例数据。上传你的 CSV 文件以分析真实数据。")

    try:
        df = load_df(uploaded)
        df = df.dropna(axis=1, how="all").dropna(how="all")
        date_col = df.columns[0]
        df[date_col] = df[date_col].astype(str)
        df = df.sort_values(date_col).reset_index(drop=True)
        numeric_cols = [c for c in df.columns[1:] if pd.to_numeric(df[c], errors="coerce").notna().any()]

        selected = st.multiselect("选择要显示的指标（可多选）", numeric_cols)

        if st.button("生成图表并分析", disabled=len(selected) == 0):
            with st.spinner("生成图表中..."):
                img_bytes = make_chart_bytes(df, selected)
                st.session_state.chart_fig_bytes = img_bytes
            summary = get_data_summary(df, selected)
            st.session_state.chart_data_summary = summary
            with st.expander("发给 Claude 的数据"):
                st.text(f"列名：{df.columns.tolist()}")
                st.dataframe(df.head(3))
                st.text(summary)
            with st.spinner("Claude 分析中..."):
                analysis = ask_claude_chart(
                    img_bytes,
                    "请分析这张趋势图，分两部分回答：1）用1-2句话指出最明显的规律或变化；2）给出1-2条具体的身材管理建议。",
                    data_summary=summary,
                    chart_only=True
                )
            st.session_state.chart_analysis = analysis
            st.session_state.chart_qa = []

        if st.session_state.chart_fig_bytes:
            st.image(st.session_state.chart_fig_bytes)
            st.info(st.session_state.chart_analysis)

            for q, a in st.session_state.chart_qa:
                with st.chat_message("user"):
                    st.write(q)
                with st.chat_message("assistant"):
                    st.write(a)

            with st.form("chart_q", clear_on_submit=True):
                question = st.text_input("还有什么问题？")
                if st.form_submit_button("提问") and question:
                    with st.spinner("思考中..."):
                        answer = ask_claude_chart(st.session_state.chart_fig_bytes, question, data_summary=st.session_state.chart_data_summary)
                    st.session_state.chart_qa.append((question, answer))
                    st.rerun()

    except Exception as e:
        if uploaded is None and not os.path.exists(real_csv):
            st.info("请上传 CSV 文件开始分析")
        else:
            st.error(f"读取数据失败：{e}")
