# Project Brief

## One-Line Pitch

AI Interview Training Platform is a deployable AI application that combines RAG, a stateful interview agent, structured scoring, tool routing, retrieval evaluation, testing, and cloud deployment.

## Problem

People preparing for AI application development roles need more than generic chatbot practice. They need role-specific technical questions, structured feedback, follow-up questions, and a way to review weaknesses across multiple rounds.

## Solution

The platform lets a user register, choose a target role, start an interview, answer questions, receive structured scoring, continue with follow-up questions, and review per-question strengths and weaknesses. It also exposes RAG tools, retrieval evaluation, logs, and weakness reports.

## Architecture

```text
Browser
  -> frontend/index.html on Vercel
  -> FastAPI backend on Railway
  -> JWT auth
  -> SQLite for users, sessions, history
  -> Chroma for vector retrieval
  -> SentenceTransformer embeddings
  -> DeepSeek-compatible LLM API
```

## AI Engineering Highlights

- RAG knowledge retrieval with Chroma.
- Rerank step after coarse vector recall.
- Stateful interview agent with `InterviewSession.current_question` and `turns_json`.
- Structured LLM evaluation contract.
- JSON parse fallback for unstable LLM output.
- Low-effort answer detection and zero-score handling.
- Tool Calling style router for RAG, retrieval evaluation, weakness report, and logs.
- Retrieval evaluation set with Recall@K and category summaries.

## Backend Engineering Highlights

- FastAPI APIs with Pydantic validation.
- JWT authentication and user-scoped data access.
- SQLAlchemy models for users, interview sessions, and history.
- Request logging middleware for path, status code, duration, and errors.
- Dockerfile for Railway deployment.
- Fake LLM and fake embeddings for reliable automated tests.

## Test Coverage

The pytest suite covers:

- health check
- register/login
- duplicate register
- invalid inputs
- protected API auth boundaries
- interview session flow
- evaluation JSON contract
- low-effort scoring
- RAG endpoint
- retrieval metrics
- agent tool router

## What Makes It More Than a Demo

It contains the parts interviewers expect in real AI application work:

- auth
- state
- RAG
- evaluation
- error handling
- observability
- tests
- deployment
- product-facing frontend
- debug-friendly raw responses

## Known Limits

- SQLite is suitable for demos but should move to PostgreSQL for production.
- Rerank is currently a lightweight keyword-and-distance strategy.
- Tool routing is deterministic and testable; it can later be replaced by real function calling or LangGraph.
- Frontend is plain HTML/CSS/JS for deploy simplicity; a larger product could migrate to React or Next.js.
