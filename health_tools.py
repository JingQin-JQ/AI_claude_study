import anthropic
import pandas as pd
import json
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
_real_csv = "/Users/jingqin/AI/减肥.csv"
_sample_csv = os.path.join(os.path.dirname(__file__), "sample_health.csv")
CSV_PATH = _real_csv if os.path.exists(_real_csv) else _sample_csv

# ── 工具函数 ─────────────────────────────────────────────────

def _load():
    df = pd.read_csv(CSV_PATH, sep=";", skiprows=1, encoding="utf-8", index_col=False)
    return df.dropna(axis=1, how="all").dropna(how="all").reset_index(drop=True)

def read_csv():
    df = _load()
    return {
        "columns": list(df.columns),
        "rows": len(df),
        "date_range": f"{df.iloc[0,0]} 到 {df.iloc[-1,0]}"
    }

def get_statistics(column: str):
    df = _load()
    if column not in df.columns:
        return {"error": f"列 '{column}' 不存在，可用列：{list(df.columns)}"}
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    return {
        "column": column,
        "最新值": float(series.iloc[-1]),
        "最小值": float(series.min()),
        "最大值": float(series.max()),
        "平均值": round(float(series.mean()), 2),
        "总变化": round(float(series.iloc[-1] - series.iloc[0]), 2)
    }

def get_trend(column: str):
    df = _load()
    if column not in df.columns:
        return {"error": f"列 '{column}' 不存在"}
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    dates = df.iloc[series.index, 0].tolist()
    values = series.tolist()
    return {"dates": dates[-5:], "values": values[-5:], "trend": "下降" if values[-1] < values[0] else "上升"}


def get_bmi(height_cm=None):
    df = pd.read_csv(CSV_PATH, sep=";", skiprows=1, encoding="utf-8")
    df = df.dropna(axis=1, how="all").dropna(how="all")
    if "体重" not in df.columns:
        return {"error": "CSV 文件中缺少体重列，无法计算 BMI。"}

    height_col = None
    for candidate in ["身高", "身高(cm)", "身高（cm）"]:
        if candidate in df.columns:
            height_col = candidate
            break

    weight = pd.to_numeric(df["体重"], errors="coerce").dropna()
    if weight.empty:
        return {"error": "体重数据为空，无法计算 BMI。"}

    latest_weight = float(weight.iloc[-1])

    # 如果提供了身高参数，使用它；否则从 CSV 中查找
    if height_cm is not None:
        latest_height = float(height_cm)
    elif height_col is not None:
        height = pd.to_numeric(df[height_col], errors="coerce").dropna()
        if height.empty:
            return {"error": "身高数据为空，无法计算 BMI。"}
        latest_height = float(height.iloc[-1])
    else:
        return {"error": "当前数据中没有身高信息，无法计算 BMI。请在 CSV 中加入身高列，或直接告诉我你的身高。"}

    if latest_height > 10:
        latest_height = latest_height / 100
    if latest_height <= 0:
        return {"error": "身高值不合法，无法计算 BMI。"}

    bmi = latest_weight / (latest_height ** 2)
    return {
        "column": "BMI",
        "体重": latest_weight,
        "身高(cm)": latest_height * 100 if height_cm is not None else (float(height.iloc[-1]) if height_col else None),
        "BMI": round(bmi, 2)
    }


def get_waist_hip_ratio():
    df = pd.read_csv(CSV_PATH, sep=";", skiprows=1, encoding="utf-8")
    df = df.dropna(axis=1, how="all").dropna(how="all")
    if "腰围（最细）" not in df.columns or "臀围" not in df.columns:
        return {"error": "缺少腰围或臀围数据，无法计算腰臀比。"}
    waist = pd.to_numeric(df["腰围（最细）"], errors="coerce").dropna()
    hip = pd.to_numeric(df["臀围"], errors="coerce").dropna()
    if waist.empty or hip.empty:
        return {"error": "腰围或臀围数据为空，无法计算腰臀比。"}
    ratio = float(waist.iloc[-1] / hip.iloc[-1])
    return {
        "column": "腰臀比",
        "最新值": round(ratio, 3),
        "腰围": float(waist.iloc[-1]),
        "臀围": float(hip.iloc[-1])
    }


def parse_health_query(query: str):
    text = query.lower()
    if "腰臀比" in text or "腰臀" in text:
        return "get_waist_hip_ratio", {}

    # 提取身高信息
    import re
    height_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|厘米|公分)', text)
    height_cm = float(height_match.group(1)) if height_match else None

    if "bmi" in text or "身体质量指数" in text or "体重指数" in text:
        return "get_bmi", {"height_cm": height_cm}

    column_keywords = {
        "体重": "体重",
        "多重": "体重",
        "腰围": "腰围（最细）",
        "肚脐": "肚脐",
        "胸围": "胸围",
        "臀围": "臀围",
        "大腿": "大腿",
        "小腿": "小腿",
        "大臂": "大臂",
    }
    trend_keywords = ["趋势", "最近", "变化", "下降", "上升", "过去", "近"]

    for keyword, column in column_keywords.items():
        if keyword in text:
            if any(x in text for x in trend_keywords):
                return "get_trend", {"column": column}
            return "get_statistics", {"column": column}

    if any(x in text for x in ["列", "有哪些", "字段", "列名", "字段名"]):
        return "read_csv", {}
    return None

# ── 工具定义（告诉 Claude 有哪些工具）────────────────────────

tools = [
    {
        "name": "read_csv",
        "description": "读取CSV文件，返回列名、行数和时间范围",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_statistics",
        "description": "获取某个身体指标的统计数据，包括最新值、最小值、最大值、平均值和总变化",
        "input_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "列名，如：体重、腰围（最细）、肚脐等"}
            },
            "required": ["column"]
        }
    },
    {
        "name": "get_trend",
        "description": "获取某个指标最近5条记录的趋势",
        "input_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "列名"}
            },
            "required": ["column"]
        }
    },
    {
        "name": "get_bmi",
        "description": "计算BMI（身体质量指数），从CSV读取最新体重，身高可从CSV读取或由用户提供",
        "input_schema": {
            "type": "object",
            "properties": {
                "height_cm": {"type": "number", "description": "用户身高（厘米），不提供则从CSV读取"}
            },
            "required": []
        }
    },
    {
        "name": "get_waist_hip_ratio",
        "description": "计算腰臀比，从CSV读取最新腰围和臀围数据",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]

# ── 执行工具调用 ─────────────────────────────────────────────

def run_tool(name, inputs):
    if name == "read_csv":
        return read_csv()
    elif name == "get_statistics":
        return get_statistics(inputs["column"])
    elif name == "get_trend":
        return get_trend(inputs["column"])
    elif name == "get_bmi":
        return get_bmi(inputs.get("height_cm"))
    elif name == "get_waist_hip_ratio":
        return get_waist_hip_ratio()

# ── 主循环（支持工具调用）────────────────────────────────────

def chat(user_message):
    direct = parse_health_query(user_message)
    if direct is not None:
        tool_name, inputs = direct
        result = run_tool(tool_name, inputs)
        print(f"\n[直接使用工具回答] {tool_name} {inputs}\n{json.dumps(result, ensure_ascii=False, indent=2)}\n")
        return

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=tools,
            system="你是一个身体数据分析助手，帮用户分析她的减肥记录数据。用中文回答。",
            messages=messages
        )

        # Claude 想调用工具
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [调用工具: {block.name} {block.input}]")
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        # Claude 完成回答
        else:
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\n回答：{block.text}\n")
            break

def main():
    print("身体数据分析助手已就绪，输入 q 退出\n")
    while True:
        query = input("你的问题：").strip()
        if query.lower() == "q":
            break
        chat(query)

if __name__ == "__main__":
    main()
