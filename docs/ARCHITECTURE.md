# Architecture

## System Overview

```mermaid
flowchart LR
    User["Candidate / Recruiter"] --> Frontend["Static Frontend<br/>HTML CSS JS on Vercel"]
    Frontend --> API["FastAPI Backend<br/>Railway"]
    API --> Auth["JWT Auth<br/>User Isolation"]
    API --> Data["SQLAlchemy Data Layer<br/>SQLite local / PostgreSQL prod"]
    API --> Interview["Stateful Interview Agent<br/>Session + Turns"]
    API --> RAG["RAG Service<br/>Embedding + Chroma + Rerank"]
    API --> Router["Agent Tool Router"]
    API --> Logs["JSONL Logs<br/>Admin Logs API"]
    Interview --> LLM["DeepSeek / Fake LLM Fallback"]
    RAG --> Knowledge["Knowledge Base<br/>interview_qa.txt"]
    Router --> Ask["Ask RAG"]
    Router --> Eval["Retrieval Eval<br/>Hit Rate + Recall@K"]
    Router --> Report["Weakness Report"]
    Router --> Logs
```

## Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as FastAPI
    participant R as RAG
    participant L as LLM
    participant DB as SQLite / PostgreSQL

    U->>F: Login and choose target role
    F->>B: POST /auth/login
    B->>F: JWT access token
    F->>B: POST /interview/start
    B->>R: Retrieve role-related context
    B->>L: Generate first question
    B->>DB: Save session
    B->>F: first_question + session_id
    U->>F: Submit answer
    F->>B: POST /interview/session_step
    B->>L: Structured evaluation JSON
    B->>DB: Save turn
    B->>F: evaluation + next_question
```

## Why This Is More Than a Chatbot

- It has authenticated, user-scoped sessions.
- It stores interview state and historical turns.
- It measures retrieval quality instead of only claiming to use RAG.
- It includes a deterministic tool router that can be tested without model randomness.
- It has migrations, deployment, logging, tests, E2E coverage, and fallback behavior.
