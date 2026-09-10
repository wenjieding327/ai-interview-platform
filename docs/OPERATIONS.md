# Deployment And Recovery

## Supported Runtime

- Frontend: https://ai-interview-platform-taupe-chi.vercel.app
- Backend: https://selfless-rejoicing-production-4735.up.railway.app
- Static HTML/CSS/JS. Vercel rewrites `/api/*` to existing backend paths.
- Railway uses one backend instance with a persistent volume mounted at `/data`.
- Without `DATABASE_URL`, `RAILWAY_VOLUME_MOUNT_PATH` selects the SQLite database and log directory. Local development defaults to `backend/storage`.
- Alembic creates parent directories before connecting. Re-running migrations is safe.
- `/health` verifies database connectivity. `llm_mode=configured` means a key is present, not that provider credit has been verified.

## Model Availability

Set `DEEPSEEK_API_KEY` privately in Railway and keep `USE_FAKE_LLM=false` in public deployments. `USE_FAKE_LLM=true` is a labeled test fixture, not a candidate-assessment model.

If the provider fails, the local question bank starts practice mode. A meaningful answer is saved as ungraded; explicit non-answers are zero by application rule. Summaries exclude missing scores. RAG returns labeled source excerpts instead of an invented model answer when the provider is unavailable.

The model timeout defaults to 30 seconds without SDK retries. Browser requests time out after 75 seconds and preserve uncertain submissions. Failed follow-up generation does not discard a successful evaluation.

## Session Recovery

1. Sign in with the same email and password. Refresh intentionally requires signing in again; tokens stay in memory.
2. Choose a historical interview and restore/review it.
3. If a response was lost after saving, retry the same answer. The persisted request ID prevents duplicate turns.
4. For a stale-turn conflict, restore the server's version first. Another tab may have already submitted or finished.
5. A failed finish stays retryable. A final summary appears only after server confirmation.
6. Export a review as text. Unsent drafts are local to the browser tab; successful turns live in the database.

## Retrieval Modes

`RETRIEVAL_MODE=lexical` uses `rank-bm25` over bilingual tokens. It needs neither GPU libraries nor a model download. Seed documents are public and uploaded documents are user-scoped. Stable content IDs deduplicate identical uploads.

`RETRIEVAL_MODE=vector` requires `pip install -r backend/requirements-vector.txt` and a larger machine. It uses Chroma, SentenceTransformer, and a keyword reranker. Model load errors are not silently replaced with random embeddings. Documents are owner-filtered in both modes.

The evaluation set uses expected keywords: historical Recall@1/3/5 fields are keyword hit-at-K proxies, not exhaustive multi-document recall. BM25 has no vector similarity; that field is null. Report the mode and metric definition with any benchmark result.

## PostgreSQL

Set `DATABASE_URL` to a PostgreSQL URL for a higher-concurrency deployment. `postgres://` and `postgresql://` are normalized to the installed psycopg driver. Alembic preserves percent-escaped passwords. To verify a provisioned test database, set `TEST_DATABASE_URL` and run pytest. The current hosted configuration and completed deployment tests use SQLite.

Changing the URL does not move old data. Back up the SQLite database and verify a separate data transfer before switching a populated service.

## Checks

```powershell
py -3.11 -m pip install -r backend/requirements-dev.txt
py -3.11 -m pytest
py -3.11 -m ruff check backend
npm ci
npx playwright install chromium
npm run e2e
```

Playwright starts isolated local servers. Setting `E2E_BASE_URL` enables an explicit cloud smoke test that creates synthetic accounts; normal CI does not write to the public demo.

Require `/health` success before activating a Railway deployment. Verify the `/data` mount and confirm account/session retention after redeploying. Persistent volumes are not independent backups; configure snapshots or database backups before storing important production data.

## Network And Scope

Same-origin proxying removes the browser's separate direct connection to Railway. It cannot guarantee Vercel availability in mainland China. Stable local-market hosting requires a suitable provider and domain, with applicable registration handled separately.

This is a single-instance portfolio application, not an audited enterprise service. Email verification, password reset, distributed workers, billing, production rate limiting, and independent recovery backups are not implemented. The tool router is deterministic intent routing, not autonomous multi-step planning.
