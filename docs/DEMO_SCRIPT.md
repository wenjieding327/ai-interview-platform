# Demo Script

Use this script for a 3-minute project demo.

## 0:00 - 0:20 Project Positioning

This is an AI interview training platform for AI application development roles. It is not just a chatbot. It combines JWT auth, RAG, a stateful interview agent, structured LLM scoring, retrieval evaluation, logs, tests, and Vercel/Railway deployment.

## 0:20 - 0:50 Login and Session Start

1. Open the Vercel frontend.
2. Register a generated test email.
3. Login.
4. Choose `AI应用开发实习生`.
5. Start interview.

Explain:

```text
/interview/start
  -> JWT auth
  -> RAG retrieval for target role
  -> LLM first question
  -> create InterviewSession
```

## 0:50 - 1:30 Submit an Answer

Answer with a technical response:

```text
我会用 FastAPI 提供 /ask 接口，先做 JWT 鉴权，然后把用户问题转成 embedding，
到 Chroma 中召回候选文档，再做 rerank，把上下文和问题一起发给 LLM。
我会用 Recall@K 和 Hit Rate 评估检索效果，并记录日志用于线上排查。
```

Show:

- next question card
- latest score
- Question Reviews
- Raw Response

Explain:

```text
/interview/session_step
  -> read current_question
  -> read turns_json
  -> evaluate answer
  -> generate next question
  -> save history
```

## 1:30 - 2:00 Show Low-Effort Guardrail

Submit:

```text
?
```

Explain:

The system detects low-effort answers and returns score 0 instead of letting the LLM invent a middle score. It also moves to a different question instead of repeating the same prompt forever.

## 2:00 - 2:30 Show RAG Evaluation

Click `Retrieval Eval`.

Explain:

The project has an eval set in `backend/data/eval_cases.json`. It reports Hit Rate, Recall@1, Recall@3, Recall@5, category summary, misses, and recommendations.

## 2:30 - 2:50 Show Agent Router

Type or use:

```text
请检查RAG检索评估，给我Recall@K和Hit Rate
```

Click `Agent Router`.

Explain:

The backend chooses a tool based on user intent:

```text
ask_rag | retrieval_eval | weakness_report | logs
```

This is a lightweight Tool Calling / LangGraph-style pattern that can later be upgraded to model-driven function calling.

## 2:50 - 3:00 Close With Engineering Quality

Mention:

- pytest + FastAPI TestClient
- GitHub Actions CI
- Docker/Railway deployment
- CORS debugging
- LLM JSON fallback
- logs and Raw Response
