import anthropic
import base64
import os
import subprocess
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── 数据路径 ──────────────────────────────────────────────────

real_csv = "/Users/jingqin/AI/减肥.csv"
sample_csv = os.path.join(os.path.dirname(__file__), "sample_health.csv")
CSV_PATH = real_csv if os.path.exists(real_csv) else sample_csv

# ── 读取数据 ──────────────────────────────────────────────────

def load_data():
    df = pd.read_csv(CSV_PATH, sep=";", skiprows=1, encoding="utf-8")
    df = df.dropna(axis=1, how="all").dropna(how="all")
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
    return df

# ── 画图 ──────────────────────────────────────────────────────

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]

COL_EN = {
    "体重": "Weight",
    "腰围（最细）": "Waist",
    "腰围(最细)": "Waist",
    "肚脐": "Navel",
    "胸围": "Chest",
    "臀围": "Hip",
    "大腿": "Thigh",
    "小腿": "Calf",
    "大臂": "Upper Arm",
}

def create_chart(df, columns: list) -> str:
    plt.figure(figsize=(10, 5))
    for i, column in enumerate(columns):
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        dates = df.iloc[series.index, 0]
        label = COL_EN.get(column, column)
        plt.plot(dates, series, marker="o", linewidth=2,
                 color=COLORS[i % len(COLORS)], label=label)

    title = " vs ".join(COL_EN.get(c, c) for c in columns)
    plt.title(f"{title} Trend", fontsize=16)
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("chart.png", dpi=72)
    plt.close()
    return "chart.png"

# ── 发图给 Claude ─────────────────────────────────────────────

def ask_claude(image_paths: list, question: str) -> str:
    content = []

    for path in image_paths:
        with open(path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": image_data}
        })

    content.append({
        "type": "text",
        "text": f"{question}\n\n注意：只根据图中实际可见的数据回答，不要引入图里没有的概念或数据。"
    })

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}]
    )
    return response.content[0].text

# ── 主程序 ───────────────────────────────────────────────────

def main():
    df = load_data()
    numeric_cols = [c for c in df.columns[1:] if pd.to_numeric(df[c], errors="coerce").notna().any()]

    while True:
        # 显示可用列
        print("\n可以画哪些图：")
        for i, col in enumerate(numeric_cols, 1):
            print(f"  {i}. {col}")
        print("  q. 退出")

        choice = input("\n选哪个（输入数字或列名）：").strip()
        if choice.lower() == "q":
            break

        # 解析选择
        if choice.isdigit() and 1 <= int(choice) <= len(numeric_cols):
            column = numeric_cols[int(choice) - 1]
        elif choice in numeric_cols:
            column = choice
        else:
            print("输入不对，请重试")
            continue

        # 画图并打开
        active_cols = [column]
        chart_path = create_chart(df, active_cols)
        subprocess.run(["open", chart_path])
        print(f"\n已生成 {column} 趋势图\n")

        # Claude 自动分析
        print("Claude 分析：")
        analysis = ask_claude([chart_path], f"请用2-3句话分析这张{column}趋势图，指出最明显的规律或变化。")
        print(f"{analysis}\n")

        # 继续追问
        while True:
            follow_up = input("还有问题吗？（直接问，或按 Enter 换图，q 退出）：").strip()
            if follow_up == "":
                break
            if follow_up.lower() == "q":
                return

            # 检测问题里是否提到了其他列（支持模糊匹配）
            def col_mentioned(c, text):
                if c in text:
                    return True
                base = c.split("（")[0].split("(")[0]
                return len(base) >= 2 and base in text

            print(f"  [调试] 问题：{repr(follow_up)}")
            for c in numeric_cols:
                if c not in active_cols:
                    base = c.split("（")[0].split("(")[0]
                    print(f"  [调试] 检查列 {repr(c)} → base={repr(base)} → 匹配={base in follow_up}")
            mentioned_col = next((c for c in numeric_cols if col_mentioned(c, follow_up) and c not in active_cols), None)
            print(f"  [调试] 识别到列：{mentioned_col}")
            if mentioned_col:
                active_cols.append(mentioned_col)
                chart_path = create_chart(df, active_cols)
                subprocess.run(["open", chart_path])
                print(f"\n已将 {mentioned_col} 加入图表\n")

            answer = ask_claude([chart_path], follow_up)
            print(f"\n{answer}\n")

if __name__ == "__main__":
    main()
