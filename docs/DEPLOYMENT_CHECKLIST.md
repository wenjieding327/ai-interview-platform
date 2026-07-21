# Deployment Checklist

This project is designed to run as a split deployment:

- Frontend: Vercel static site
- Backend: Railway FastAPI service
- Database: SQLite inside the Railway service runtime
- RAG data: `backend/data/interview_qa.txt` and `backend/data/eval_cases.json`

## Expected Production URLs

- Frontend: `https://ai-interview-platform-taupe-chi.vercel.app`
- Backend: `https://selfless-rejoicing-production-4735.up.railway.app`

The frontend default API URL must stay:

```text
https://selfless-rejoicing-production-4735.up.railway.app
```

## Railway Configuration

Use the repository root as the Railway root directory. The root `Dockerfile` copies the backend app and starts FastAPI with Railway's `$PORT`.

Required files:

- `Dockerfile`
- `railway.json`
- `backend/requirements.txt`
- `backend/main.py`

Recommended Railway variables:

```text
JWT_SECRET_KEY=<a strong random secret>
DEEPSEEK_API_KEY=<optional real LLM key>
USE_FAKE_LLM=false
USE_FAKE_EMBEDDINGS=true
```

Use `USE_FAKE_EMBEDDINGS=true` on the hosted demo if you want stable, free retrieval behavior without downloading local embedding models during deployment.

## Smoke Tests

After each deploy, verify these endpoints:

```powershell
Invoke-RestMethod https://selfless-rejoicing-production-4735.up.railway.app/health

$openapi = (Invoke-WebRequest https://selfless-rejoicing-production-4735.up.railway.app/openapi.json).Content
$openapi.Contains('/agent/tools')
$openapi.Contains('/agent/tool-call')
```

Expected result:

- `/health` returns JSON with `status: ok`
- `/openapi.json` contains the interview, RAG, eval, logs, and agent router endpoints

## If Railway Returns 404

A 404 from `/health` usually means the custom domain is not serving this FastAPI app. Check these items in Railway:

- The service is connected to the correct GitHub repo.
- The deployed commit is the latest `main` commit.
- The service root directory is the repository root, not a stale folder.
- The custom domain points to the FastAPI service, not another Railway service.
- The deploy log shows `uvicorn main:app --host 0.0.0.0 --port`.
- Variables are saved and the service was redeployed after changing them.

## Vercel Configuration

The frontend is a static HTML/CSS/JS app. Vercel should serve `frontend/index.html`.

Smoke test:

```powershell
$html = (Invoke-WebRequest https://ai-interview-platform-taupe-chi.vercel.app).Content
$html.Contains('Agent Router')
$html.Contains('/agent/tool-call')
```

If the frontend is updated but backend calls fail, debug Railway first.

## GitHub Evidence

Use this evidence in the resume/project interview:

- CI runs static safety checks, compile checks, and backend tests on every push and pull request.
- Tests cover auth, JWT, interview sessions, RAG, retrieval evaluation, and agent tool routing.
- Deployment docs explain frontend/backend separation and production smoke testing.
- The app includes fallback behavior for low-quality answers, unstable LLM JSON, and auth failures.
