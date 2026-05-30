from fastapi import HTTPException
from openai import OpenAI
from config import DEEPSEEK_API_KEY, USE_FAKE_LLM
from services_cache import make_key, get_cache, set_cache
from services_logging import log_event

llm_client = None

if DEEPSEEK_API_KEY:
    llm_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )


def fake_llm_response(system_prompt: str, user_prompt: str) -> str:
    prompt = f"{system_prompt}\n{user_prompt}"

    if "score" in prompt.lower() or "评分" in prompt:
        return """
{
  "score": 82,
  "technical_accuracy": 80,
  "rag_understanding": 84,
  "agent_understanding": 78,
  "backend_understanding": 86,
  "project_depth": 82,
  "strengths": ["回答覆盖了核心流程", "能把 RAG 与后端接口联系起来"],
  "weaknesses": ["对评估指标和异常处理说明还不够具体"],
  "suggestion": "补充 Recall@K、日志追踪、LLM 输出兜底和接口测试设计。"
}
""".strip()

    if "追问" in prompt or "follow" in prompt.lower():
        return "如果 LLM 返回的评分 JSON 格式错误，你会如何设计解析、降级和日志记录机制？"

    if "弱点" in prompt or "weakness" in prompt.lower():
        return "候选人需要继续加强 RAG 评估、异常输入处理、线上日志排查和 Agent 状态管理。"

    return "请设计一个面向 AI 应用开发岗位的 RAG 面试系统，并说明知识库构建、检索评估、Agent 追问和后端接口测试方案。"


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3, use_cache: bool = True) -> str:
    if USE_FAKE_LLM:
        log_event("llm_fake_response", {
            "user_prompt_preview": user_prompt[:200],
            "temperature": temperature
        })
        return fake_llm_response(system_prompt, user_prompt)

    if llm_client is None:
        log_event("llm_call_failed", {"error": "Missing DEEPSEEK_API_KEY"})
        raise HTTPException(
            status_code=500,
            detail="LLM call failed: missing DEEPSEEK_API_KEY"
        )

    cache_key = make_key("llm", {
        "system": system_prompt,
        "user": user_prompt,
        "temperature": temperature
    })

    if use_cache:
        cached = get_cache(cache_key)

        if cached:
            log_event("llm_cache_hit", {"key": cache_key})
            return cached

    try:
        log_event("llm_call_start", {
            "user_prompt_preview": user_prompt[:200],
            "temperature": temperature
        })

        response = llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )

        content = response.choices[0].message.content

        if use_cache:
            set_cache(cache_key, content)

        log_event("llm_call_success", {
            "response_preview": content[:200]
        })

        return content

    except Exception as e:
        log_event("llm_call_failed", {"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"LLM call failed: {str(e)}"
        )
