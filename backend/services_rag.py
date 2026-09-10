import os
import hashlib
from typing import Dict, Any, List

import re
import threading
import time
from rank_bm25 import BM25Okapi
from sqlalchemy.exc import IntegrityError

from config import CHROMA_PATH, DATA_PATH, RETRIEVAL_MODE
from database import SessionLocal
from models import KnowledgeDocument
from services_logging import log_event


embedding_model = None
knowledge_initialized = False
collection = None
index_lock = threading.RLock()


def get_embedding_model():
    global embedding_model

    if embedding_model is not None:
        return embedding_model

    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
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

    with index_lock:
        if not knowledge_initialized:
            for doc in load_seed_documents():
                add_knowledge_text(doc)
            knowledge_initialized = True


def add_knowledge_text(text: str, user_id: int | None = None) -> str:
    owner = "seed" if user_id is None else str(user_id)
    doc_id = hashlib.sha256(f"{owner}:{text}".encode("utf-8")).hexdigest()
    with SessionLocal() as db:
        if db.get(KnowledgeDocument, doc_id) is None:
            db.add(KnowledgeDocument(id=doc_id, owner=owner, content=text))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
    return doc_id


def knowledge_count(user_id: int | None = None) -> int:
    with SessionLocal() as db:
        owners = ["seed"] + ([str(user_id)] if user_id is not None else [])
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.owner.in_(owners)).count()


def tokenize(text: str) -> List[str]:
    # Chinese bigrams plus Latin terms work without downloading an embedding model.
    tokens = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower())
    for chunk in re.findall(r"[\u4e00-\u9fff]+", text):
        tokens.extend(chunk[i:i + 2] for i in range(len(chunk) - 1))
    return tokens or [""]


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


def retrieve_context(query: str, top_k: int = 5, candidate_k: int = 15, user_id: int | None = None) -> Dict[str, Any]:
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
    started = time.perf_counter()
    init_knowledge_base()
    owners = ["seed"] + ([str(user_id)] if user_id is not None else [])
    with SessionLocal() as db:
        documents = db.query(KnowledgeDocument).filter(KnowledgeDocument.owner.in_(owners)).all()
    if not documents:
        return {
            "ids": [],
            "raw_docs": [],
            "ranked_docs": [],
            "docs": [],
            "distances": [],
            "context": "",
            "best_distance": None
        }

    mode = RETRIEVAL_MODE
    if mode == "vector":
        global collection
        import chromadb
        with index_lock:
            if collection is None:
                collection = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection(
                    name="interview_knowledge_scoped_v1"
                )
            existing = set(collection.get(ids=[doc.id for doc in documents])["ids"])
            for doc in documents:
                if doc.id not in existing:
                    collection.upsert(ids=[doc.id], documents=[doc.content],
                                      embeddings=[encode_text(doc.content)], metadatas=[{"owner": doc.owner}])
            result = collection.query(query_embeddings=[encode_text(query)],
                                      n_results=min(candidate_k, len(documents)),
                                      where={"owner": {"$in": owners}})
        ids = result["ids"][0]
        docs = result["documents"][0]
        distances = result["distances"][0]
        ranked = keyword_rerank(query, docs, distances)
    else:
        scores = BM25Okapi([tokenize(doc.content) for doc in documents]).get_scores(tokenize(query))
        candidates = sorted(zip(documents, scores), key=lambda item: (-item[1], item[0].id))[:candidate_k]
        ranked = [{"doc": doc.content, "id": doc.id, "distance": None,
                   "rerank_score": float(score), "bm25_score": float(score)}
                  for doc, score in candidates if score > 0]
        ids = [item["id"] for item in ranked]
        docs = [item["doc"] for item in ranked]
        distances = []

    top_docs = [item["doc"] for item in ranked[:top_k]]
    context = "\n".join(top_docs)
    log_event("rag_retrieval", {"mode": mode, "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                                "result_count": len(top_docs)})

    return {
        "ids": ids,
        "raw_docs": docs,
        "ranked_docs": ranked,
        "docs": top_docs,
        "distances": distances,
        "context": context,
        "best_distance": distances[0] if distances else None,
        "retrieval_mode": mode
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
        if similarity_scores else None
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
        "retrieval_mode": RETRIEVAL_MODE,
        "metric_note": "Recall@K fields are keyword-hit proxies, not multi-document recall. BM25 scores are not vector similarity.",
        "category_summary": category_summary,
        "misses": misses,
        "recommendations": [
            "Review misses first; they usually indicate chunking, keyword coverage, or rerank issues.",
            "Compare Recall@1 with Recall@5 to decide whether reranking or retrieval breadth needs improvement.",
            "Keep eval_cases.json versioned so RAG quality can be checked in CI or before deployment."
        ],
        "details": details
    }
