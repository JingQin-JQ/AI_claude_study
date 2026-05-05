import json
import os
from typing import Dict, Any, List

import anthropic
from pydantic import BaseModel, Field

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ── Pydantic 模型定义 ──────────────────────────────────────────

class HealthMetrics(BaseModel):
    """身体指标数据结构"""
    metric_name: str = Field(description="指标名称")
    current_value: float = Field(description="当前值")
    unit: str = Field(description="单位")
    status: str = Field(description="状态：正常/偏高/偏低")
    trend: str = Field(description="趋势：上升/下降/稳定")
    recommendation: str = Field(description="建议")


class HealthAnalysis(BaseModel):
    """健康分析结果"""
    overall_status: str = Field(description="整体健康状态")
    metrics: List[HealthMetrics] = Field(description="各项指标")
    summary: str = Field(description="总结")
    next_check_date: str = Field(description="下次检查日期")


class DocumentSummary(BaseModel):
    """文档摘要结构"""
    title: str = Field(description="文档标题")
    key_points: List[str] = Field(description="关键要点")
    category: str = Field(description="文档类别")
    word_count: int = Field(description="字数统计")
    main_topics: List[str] = Field(description="主要话题")


# ── 结构化输出函数 ────────────────────────────────────────────

def analyze_health_data() -> HealthAnalysis:
    """分析健康数据，返回结构化结果"""
    # 这里可以调用你的 step3_tool_use 函数
    # 为了演示，我们用模拟数据

    metrics = [
        HealthMetrics(
            metric_name="体重",
            current_value=58.35,
            unit="kg",
            status="正常",
            trend="稳定",
            recommendation="保持当前饮食习惯"
        ),
        HealthMetrics(
            metric_name="BMI",
            current_value=21.18,
            unit="",
            status="正常",
            trend="稳定",
            recommendation="继续保持健康生活方式"
        ),
        HealthMetrics(
            metric_name="腰臀比",
            current_value=0.75,
            unit="",
            status="正常",
            trend="下降",
            recommendation="继续减脂训练"
        )
    ]

    return HealthAnalysis(
        overall_status="健康",
        metrics=metrics,
        summary="各项指标均在正常范围内，减肥效果良好",
        next_check_date="2026-05-01"
    )


def summarize_document(doc_path: str) -> DocumentSummary:
    """总结文档，返回结构化结果"""
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用 Claude 生成结构化摘要
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="""你是一个文档分析助手。请分析给定的文档内容，返回结构化的JSON摘要。

要求：
- 提取文档标题
- 列出3-5个关键要点
- 判断文档类别（面试准备/学习笔记/其他）
- 统计字数
- 识别主要话题

返回格式必须是有效的JSON，符合以下结构：
{
  "title": "文档标题",
  "key_points": ["要点1", "要点2", ...],
  "category": "类别",
  "word_count": 数字,
  "main_topics": ["话题1", "话题2", ...]
}""",
        messages=[{
            "role": "user",
            "content": f"请分析以下文档内容：\n\n{content[:2000]}"  # 限制长度
        }]
    )

    # 解析 Claude 的 JSON 响应（去掉可能的 markdown 代码块）
    try:
        import re
        text = response.content[0].text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        result = json.loads(text.strip())
        return DocumentSummary(**result)
    except (json.JSONDecodeError, Exception):
        # 如果解析失败，返回默认结构
        return DocumentSummary(
            title="文档分析",
            key_points=["无法解析文档内容"],
            category="未知",
            word_count=len(content.split()),
            main_topics=["文档处理"]
        )


# ── 使用 Anthropic 结构化输出 ─────────────────────────────────

def analyze_with_structured_output(query: str) -> Dict[str, Any]:
    """使用 Anthropic 的结构化输出功能"""

    # 定义工具（实际上是输出模式）
    tools = [
        {
            "name": "health_analysis",
            "description": "分析健康数据并返回结构化结果",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query_type": {"type": "string", "enum": ["health", "document"]},
                    "data": {"type": "object"}
                },
                "required": ["query_type"]
            }
        }
    ]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        tools=tools,
        tool_choice={"type": "any"},
        system="""你是一个结构化输出助手。请根据用户查询返回结构化的JSON数据。

如果用户询问健康相关问题，返回：
{
  "type": "health_analysis",
  "data": {
    "status": "健康状态",
    "metrics": [
      {
        "name": "指标名",
        "value": 数值,
        "unit": "单位",
        "assessment": "评估"
      }
    ],
    "recommendations": ["建议1", "建议2"]
  }
}

如果用户询问文档相关问题，返回：
{
  "type": "document_summary",
  "data": {
    "title": "标题",
    "summary": "摘要",
    "key_points": ["要点1", "要点2"],
    "topics": ["话题1", "话题2"]
  }
}""",
        messages=[{"role": "user", "content": query}]
    )

    # 处理工具调用响应
    if response.stop_reason == "tool_use":
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "tool_called": block.name,
                    "input": block.input,
                    "structured_output": True
                }

    # 如果没有工具调用，返回文本响应
    return {
        "type": "text_response",
        "content": response.content[0].text if response.content else "",
        "structured_output": False
    }


# ── 主程序 ───────────────────────────────────────────────────

def main():
    print("结构化输出演示")
    print("=" * 50)

    # 1. Pydantic 结构化输出
    print("\n1. Pydantic 结构化输出示例：")
    health_data = analyze_health_data()
    print(json.dumps(health_data.model_dump(), ensure_ascii=False, indent=2))

    # 2. 文档结构化摘要
    print("\n2. 文档结构化摘要示例：")
    doc_path = "/Users/jingqin/AI/Interview prepare.txt"
    if os.path.exists(doc_path):
        doc_summary = summarize_document(doc_path)
        print(json.dumps(doc_summary.model_dump(), ensure_ascii=False, indent=2))
    else:
        print("文档文件不存在")

    # 3. Anthropic 结构化输出
    print("\n3. Anthropic 结构化输出示例：")
    query = "分析我的健康数据"
    result = analyze_with_structured_output(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()