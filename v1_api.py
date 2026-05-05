import os
from datetime import date, timedelta
from typing import Any, Dict, List, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import doc_tools as rag_demo
import health_tools as step3_tool_use
from demo_structured_output import HealthAnalysis, DocumentSummary

app = FastAPI(
    title="AI 学习助手 API",
    description="统一入口：身体数据分析 + 文档检索问答",
    version="0.1"
)


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    source: str = Field(description="数据来源：health 或 document")
    result: Union[HealthAnalysis, DocumentSummary] = Field(description="结构化结果")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return """
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <title>AI 学习助手</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 32px; background: #f7f8fb; color: #202124; }
    .container { max-width: 720px; margin: 0 auto; padding: 24px; background: #ffffff; border-radius: 16px; box-shadow: 0 12px 32px rgba(0,0,0,0.08); }
    h1 { margin-bottom: 8px; }
    p { color: #555; }
    input[type=text] { width: 100%; padding: 12px 16px; border: 1px solid #dfe1e5; border-radius: 12px; font-size: 16px; margin: 12px 0; }
    button { padding: 12px 20px; border: none; border-radius: 12px; background: #2563eb; color: #fff; font-size: 16px; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .result-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    .result-table td { border: 1px solid #e5e7eb; padding: 12px; vertical-align: top; }
    .label-cell { width: 28%; font-weight: 600; background: #f7fafc; }
    .value-cell { color: #333; }
    pre { background: #f3f4f6; padding: 16px; border-radius: 12px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
    .footer { margin-top: 24px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>AI 学习助手</h1>
    <p>输入你的问题，点击“提交”。当前支持身体数据与文档问答。</p>
    <input id=\"question\" type=\"text\" placeholder=\"例如：我身高166厘米，BMI多少？\" />
    <button onclick=\"askQuestion()\">提交</button>
    <h2>结果</h2>
    <div id=\"resultContainer\">
      <p id=\"resultMessage\">请提交问题，结果将在这里显示。</p>
    </div>
    <div class=\"footer\">API: <code>/ask</code>，状态: <code>/status</code></div>
  </div>
  <script>
    function createTable(rows) {
      const table = document.createElement('table');
      table.className = 'result-table';
      rows.forEach(({ label, value }) => {
        const tr = document.createElement('tr');
        const tdLabel = document.createElement('td');
        tdLabel.textContent = label;
        tdLabel.className = 'label-cell';
        const tdValue = document.createElement('td');
        tdValue.textContent = value;
        tdValue.className = 'value-cell';
        tr.appendChild(tdLabel);
        tr.appendChild(tdValue);
        table.appendChild(tr);
      });
      return table;
    }

    function renderHealthResult(result) {
      const container = document.createElement('div');
      const status = document.createElement('p');
      status.innerHTML = `<strong>整体状态：</strong>${result.overall_status}`;
      container.appendChild(status);

      const summary = document.createElement('p');
      summary.innerHTML = `<strong>总结：</strong>${result.summary}`;
      container.appendChild(summary);

      if (result.metrics && result.metrics.length > 0) {
        const tableRows = result.metrics.map(metric => ({
          label: metric.metric_name,
          value: `当前值：${metric.current_value}${metric.unit ? ' ' + metric.unit : ''}；状态：${metric.status}；趋势：${metric.trend}；建议：${metric.recommendation}`
        }));
        container.appendChild(createTable(tableRows));
      }

      const nextCheck = document.createElement('p');
      nextCheck.innerHTML = `<strong>下次检查：</strong>${result.next_check_date}`;
      container.appendChild(nextCheck);
      return container;
    }

    function renderDocumentResult(result) {
      const container = document.createElement('div');
      const title = document.createElement('p');
      title.innerHTML = `<strong>标题：</strong>${result.title}`;
      container.appendChild(title);

      if (result.key_points && result.key_points.length > 0) {
        const listTitle = document.createElement('p');
        listTitle.innerHTML = '<strong>关键要点：</strong>';
        container.appendChild(listTitle);
        const ul = document.createElement('ul');
        result.key_points.forEach(point => {
          const li = document.createElement('li');
          li.textContent = point;
          ul.appendChild(li);
        });
        container.appendChild(ul);
      }

      const tableRows = [
        { label: '类别', value: result.category },
        { label: '字数', value: result.word_count },
        { label: '主题', value: result.main_topics.join('，') }
      ];
      container.appendChild(createTable(tableRows));
      return container;
    }

    async function askQuestion() {
      const query = document.getElementById('question').value.trim();
      const resultContainer = document.getElementById('resultContainer');
      resultContainer.innerHTML = '<p>正在请求，请稍候...</p>';
      if (!query) {
        resultContainer.innerHTML = '<p>请先输入问题。</p>';
        return;
      }
      try {
        const response = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        const data = await response.json();
        resultContainer.innerHTML = '';
        if (data.source === 'health') {
          resultContainer.appendChild(renderHealthResult(data.result));
        } else if (data.source === 'document') {
          resultContainer.appendChild(renderDocumentResult(data.result));
        } else {
          const pre = document.createElement('pre');
          pre.textContent = JSON.stringify(data, null, 2);
          resultContainer.appendChild(pre);
        }
      } catch (error) {
        resultContainer.innerHTML = '<p>请求失败：' + error.message + '</p>';
      }
    }
  </script>
</body>
</html>
"""


@app.get("/status")
def status() -> Dict[str, Any]:
    return {
        "status": "ok",
        "health_module": "step3_tool_use",
        "document_module": "rag_demo",
        "doc_source": "/Users/jingqin/AI/Interview prepare.txt",
        "health_source": "/Users/jingqin/AI/减肥.csv",
    }


@app.get("/health_columns")
def health_columns() -> Dict[str, Any]:
    data = step3_tool_use.read_csv()
    return {
        "columns": data["columns"],
        "rows": data["rows"],
        "date_range": data["date_range"],
    }


@app.get("/doc_info")
def doc_info() -> Dict[str, Any]:
    doc_path = "/Users/jingqin/AI/Interview prepare.txt"
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Interview prepare.txt not found")
    with open(doc_path, "r", encoding="utf-8") as f:
        text = f.read()
    return {
        "path": doc_path,
        "length": len(text),
        "chunks": len(rag_demo.chunk_document(text)),
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query cannot be empty")

    # 优先尝试解析为身体数据问题
    parsed = step3_tool_use.parse_health_query(query)
    if parsed is not None:
        tool_name, inputs = parsed
        result = step3_tool_use.run_tool(tool_name, inputs)

        # 转换为结构化健康分析
        health_analysis = _convert_to_health_analysis(result, tool_name)
        return AskResponse(source="health", result=health_analysis)

    # 如果身体解析无法识别，使用文档检索
    chunks = rag_demo.chunk_document(rag_demo.load_document("/Users/jingqin/AI/Interview prepare.txt"))
    answer = rag_demo.generate(query, chunks)

    # 转换为结构化文档摘要
    doc_summary = _convert_to_document_summary(answer, query)
    return AskResponse(source="document", result=doc_summary)


def _convert_to_health_analysis(result: Dict[str, Any], tool_name: str) -> HealthAnalysis:
    """将健康工具结果转换为结构化分析"""
    from demo_structured_output import HealthMetrics

    metrics = []

    # 根据工具类型构建指标
    if tool_name == "get_weight":
        metrics.append(HealthMetrics(
            metric_name="体重",
            current_value=result.get("weight", 0),
            unit="kg",
            status="正常" if 50 <= result.get("weight", 0) <= 80 else "异常",
            trend="稳定",
            recommendation="保持健康饮食"
        ))

    elif tool_name == "get_bmi":
        bmi_value = result.get("BMI", result.get("bmi", 0))
        metrics.append(HealthMetrics(
            metric_name="BMI",
            current_value=bmi_value,
            unit="",
            status="正常" if 18.5 <= bmi_value <= 24.9 else "异常",
            trend="稳定",
            recommendation="继续保持健康生活方式"
        ))

    elif tool_name == "get_waist_hip_ratio":
        whr_value = result.get("最新值", result.get("ratio", 0))
        metrics.append(HealthMetrics(
            metric_name="腰臀比",
            current_value=whr_value,
            unit="",
            status="正常" if whr_value <= 0.9 else "偏高",
            trend="下降",
            recommendation="加强腹部训练"
        ))

    elif tool_name == "get_statistics":
        metric_name = result.get("column", "指标")
        current_value = result.get("最新值", 0)
        metrics.append(HealthMetrics(
            metric_name=metric_name,
            current_value=current_value,
            unit="",
            status="正常",
            trend="稳定",
            recommendation="保持当前记录并继续观察"
        ))

    elif tool_name == "get_trend":
        metric_name = result.get("column", "指标")
        values = result.get("values", [])
        latest_value = values[-1] if isinstance(values, list) and values else 0
        metrics.append(HealthMetrics(
            metric_name=metric_name,
            current_value=latest_value,
            unit="",
            status="正常",
            trend=result.get("trend", "未知"),
            recommendation="根据趋势调整训练或饮食"
        ))

    # 计算整体状态
    overall_status = "健康"
    if any(m.status == "异常" for m in metrics):
        overall_status = "需要关注"

    return HealthAnalysis(
        overall_status=overall_status,
        metrics=metrics,
        summary=f"分析了 {len(metrics)} 项健康指标",
        next_check_date=(date.today() + timedelta(weeks=1)).isoformat()
    )


def _convert_to_document_summary(answer: str, query: str) -> DocumentSummary:
    """将文档回答转换为结构化摘要"""
    # 简单的关键词提取作为要点
    key_points = [point.strip() for point in answer.split("。") if point.strip()][:3]

    return DocumentSummary(
        title=f"关于 '{query}' 的回答",
        key_points=key_points if key_points else ["无法提取关键要点"],
        category="面试准备",
        word_count=len(answer),
        main_topics=["面试技巧", "职业发展"]
    )
