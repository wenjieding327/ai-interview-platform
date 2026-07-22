# Interview Prep Guide

This file is the speaking guide for using the project in job interviews.

## 30-Second Pitch

I built an AI interview training platform for AI application developer candidates. The frontend is a pure HTML/CSS/JS app deployed on Vercel, and the backend is a FastAPI service on Railway. It includes JWT auth, stateful interview sessions, RAG retrieval with Chroma, structured LLM evaluation, a Tool Calling style agent router, retrieval evaluation metrics, logs, pytest tests, and GitHub Actions CI.

## 2-Minute Project Walkthrough

First, the user registers or logs in. The backend returns a JWT token, and all protected APIs use `Authorization: Bearer <token>`.

Second, the user starts an interview by choosing a target role. The backend creates a session, retrieves related knowledge from the RAG knowledge base, and asks the first question.

Third, after each answer, the backend evaluates the answer with a structured JSON schema. The frontend parses the evaluation and displays score, strengths, weaknesses, and suggestions as readable cards instead of raw JSON.

Fourth, the project includes an Agent Tool Router. Given a user intent, it selects one of several backend tools: Ask RAG, Retrieval Eval, Weakness Report, or Logs. This demonstrates the core idea of tool use and agent orchestration in a simple, testable way.

Fifth, I added engineering evidence: pytest tests, boundary cases, GitHub Actions CI, Docker deployment, Railway/Vercel deployment, and operational logs.

## Questions You Should Be Ready For

### Why did you use RAG?

Because interview questions and explanations should be grounded in a maintainable knowledge base. RAG lets me update AI application knowledge without changing model weights.

### How do you evaluate RAG quality?

I created an evaluation set in `backend/data/eval_cases.json`. The backend calculates Hit Rate, Recall@1, Recall@3, Recall@5, average similarity, category summaries, misses, and recommendations.

### What is the Agent part?

The project has two agent-like parts. The interview flow is stateful and uses prior turns to continue the session. The Tool Router selects a backend tool based on intent and returns a traceable result.

### How did you handle unstable LLM output?

The frontend and backend are designed with fallbacks. If evaluation is returned as a JSON string, the frontend parses it. If fields are missing or invalid, the UI degrades to readable text instead of breaking.

### What engineering work makes this credible?

The project includes auth, protected APIs, session persistence, tests, CI, deployment docs, Docker/Railway configuration, logs, and error handling. It is not just a local prompt demo.

## Strong Resume Version

Built and deployed an AI interview training platform using FastAPI, JWT, Chroma, RAG, structured LLM evaluation, and an agent-style tool router. Added retrieval evaluation with Hit Rate and Recall@K, pytest API coverage, GitHub Actions CI, and Vercel/Railway deployment.

## What To Admit Honestly

- It is not yet a production SaaS.
- SQLite is fine for the demo, but PostgreSQL would be better for production.
- The tool router is deterministic for testability; a production version could use function calling or LangGraph.
- The hosted demo may use fake embeddings for stable free-tier deployment.
