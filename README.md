# AI Interview Training Platform

An AI application project for interview training: **FastAPI + RAG + Stateful Agent + Tool Calling demo + structured evaluation + testing + cloud deployment**.

This is not just a chat UI. It is a full AI application workflow:

```text
Vercel Frontend
  -> Railway FastAPI Backend
  -> JWT Auth
  -> SQLite User / Session / History
  -> Chroma Vector DB
  -> SentenceTransformer Embeddings
  -> RAG Retrieval + Rerank
  -> Interview Agent Scoring + Follow-up
  -> Tool Router Agent
  -> Retrieval Evaluation + Logs + Weakness Report
```

## Live Demo

- Frontend: https://ai-interview-platform-taupe-chi.vercel.app
- Backend health: https://selfless-rejoicing-production-4735.up.railway.app/health
- API docs: https://selfless-rejoicing-production-4735.up.railway.app/docs
- Live demo recording: [assets/demo/live_demo_recording.webm](assets/demo/live_demo_recording.webm)
- Competition pitch page: https://ai-interview-platform-taupe-chi.vercel.app/pitch.html

Default backend URL used by the frontend:

```text
https://selfless-rejoicing-production-4735.up.railway.app
```

## Why This Project Is Resume-Ready

Most AI demos stop at:

```text
User question -> Vector search -> LLM answer
```

This project goes further:

- JWT registration/login and protected APIs
- Stateful interview sessions with `current_question` and historical `turns`
- RAG knowledge retrieval using Chroma and SentenceTransformer
- Candidate reranking before context injection
- Structured LLM evaluation with JSON fallback
- Added low-effort answer detection so `"我不知道"` or `"?"` scores 0 and advances to a new question.
- Tool Calling style agent router for RAG, retrieval eval, weakness reports, and logs
- Retrieval evaluation with Hit Rate, Recall@1, Recall@3, Recall@5, misses, and category summaries
- API logging middleware for status code, path, duration, and errors
- pytest + FastAPI TestClient coverage
- Playwright E2E coverage for the real browser flow
- PostgreSQL-ready data layer with Alembic migrations
- GitHub Actions CI
- Vercel frontend + Railway backend deployment

In other words, this project is stronger than a typical AI wrapper because it demonstrates the full application lifecycle: product UI, backend contracts, authenticated state, retrieval quality measurement, agent tool routing, migrations, automated tests, deployment, and debugging evidence.

## Core Features

| Area | Feature |
|---|---|
| Auth | Register, login, JWT bearer auth, user-scoped sessions |
| Interview Agent | Start interview, submit answer, score response, generate next question |
| RAG | Seed knowledge base, upload `.txt`, retrieve context, rerank candidates |
| Tool Router | `/agent/tool-call` chooses Ask RAG, Retrieval Eval, Weakness Report, or Logs |
| Evaluation | Hit Rate, Recall@K, average similarity, category summary, misses |
| Reliability | LLM JSON fallback, low-effort answer scoring, Railway startup fallback |
| Observability | Local JSONL logs and `/admin/logs` endpoint |
| Engineering | pytest, Playwright E2E, Alembic migrations, GitHub Actions CI, Docker/Railway config |
| Frontend | Professional dark UI, scoring cards, next-question cards, right-side console |

## Main User Flow

```text
1. Register / login
2. Choose target role
3. Start interview
4. Backend retrieves role-related knowledge
5. LLM generates first question
6. User submits answer
7. Backend evaluates answer and generates next question
8. Frontend stores per-question reviews in the right console
9. User can inspect RAG eval, weakness report, logs, and raw responses
10. User ends the interview and gets a summary
```

## API Map

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /health` | Health check and prompt version | No |
| `POST /auth/register` | Create user | No |
| `POST /auth/login` | Return JWT access token | No |
| `POST /interview/start` | Create stateful interview session | Yes |
| `POST /interview/session_step` | Score answer, save turn, generate next question | Yes |
| `GET /interview/session/{session_id}` | Read session memory | Yes |
| `POST /interview/session/{session_id}/finish` | Mark session finished | Yes |
| `POST /ask` | RAG question answering | Yes |
| `POST /knowledge/upload` | Upload `.txt` knowledge base lines | Yes |
| `GET /eval/retrieval` | Run retrieval evaluation set | Yes |
| `GET /report/weakness` | Generate weakness report from history | Yes |
| `GET /admin/logs` | Read recent logs | Yes |
| `GET /agent/tools` | List available agent tools | Yes |
| `POST /agent/tool-call` | Route user intent to a backend tool | Yes |

## Tool Calling Demo

The project includes a lightweight deterministic tool router:

```text
User intent
  -> select_agent_tool()
  -> ask_rag | retrieval_eval | weakness_report | logs
  -> execute selected tool
  -> return result + tool trace
```

Example:

```json
{
  "intent": "请检查 RAG 检索评估，给我 Recall@K 和 Hit Rate"
}
```

Response includes:

```json
{
  "selected_tool": "retrieval_eval",
  "reason": "...",
  "tool_scores": {},
  "tool_trace": {},
  "result": {}
}
```

This is intentionally dependency-light and testable. In a production-grade extension, the same contract can be replaced with OpenAI/DeepSeek function calling or a LangGraph workflow.

## Retrieval Evaluation

The evaluation set is stored in:

```text
backend/data/eval_cases.json
```

It covers RAG, embeddings, vector DB, auth, deployment, testing, observability, Function Calling, and prompt engineering.

Returned metrics:

- `hit_rate`
- `recall_at_1`
- `recall_at_3`
- `recall_at_5`
- `average_similarity`
- `category_summary`
- `misses`
- `recommendations`

This lets the project say more than "I used RAG"; it shows how RAG quality is measured.

## Local Development

### Backend

```powershell
cd backend
copy .env.example .env
notepad .env
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Use a local HTTP server instead of opening `frontend/index.html` directly with `file://`.

```powershell
py -m http.server 4173 --bind 127.0.0.1 --directory frontend
```

Open:

```text
http://127.0.0.1:4173/
```

## Tests

```powershell
py -m pytest
```

The tests use fake LLM and fake embeddings to avoid network, cost, and randomness:

- health check
- register/login
- duplicate register
- invalid email/password
- unauthenticated protected APIs
- interview session flow
- evaluation JSON contract
- low-effort answer zero-score behavior
- RAG answer endpoint
- retrieval evaluation metrics
- agent tool router

### End-to-End Browser Test

```powershell
npm install
npx playwright install chromium
npm run e2e
```

The E2E test opens the deployed frontend, registers a fresh test user, logs in, starts an interview, submits an answer, runs Agent Router, and verifies Retrieval Eval output.

## Database Migrations

Local demos still work with SQLite by default. Production deployments can use PostgreSQL by setting:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB_NAME
RUN_DB_MIGRATIONS=true
```

Run migrations:

```powershell
cd backend
alembic upgrade head
```

Docker/Railway startup runs `alembic upgrade head` before `uvicorn`. The FastAPI startup path can also run migrations for PostgreSQL deployments, so the app is not locked to a single Railway build strategy.

## Deployment Notes

### Railway Backend

Railway runs the backend with Docker from the repository root:

```text
Dockerfile
```

Important variables:

```text
DEEPSEEK_API_KEY
JWT_SECRET_KEY
DATABASE_URL
CHROMA_PATH
LOG_PATH
USE_FAKE_LLM
USE_FAKE_EMBEDDINGS
```

For a production-grade data layer, set `DATABASE_URL` to PostgreSQL. Without it, the app falls back to SQLite for local and free-tier demos.

The Dockerfile uses:

```text
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

This avoids the common Railway bug where `$PORT` is treated as a literal string.

### Vercel Frontend

The frontend is static HTML/CSS/JS and calls the Railway backend URL. The backend enables CORS for demo deployment.

## Debugging Stories Worth Discussing in Interviews

- Fixed Vercel -> Railway CORS errors by adding FastAPI CORS middleware.
- Fixed registration 500 caused by bcrypt password length limits.
- Fixed Railway deployment issues caused by nested directories and `$PORT` startup command.
- Added Railway-safe fake embedding fallback and lazy model initialization.
- Prevented raw evaluation JSON from appearing in the chat UI.
- Added low-effort answer detection so `"我不知道"` or `"?"` scores 0 and advances to a new question.
- Added silent login retry for expired JWT during interview submission.

## Resume Bullets

- Built an AI interview training platform with FastAPI, JWT auth, Chroma vector search, SentenceTransformer embeddings, DeepSeek API, and a stateful interview agent.
- Implemented RAG retrieval with candidate reranking and retrieval evaluation using Hit Rate, Recall@K, category summaries, and miss analysis.
- Designed LLM output parsing and fallback logic to handle invalid JSON, missing fields, non-numeric scores, and low-effort answers.
- Added a Tool Calling style agent router that selects RAG, retrieval evaluation, weakness analysis, or log inspection based on user intent.
- Wrote pytest + FastAPI TestClient tests for auth, protected APIs, interview sessions, RAG, retrieval metrics, low-effort scoring, and the agent router.
- Deployed the frontend to Vercel and backend to Railway with Docker, environment variables, CORS, health checks, and request logging.

## Production Roadmap

Planned upgrades:

- PostgreSQL + Alembic migrations
- Playwright E2E tests
- Real reranker model such as BGE Reranker
- Hybrid retrieval with BM25 + vector search
- LangGraph-based agent workflow
- Centralized observability and latency dashboards
- Better role-based access control
- Exportable interview report PDF

See also:

- [Architecture](docs/ARCHITECTURE.md)
- [Project brief](docs/PROJECT_BRIEF.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Pitch page](frontend/pitch.html)
- [Deployment checklist](docs/DEPLOYMENT_CHECKLIST.md)
- [Security policy](SECURITY.md)
