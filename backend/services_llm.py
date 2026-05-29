from fastapi import HTTPException
from openai import OpenAI
from config import DEEPSEEK_API_KEY
from services_cache import make_key, get_cache, set_cache
from services_logging import log_event

if not DEEPSEEK_API_KEY:
    raise RuntimeError("Missing DEEPSEEK_API_KEY in .env")

llm_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3, use_cache: bool = True) -> str:
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
