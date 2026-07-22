# 2-Minute Demo Video Script

Use this as the voiceover script for `assets/demo/ai_interview_platform_2min_demo.mp4`.

## 0:00-0:16 Opening

This is an AI Interview Training Platform for AI application developer candidates. It is built with FastAPI, RAG, a stateful interview agent, retrieval evaluation, and cloud deployment on Vercel and Railway.

## 0:16-0:34 Product Flow

The candidate registers or logs in with JWT authentication, chooses a target role, and starts a mock interview. The backend keeps a session with the current question, historical turns, and per-question evaluation.

## 0:34-0:52 RAG System

The platform uses a knowledge base, embeddings, Chroma vector search, and reranking. Retrieved context is injected into prompts so the interview can focus on real AI application engineering topics.

## 0:52-1:12 Agent Router

The Tool Router demonstrates an agent-style workflow. It can select Ask RAG, Retrieval Eval, Weakness Report, or Logs according to user intent, execute the selected backend tool, and return a traceable result.

## 1:12-1:30 Engineering Evidence

The project is not just a one-time demo. It includes pytest tests, FastAPI TestClient coverage, GitHub Actions CI, Docker deployment, Railway backend hosting, Vercel frontend hosting, and human-readable error fallbacks.

## 1:30-1:50 Career Value

This project is designed to support an AI application developer resume. It shows LLM integration, prompt engineering, RAG quality evaluation, agent tool routing, backend API design, auth, deployment, and observability.

## 1:50-2:00 Close

The next commercial direction is an AI career coach for schools and training programs, with class dashboards, question banks, PDF reports, and team-level analytics.
