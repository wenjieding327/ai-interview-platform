from typing import Dict, Any, List

from services_logging import log_event


AGENT_TOOLS = [
    {
        "name": "ask_rag",
        "label": "Ask RAG",
        "description": "Use RAG knowledge retrieval to answer a technical question."
    },
    {
        "name": "retrieval_eval",
        "label": "Retrieval Eval",
        "description": "Run the retrieval evaluation set and return Hit Rate / Recall@K metrics."
    },
    {
        "name": "weakness_report",
        "label": "Weakness Report",
        "description": "Summarize recent interview history into weaknesses and next training steps."
    },
    {
        "name": "logs",
        "label": "Logs",
        "description": "Inspect recent API and model-call logs for debugging."
    }
]


TOOL_KEYWORDS = {
    "logs": {
        "日志", "log", "logs", "报错", "错误", "失败", "500", "401",
        "railway", "vercel", "debug", "排查", "耗时", "latency"
    },
    "retrieval_eval": {
        "检索评估", "评估", "recall", "recall@k", "hit rate", "hit_rate",
        "召回", "命中", "相似度", "retrieval", "eval", "指标", "rag评估"
    },
    "weakness_report": {
        "弱点", "短板", "weakness", "report", "报告", "复盘", "建议",
        "训练计划", "能力", "哪里不好", "薄弱"
    },
    "ask_rag": {
        "rag", "知识库", "解释", "什么是", "怎么理解", "向量",
        "embedding", "agent", "prompt", "fastapi", "jwt", "chroma"
    }
}


def available_agent_tools() -> List[Dict[str, str]]:
    return AGENT_TOOLS


def select_agent_tool(intent: str) -> Dict[str, Any]:
    normalized = (intent or "").strip().lower()
    scores = {}

    for tool_name, keywords in TOOL_KEYWORDS.items():
        scores[tool_name] = sum(1 for keyword in keywords if keyword in normalized)

    selected = max(scores, key=scores.get)

    if scores[selected] == 0:
        selected = "ask_rag"

    reason_map = {
        "ask_rag": "The intent looks like a knowledge question, so the agent selected RAG retrieval.",
        "retrieval_eval": "The intent asks about retrieval quality or Recall@K metrics, so the agent selected retrieval evaluation.",
        "weakness_report": "The intent asks for weaknesses or training advice, so the agent selected the weakness report tool.",
        "logs": "The intent mentions errors, logs, deployment, or debugging, so the agent selected logs."
    }

    decision = {
        "selected_tool": selected,
        "reason": reason_map[selected],
        "scores": scores,
        "available_tools": AGENT_TOOLS
    }

    log_event("agent_tool_selected", decision)

    return decision
