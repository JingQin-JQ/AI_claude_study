import anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── 1. 读取文档 ──────────────────────────────────────────────
def load_document(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ── 2. 切块 ──────────────────────────────────────────────────
def chunk_document(text, chunk_size=200):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# ── 3. 检索：找最相关的块 ────────────────────────────────────
def retrieve(query, chunks, top_k=2):
    vectorizer = TfidfVectorizer()
    all_texts = chunks + [query]
    matrix = vectorizer.fit_transform(all_texts)
    chunk_vecs = matrix[:-1]
    query_vec = matrix[-1]
    scores = cosine_similarity(query_vec, chunk_vecs)[0]
    top_indices = scores.argsort()[-top_k:][::-1]
    return [chunks[i] for i in top_indices]

# ── 4. 生成回答 ──────────────────────────────────────────────
def generate(query, relevant_chunks):
    context = "\n\n".join(relevant_chunks)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="你是一个助手，只根据提供的资料回答问题，不要使用资料以外的知识。",
        messages=[{
            "role": "user",
            "content": f"资料：\n{context}\n\n问题：{query}"
        }]
    )
    return response.content[0].text

# ── 主程序 ───────────────────────────────────────────────────
def main():
    doc_path = "/Users/jingqin/AI/Interview prepare.txt"
    print("正在加载文档...")
    text = load_document(doc_path)
    chunks = chunk_document(text)
    print(f"文档已切成 {len(chunks)} 块\n")

    print("RAG 问答系统已就绪，输入 q 退出\n")
    while True:
        query = input("你的问题：").strip()
        if query.lower() == "q":
            break
        relevant = retrieve(query, chunks)
        answer = generate(query, relevant)
        print(f"\n回答：{answer}\n")

if __name__ == "__main__":
    main()
