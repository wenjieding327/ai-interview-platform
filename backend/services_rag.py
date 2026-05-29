import os
from typing import Dict, Any, List

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_PATH, DATA_PATH

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = chroma_client.get_or_create_collection(
    name="interview_knowledge"
)


def load_seed_documents() -> List[str]:
    if not os.path.exists(DATA_PATH):
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    documents = []

    for line in lines:
        line = line.strip()

        if line:
            documents.append(line)

    return documents


def init_knowledge_base() -> None:
    if collection.count() > 0:
        return

    documents = load_seed_documents()

    for doc in documents:
        add_knowledge_text(doc)


def add_knowledge_text(text: str) -> str:
    doc_id = str(collection.count() + 1)
    embedding = embedding_model.encode(text)

    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding.tolist()]
    )

    return doc_id


def keyword_rerank(query: str, docs: List[str], distances: List[float]) -> List[Dict[str, Any]]:
    """
    简化版Rerank：
    - 向量检索先召回候选
    - 再用关键词重叠 + 向量距离做二次排序
    - 商业版可替换为 bge-reranker / Cohere Rerank

    这不是最强reranker，但能展示RAG工程中“召回 + 重排”的核心思想。
    """
    query_chars = set(query.lower())

    ranked = []

    for idx, doc in enumerate(docs):
        doc_chars = set(doc.lower())
        overlap = len(query_chars & doc_chars)
        distance = distances[idx] if idx < len(distances) else 999

        score = overlap - distance

        ranked.append({
            "doc": doc,
            "distance": distance,
            "keyword_overlap": overlap,
            "rerank_score": score
        })

    ranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    return ranked


def retrieve_context(query: str, top_k: int = 5, candidate_k: int = 15) -> Dict[str, Any]:
    """
    V3 RAG:
    query
    ↓
    embedding
    ↓
    Chroma Top candidate_k 粗召回
    ↓
    keyword_rerank 二次重排
    ↓
    Top top_k 拼接context
    """
    query_embedding = embedding_model.encode(query)

    total_count = max(collection.count(), 1)
    real_candidate_k = min(candidate_k, total_count)

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=real_candidate_k
    )

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    ranked = keyword_rerank(query, docs, distances)

    top_docs = [item["doc"] for item in ranked[:top_k]]
    context = "\n".join(top_docs)

    return {
        "ids": ids,
        "raw_docs": docs,
        "ranked_docs": ranked,
        "docs": top_docs,
        "distances": distances,
        "context": context,
        "best_distance": distances[0] if distances else None
    }


def evaluate_retrieval(test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    简化检索评测：
    test_cases格式：
    [
      {"query": "什么是RAG", "expected_keyword": "检索增强生成"}
    ]

    指标：
    hit_rate = 检索结果中包含expected_keyword的比例
    """
    if not test_cases:
        return {
            "total": 0,
            "hit": 0,
            "hit_rate": 0
        }

    hit = 0
    details = []

    for case in test_cases:
        query = case["query"]
        expected = case["expected_keyword"]

        retrieved = retrieve_context(query, top_k=3)
        context = retrieved["context"]

        is_hit = expected in context

        if is_hit:
            hit += 1

        details.append({
            "query": query,
            "expected_keyword": expected,
            "hit": is_hit,
            "context": context
        })

    return {
        "total": len(test_cases),
        "hit": hit,
        "hit_rate": hit / len(test_cases),
        "details": details
    }
