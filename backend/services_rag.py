import os
import hashlib
from typing import Dict, Any, List

import chromadb

from config import CHROMA_PATH, DATA_PATH, USE_FAKE_EMBEDDINGS
from services_logging import log_event


class FakeEmbeddingModel:
    def encode(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest]


embedding_model = None
knowledge_initialized = False

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

COLLECTION_NAME = (
    "interview_knowledge_fake"
    if USE_FAKE_EMBEDDINGS
    else "interview_knowledge"
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)


def get_embedding_model():
    global embedding_model

    if embedding_model is not None:
        return embedding_model

    if USE_FAKE_EMBEDDINGS:
        log_event("embedding_fake_model_enabled", {})
        embedding_model = FakeEmbeddingModel()
        return embedding_model

    try:
        from sentence_transformers import SentenceTransformer

        embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        return embedding_model

    except Exception as exc:
        log_event("embedding_model_fallback", {"error": str(exc)})
        embedding_model = FakeEmbeddingModel()
        return embedding_model


def encode_text(text: str) -> List[float]:
    embedding = get_embedding_model().encode(text)
    return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)


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
    global knowledge_initialized

    if knowledge_initialized:
        return

    if collection.count() > 0:
        knowledge_initialized = True
        return

    documents = load_seed_documents()

    for doc in documents:
        add_knowledge_text(doc)

    knowledge_initialized = True


def add_knowledge_text(text: str) -> str:
    doc_id = str(collection.count() + 1)
    vector = encode_text(text)

    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[vector]
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
    init_knowledge_base()
    query_vector = encode_text(query)

    total_count = collection.count()
    if total_count == 0:
        return {
            "ids": [],
            "raw_docs": [],
            "ranked_docs": [],
            "docs": [],
            "distances": [],
            "context": "",
            "best_distance": None
        }

    real_candidate_k = min(candidate_k, total_count)

    results = collection.query(
        query_embeddings=[query_vector],
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
            "total_cases": 0,
            "hit": 0,
            "hit_rate": 0,
            "recall_at_1": 0,
            "recall_at_3": 0,
            "recall_at_5": 0,
            "average_similarity": 0,
            "details": [],
            "misses": [],
            "category_summary": {}
        }

    hit = 0
    recall_hits = {
        1: 0,
        3: 0,
        5: 0
    }
    similarity_scores = []
    details = []
    category_summary: Dict[str, Dict[str, Any]] = {}

    for case in test_cases:
        query = case["query"]
        expected = case["expected_keyword"]
        category = case.get("category", "uncategorized")

        retrieved = retrieve_context(query, top_k=5)
        ranked_docs = retrieved["ranked_docs"]
        docs = [item["doc"] for item in ranked_docs]
        context = "\n".join(docs[:3])

        is_hit = any(expected in doc for doc in docs[:3])

        if is_hit:
            hit += 1

        for k in recall_hits:
            if any(expected in doc for doc in docs[:k]):
                recall_hits[k] += 1

        distances = [
            item.get("distance")
            for item in ranked_docs[:5]
            if item.get("distance") is not None
        ]
        if distances:
            similarity_scores.append(
                sum(1 / (1 + max(float(distance), 0)) for distance in distances) / len(distances)
            )

        details.append({
            "query": query,
            "expected_keyword": expected,
            "category": category,
            "hit": is_hit,
            "recall_at_1": any(expected in doc for doc in docs[:1]),
            "recall_at_3": any(expected in doc for doc in docs[:3]),
            "recall_at_5": any(expected in doc for doc in docs[:5]),
            "top_docs": docs[:5],
            "average_similarity": (
                sum(1 / (1 + max(float(distance), 0)) for distance in distances) / len(distances)
                if distances else 0
            ),
            "context": context
        })

        if category not in category_summary:
            category_summary[category] = {
                "total": 0,
                "hit": 0
            }

        category_summary[category]["total"] += 1
        if is_hit:
            category_summary[category]["hit"] += 1

    for category, stats in category_summary.items():
        stats["hit_rate"] = stats["hit"] / stats["total"] if stats["total"] else 0

    misses = [
        detail
        for detail in details
        if not detail["hit"]
    ]

    hit_rate = hit / len(test_cases)
    recall_at_1 = recall_hits[1] / len(test_cases)
    recall_at_3 = recall_hits[3] / len(test_cases)
    recall_at_5 = recall_hits[5] / len(test_cases)
    average_similarity = (
        sum(similarity_scores) / len(similarity_scores)
        if similarity_scores else 0
    )

    return {
        "total": len(test_cases),
        "total_cases": len(test_cases),
        "hit": hit,
        "hit_rate": hit_rate,
        "recall_at_1": recall_at_1,
        "recall_at_3": recall_at_3,
        "recall_at_5": recall_at_5,
        "average_similarity": average_similarity,
        "category_summary": category_summary,
        "misses": misses,
        "recommendations": [
            "Review misses first; they usually indicate chunking, keyword coverage, or rerank issues.",
            "Compare Recall@1 with Recall@5 to decide whether reranking or retrieval breadth needs improvement.",
            "Keep eval_cases.json versioned so RAG quality can be checked in CI or before deployment."
        ],
        "details": details
    }
