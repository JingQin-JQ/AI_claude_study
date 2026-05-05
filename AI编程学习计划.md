# 自雇 Data Scientist 的 AI 编程学习计划

> 目标：用 Claude 作为学习伙伴，掌握 AI 编程核心技能，提升自雇竞争力

---

## 你的起点

- 已有 DS 背景（Python、数据分析、建模）
- 使用 Claude Pro
- 目标：能独立开发 AI 驱动的产品/工具/自动化流程

---

## 阶段一：基础夯实（2–4 周）

### 目标：搞懂 LLM 怎么用，能写出第一个 AI 功能

**1. Prompt Engineering**
- 学会写清晰、结构化的 prompt
- 掌握：system prompt、few-shot、chain of thought
- 实践：用 Claude 帮你优化自己的 prompt

#### 实战项目：数据分析报告生成器

用你的 DS 日常场景练 prompt，目标是打造一个可复用的报告模板。

**四个练习步骤（难度递进）：**

| 步骤 | 技巧 | 任务 |
|------|------|------|
| Step 1 | 基础 prompt | 用一句话描述场景，观察输出质量 |
| Step 2 | System Prompt | 给 Claude 定义角色、格式、语气，对比效果 |
| Step 3 | Few-shot | 提供一个你满意的报告片段作为示例 |
| Step 4 | Chain of Thought | 让 Claude 先列分析思路再写报告 |

**练习数据：** `AI/prompt engineering/电商销售数据摘要.md`

**最终交付物：** 一个你自己的数据分析报告 prompt 模板，以后直接套用

**2. Anthropic API 入门**
- 注册 API key，跑通第一个 API 调用
- 学会：`messages` 接口、流式输出（streaming）、token 计算
- 工具：`anthropic` Python SDK

**3. 用 Claude Code 提效**
- 学会用 Claude Code CLI 辅助写代码
- 让 Claude 帮你 debug、重构、写测试

**学习方式：**
> 把 Claude 当作导师，每天给它一个具体问题："帮我解释 temperature 参数的作用，并给我一个实验代码"

---

## 阶段二：核心技能（1–2 个月）

### 目标：能独立构建可用的 AI 工具

**4. RAG（检索增强生成）**
- 为什么重要：让 AI 能读你自己的数据/文档
- 技术栈：`LangChain` 或 `LlamaIndex` + 向量数据库（Chroma / Pinecone）
- 实践项目：做一个能问答你自己 PDF 文件的工具

**5. Tool Use / Function Calling**
- 让 Claude 调用外部 API、查数据库、执行代码
- 实践：给 Claude 接一个天气 API 或你自己的数据源

**6. AI Agent 基础**
- 理解 Agent 循环：思考 → 工具调用 → 观察 → 继续
- 用 Anthropic 的 Agent SDK 或 LangGraph 搭一个简单 Agent
- 实践项目：自动化数据分析 Agent（给它一个 CSV，它自己分析并出报告）

**7. 结构化输出**
- 让 LLM 返回 JSON / 表格而不是自由文本
- 工具：Pydantic + Claude 的 structured output

---

## 阶段三：产品化能力（1–2 个月）

### 目标：能把 AI 功能做成可交付的产品

**8. 前端快速原型**
- 学 Streamlit 或 Gradio（Python 友好，DS 上手快）
- 实践：把你的 RAG 工具做成一个网页应用

**9. API 服务化**
- 用 FastAPI 把 AI 功能包成 REST API
- 这样可以卖给客户或嵌入其他系统

**10. 部署**
- 免费/低成本方案：Railway、Render、Hugging Face Spaces
- 学会用环境变量管理 API key，不要把 key 写死在代码里

**11. 成本控制**
- 学会估算 token 成本
- 用 prompt caching 降低重复调用费用
- 用小模型（Haiku）处理简单任务，大模型（Opus/Sonnet）处理复杂任务

---

## 阶段四：自雇竞争力（持续）

### 目标：形成自己的 AI 服务能力

**12. 自动化工作流**
- 用 Claude + Python 自动化你日常的 DS 工作
- 例：自动生成数据报告、自动写分析摘要、自动清洗数据

**13. 多模态**
- 让 Claude 读图（截图、图表、PDF 扫描件）
- 实践：自动分析客户发来的图表截图

**14. 评估与质量控制**
- 学会评估 LLM 输出质量（LLM-as-judge）
- 建立自己的 prompt 版本管理习惯

---

## 推荐的学习资源

| 资源 | 用途 |
|------|------|
| [Anthropic 官方文档](https://docs.anthropic.com) | API、工具、最佳实践 |
| [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook) | 代码示例 |
| [LangChain 文档](https://python.langchain.com) | RAG、Agent 框架 |
| fast.ai | 深度学习基础（如需补充） |
| Claude 本身 | 每个知识点都可以直接问它 |

---

## 用 Claude 学习的技巧

1. **让 Claude 出题考你**："给我出 3 道关于 RAG 的实践题"
2. **让 Claude 做代码 review**：把你写的代码贴给它，让它指出问题
3. **让 Claude 解释错误**：把报错信息直接粘贴，让它解释原因
4. **项目驱动学习**：每个阶段都做一个真实小项目，比看教程有效 10 倍
5. **让 Claude 模拟客户**："假设你是一个需要数据报告的客户，问我问题"

---

## 里程碑检查点

- [ ] 阶段一完成：能用 API 写一个对话机器人
- [ ] 阶段二完成：能做一个读自己文档的 RAG 系统
- [ ] 阶段三完成：能把 AI 工具部署成网页给客户用
- [ ] 阶段四持续：有 2–3 个可复用的 AI 工具模板

---

*最后更新：2026-04-17*
