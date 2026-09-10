from typing import Dict, Any, List
import json
import re
import math
from difflib import SequenceMatcher
from fastapi import HTTPException

from services_llm import call_llm
from services_rag import retrieve_context
from prompt_registry import PROMPTS, PROMPT_VERSION
from services_logging import log_event

LOW_EFFORT_ANSWERS = {
    "?", "？", "??", "？？", ".", "...", "。", "xxx", "xx", "x",
    "hello", "hi", "ok", "嗯", "哦", "好", "好的", "你好",
    "我知道", "不知道", "不清楚", "不会", "没有", "随便"
}

TECHNICAL_TERMS = {
    "rag", "agent", "llm", "api", "fastapi", "embedding", "chroma",
    "vector", "token", "jwt", "prompt", "rerank", "recall", "pytest",
    "知识库", "检索", "向量", "召回", "重排", "后端", "接口", "数据库",
    "日志", "测试", "部署", "模型", "评估"
}

NEXT_QUESTION_BANK = [
    "请描述一个你会参与设计的 AI 应用场景，例如智能客服、文档问答助手或面试训练系统。你会如何把 LLM、知识库和业务流程结合起来？",
    "如果一个 RAG 系统回答不准确，你会如何从数据切分、Embedding、召回、Rerank 和 Prompt 五个环节定位问题？",
    "请设计一个 /ask 问答接口的数据流：从用户请求、JWT 鉴权、检索知识库、调用 LLM，到返回结果和记录日志，你会怎么实现？",
    "如果 LLM 返回的评分 JSON 格式不稳定，前端和后端分别应该做哪些兜底，避免页面崩溃或展示原始 JSON？",
    "你会如何评估一个知识库系统的效果？请说明 Hit Rate、Recall@K、平均相似度或人工评测集在项目中的作用。",
    "如果要把这个 AI 面试平台部署到 Vercel 和 Railway，你会如何设计环境变量、健康检查、日志排查和自动化测试流程？"
]


def answer_with_rag(question: str, user_id: int | None = None) -> Dict[str, Any]:
    retrieved = retrieve_context(question, top_k=5, candidate_k=15, user_id=user_id)

    context = retrieved["context"]

    if not context:
        return {
            "question": question,
            "answer": "我无法从资料中找到答案。",
            "retrieved_context": "",
            "warning": "no_context",
            "prompt_version": PROMPT_VERSION
        }

    system_prompt = f"""
{PROMPTS["rag_answer"]}

资料：
{context}
"""

    warning = None
    try:
        answer = call_llm(system_prompt=system_prompt, user_prompt=question, temperature=0.2)
    except HTTPException:
        warning = "practice_mode"
        answer = "AI 服务暂不可用，以下是检索到的知识库原文摘录：\n\n" + context

    return {
        "question": question,
        "answer": answer,
        "warning": warning,
        "retrieved_context": context,
        "ranked_docs": retrieved["ranked_docs"],
        "prompt_version": PROMPT_VERSION
    }


def generate_first_question(target_role: str, user_id: int | None = None) -> Dict[str, Any]:
    query = f"{target_role} 面试 核心知识点"
    retrieved = retrieve_context(query, top_k=5, candidate_k=15, user_id=user_id)
    context = retrieved["context"]

    system_prompt = f"""
你是严格的AI应用开发技术面试官。

请根据目标岗位和资料生成一道难度与岗位相符的面试题。

目标岗位：
{target_role}

资料：
{context}

要求：
1. 只输出一道问题
2. 问题要具体
3. 能考察RAG、Agent、后端API、工程实践中的至少一个点
4. 不要给答案
"""

    warning = None
    try:
        question = call_llm(system_prompt=system_prompt, user_prompt="请生成第一道面试题。", temperature=0.4)
    except HTTPException:
        warning = "practice_mode"
        question = NEXT_QUESTION_BANK[0]

    return {
        "target_role": target_role,
        "retrieved_context": context,
        "ranked_docs": retrieved["ranked_docs"],
        "first_question": question,
        "warning": warning,
        "prompt_version": PROMPT_VERSION
    }


def normalize_answer_text(answer: str) -> str:
    return re.sub(r"\s+", "", (answer or "").strip().lower())


def is_low_effort_answer(answer: str) -> bool:
    cleaned = normalize_answer_text(answer)

    if not cleaned:
        return True

    if cleaned in LOW_EFFORT_ANSWERS:
        return True

    meaningful_chars = re.findall(r"[a-z0-9\u4e00-\u9fff]", cleaned)
    if len(meaningful_chars) < 8:
        return True

    technical_hits = sum(1 for term in TECHNICAL_TERMS if term in cleaned)
    if len(cleaned) < 20 and technical_hits == 0:
        return True

    return False


def low_effort_evaluation() -> str:
    return json.dumps({
        "score": 0,
        "technical_accuracy": 0,
        "rag_understanding": 0,
        "agent_understanding": 0,
        "backend_understanding": 0,
        "project_depth": 0,
        "strengths": ["暂无有效回答内容"],
        "weaknesses": ["回答过短、过于泛泛，或没有回应题目中的技术点"],
        "suggestion": "请结合具体方案、接口设计、RAG流程、Agent状态或工程实践重新回答。"
    }, ensure_ascii=False)


def next_question_after_low_effort(target_role: str, turns: List[Dict[str, Any]]) -> str:
    asked = [turn.get("question", "") for turn in turns]
    question = next((q for q in NEXT_QUESTION_BANK if not any(q in old for old in asked)), NEXT_QUESTION_BANK[-1])

    if target_role:
        return f"{question}\n\n请尽量结合“{target_role}”这个岗位来回答。"

    return question


def evaluate_answer(question: str, answer: str, target_role: str = "", turns: List[Dict[str, Any]] | None = None) -> str:
    turns = turns or []
    history_text = json.dumps(turns[-5:], ensure_ascii=False, indent=2)

    user_prompt = f"""
目标岗位：
{target_role}

最近历史轮次：
{history_text}

当前面试问题：
{question}

候选人回答：
{answer}
"""

    return call_llm(
        system_prompt=PROMPTS["score_answer"],
        user_prompt=user_prompt,
        temperature=0.2
    )


def normalize_evaluation(evaluation: str) -> str:
    required_defaults = {
        "score": None,
        "technical_accuracy": "未提供",
        "rag_understanding": "未提供",
        "agent_understanding": "未提供",
        "backend_understanding": "未提供",
        "project_depth": "未提供",
        "strengths": [],
        "weaknesses": [],
        "suggestion": "建议继续补充回答中的工程细节。"
    }

    parsed = None

    try:
        parsed = evaluation if isinstance(evaluation, dict) else json.loads(evaluation)

    except (json.JSONDecodeError, TypeError):
        evaluation = str(evaluation or "")
        start = evaluation.find("{")
        end = evaluation.rfind("}")

        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(evaluation[start:end + 1])
            except json.JSONDecodeError:
                parsed = None

    if not isinstance(parsed, dict):
        log_event("evaluation_parse_fallback", {
            "format": "non_json"
        })
        parsed = {
            **required_defaults,
            "weaknesses": ["LLM 评分格式不稳定，已触发兜底解析。"],
            "suggestion": ("本轮评分暂不可用，请结合原始回答复盘。" if "{" in evaluation
                           else evaluation.strip()) or required_defaults["suggestion"]
        }

    normalized = {
        **required_defaults,
        **parsed
    }

    try:
        if normalized["score"] is not None:
            score = float(normalized["score"])
            normalized["score"] = max(0, min(100, round(score))) if math.isfinite(score) else None

    except (TypeError, ValueError):
        normalized["score"] = None

    for key in ("strengths", "weaknesses"):
        value = normalized[key]
        if isinstance(value, str):
            normalized[key] = [value]
        elif not isinstance(value, list):
            normalized[key] = []

    return json.dumps(normalized, ensure_ascii=False)


def generate_followup(
    question: str,
    answer: str,
    evaluation: str = "",
    target_role: str = "",
    turns: List[Dict[str, Any]] | None = None
) -> str:
    turns = turns or []
    history_text = json.dumps(turns[-5:], ensure_ascii=False, indent=2)

    user_prompt = f"""
目标岗位：
{target_role}

历史轮次：
{history_text}

当前问题：
{question}

候选人回答：
{answer}

评分结果：
{evaluation}

请生成下一道追问。
"""

    return call_llm(
        system_prompt=PROMPTS["followup"],
        user_prompt=user_prompt,
        temperature=0.4
    )


def run_interview_step(
    target_role: str,
    question: str,
    answer: str,
    turns: List[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    turns = turns or []

    if is_low_effort_answer(answer):
        evaluation = low_effort_evaluation()
        followup_question = next_question_after_low_effort(target_role, turns + [{"question": question}])

        return {
            "target_role": target_role,
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "followup_question": followup_question,
            "prompt_version": PROMPT_VERSION
        }

    try:
        evaluation_raw = evaluate_answer(question=question, answer=answer, target_role=target_role, turns=turns)
    except HTTPException:
        return {
            "target_role": target_role, "question": question, "answer": answer,
            "evaluation": json.dumps({"score": None, "status": "ungraded",
                "strengths": [], "weaknesses": [],
                "suggestion": "AI 服务暂不可用，本轮回答已保存但未评分，可导出后复盘。"}, ensure_ascii=False),
            "followup_question": next_question_after_low_effort(target_role, turns + [{"question": question}]),
            "warning": "practice_mode", "prompt_version": PROMPT_VERSION
        }
    evaluation = normalize_evaluation(evaluation_raw)

    try:
        followup_question = generate_followup(
            question=question, answer=answer, evaluation=evaluation,
            target_role=target_role, turns=turns
        )
    except HTTPException:
        followup_question = ""
    asked = [item.get("question", "") for item in turns] + [question]
    if (not followup_question or "{" in followup_question or len(followup_question) > 1200
            or any(SequenceMatcher(None, followup_question, old).ratio() > 0.8 for old in asked)):
        followup_question = next_question_after_low_effort(target_role, turns + [{"question": question}])

    return {
        "target_role": target_role,
        "question": question,
        "answer": answer,
        "evaluation": evaluation,
        "followup_question": followup_question,
        "prompt_version": PROMPT_VERSION
    }


def generate_weakness_report(history_text: str) -> str:
    return call_llm(
        system_prompt=PROMPTS["weakness_report"],
        user_prompt=history_text,
        temperature=0.3
    )


def summarize_turns(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    reviews = [json.loads(normalize_evaluation(turn.get("evaluation", ""))) for turn in turns]
    scores = [review["score"] for review in reviews if review["score"] is not None]
    average = round(sum(scores) / len(scores), 1) if scores else None
    strengths, weaknesses, suggestions = [], [], []
    for review in reviews:
        for key, target in (("strengths", strengths), ("weaknesses", weaknesses)):
            for item in review[key]:
                if isinstance(item, str) and item not in target:
                    target.append(item)
        suggestion = review.get("suggestion")
        if isinstance(suggestion, str) and suggestion not in suggestions:
            suggestions.append(suggestion)
    score_text = f"已评分 {len(scores)} 轮，平均 {average:g} / 100 分。" if scores else "暂无可用评分。"
    text = f"本场面试完成 {len(turns)} 轮。{score_text}"
    for title, items in (("主要优势", strengths), ("主要短板", weaknesses), ("下一步建议", suggestions)):
        text += f"\n\n{title}：\n" + "\n".join(f"- {item}" for item in items[:5])
    return {"summary": text, "average_score": average, "score_scale": 100,
            "scored_turns": len(scores), "turn_count": len(turns),
            "strengths": strengths[:5], "weaknesses": weaknesses[:5], "suggestions": suggestions[:5]}
