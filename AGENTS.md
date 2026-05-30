# AGENTS.md

## Project
This is an AI Interview Training Platform.

Frontend:
- `frontend/index.html`
- Plain HTML/CSS/JavaScript
- Deployed on Vercel
- Calls Railway backend API

Backend:
- `backend/main.py`
- FastAPI
- JWT auth
- RAG with Chroma
- Stateful interview sessions
- DeepSeek API
- Deployed on Railway

## Do not change
- Do not change backend API paths unless absolutely necessary.
- Do not break these endpoints:
  - POST /auth/register
  - POST /auth/login
  - POST /interview/start
  - POST /interview/session_step
  - GET /interview/session/{session_id}
  - POST /ask
  - GET /eval/retrieval
  - GET /report/weakness
  - GET /admin/logs
- Do not expose API keys.
- Do not commit `.env`.
- Keep the default backend URL:
  `https://selfless-rejoicing-production-4735.up.railway.app`

## Current problems to fix
- The AI answer displays raw JSON like `{...}` in the chat, which looks unprofessional.
- The score/evaluation should be parsed and rendered as UI cards.
- The right-side buttons look basic and should be grouped into clean sections.
- Error messages like `Failed to fetch` or `[object Object]` should be converted into human-readable Chinese messages.
- The chat UI should feel like a polished AI product, not a debugging page.
- Keep Raw Response available, but make it collapsible or less visually dominant.
- Improve spacing, button hierarchy, responsive layout, and typography.

## Frontend behavior requirements
- Register and Login must still work.
- After Login, token must be stored in memory and used as `Authorization: Bearer <token>`.
- Start Interview must create a session and show the first question.
- Submit Answer must call `/interview/session_step`.
- If `evaluation` is JSON string, parse it and render:
  - score
  - technical_accuracy
  - rag_understanding
  - agent_understanding
  - backend_understanding
  - project_depth
  - strengths
  - weaknesses
  - suggestion
- Do not display raw JSON inside the main chat bubble.
- Show the follow-up question clearly as “下一问”.
- Keep `Raw Response` only in the right console for debugging.

## Testing checklist
After editing, manually verify:
1. Register
2. Login
3. Start Interview
4. Submit Answer
5. View Memory
6. Ask RAG
7. Retrieval Eval
8. Weakness Report

## Style
- Premium SaaS feeling.
- Dark theme.
- Clean cards.
- Clear Chinese labels.
- Professional, not toy-like.
