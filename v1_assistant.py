import os

import doc_tools as rag_demo
import health_tools as step3_tool_use


HEALTH_KEYWORDS = [
    "体重",
    "多重",
    "腰围",
    "肚脐",
    "胸围",
    "臀围",
    "大腿",
    "小腿",
    "大臂",
    "减肥",
    "身体",
]

HEALTH_PHRASES = [
    "体重趋势",
    "体重变化",
    "体重多少",
    "多重",
    "减肥进展",
    "减肥效果",
    "体重下降",
    "体重上升",
    "腰臀比",
    "腰臀",
    "bmi",
    "身体质量指数",
    "体重指数",
]


def is_health_question(text: str) -> bool:
    q = text.lower()
    if any(phrase in q for phrase in HEALTH_PHRASES):
        return True
    return any(keyword in q for keyword in HEALTH_KEYWORDS)


def health_answer(query: str) -> None:
    print("\n[路由到身体数据分析模块]")
    direct = step3_tool_use.parse_health_query(query)
    if direct is None:
        print("\n回答：我不确定这是哪个身体指标问题，请更明确地问体重、腰围、肚脐等。\n")
        return
    tool_name, inputs = direct
    result = step3_tool_use.run_tool(tool_name, inputs)
    print(f"\n回答：{result}\n")


def load_rag_chunks() -> list[str]:
    doc_path = "/Users/jingqin/AI/Interview prepare.txt"
    text = rag_demo.load_document(doc_path)
    return rag_demo.chunk_document(text)


def document_answer(query: str, chunks: list[str]) -> None:
    print("\n[路由到文档检索模块]")
    answer = rag_demo.generate(query, chunks)
    print(f"\n回答：{answer}\n")


def main() -> None:
    chunks = load_rag_chunks()
    print("智能问答助手已就绪。")
    print("输入问题，输入 q 退出。\n")

    while True:
        query = input("你的问题：").strip()
        if query.lower() in {"q", "quit", "exit"}:
            break
        if is_health_question(query):
            health_answer(query)
        else:
            document_answer(query, chunks)


if __name__ == "__main__":
    main()
