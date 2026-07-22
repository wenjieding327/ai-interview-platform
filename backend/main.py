from datetime import datetime
import time
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config

import json
from services_logging import read_logs, log_event

from database import Base, engine, get_db
from config import RUN_DB_MIGRATIONS
from models import User, InterviewHistory, InterviewSession
from schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    AskRequest,
    StartInterviewRequest,
    InterviewStepRequest,
    SessionStepRequest,
    AgentToolRequest
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from services_rag import (
    init_knowledge_base,
    add_knowledge_text,
    collection,
    evaluate_retrieval
)
from prompt_registry import PROMPT_VERSION, PROMPTS
from services_interview import (
    answer_with_rag,
    generate_first_question,
    run_interview_step,
    generate_weakness_report
)
from services_agent import available_agent_tools, select_agent_tool

def run_db_migrations_if_enabled():
    if not RUN_DB_MIGRATIONS:
        return

    alembic_ini = Path(__file__).with_name("alembic.ini")
    if not alembic_ini.exists():
        log_event("db_migration_skipped", {"reason": "alembic.ini not found"})
        return

    alembic_config = Config(str(alembic_ini))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).with_name("alembic"))
    )
    command.upgrade(alembic_config, "head")
    log_event("db_migration_completed", {"revision": "head"})


run_db_migrations_if_enabled()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Interview Training Platform V2",
    description="AI Application Project: Auth + RAG + Stateful Agent + Scoring + History",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_event("api_request", {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        })
        return response

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_event("api_request_failed", {
            "method": request.method,
            "path": request.url.path,
            "duration_ms": duration_ms,
            "error_type": type(exc).__name__,
            "error": str(exc)
        })
        raise


def parse_turns(turns_json: str):
    try:
        return json.loads(turns_json or "[]")
    except json.JSONDecodeError:
        return []


def dump_turns(turns):
    return json.dumps(turns, ensure_ascii=False)


def load_retrieval_eval_cases():
    path = os.path.join(os.path.dirname(__file__), "data", "eval_cases.json")

    try:
        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        if isinstance(cases, list) and cases:
            return cases

    except Exception as exc:
        log_event("retrieval_eval_cases_load_failed", {"error": str(exc)})

    return [
        {
            "query": "什么是RAG",
            "expected_keyword": "检索增强生成"
        },
        {
            "query": "为什么需要向量数据库",
            "expected_keyword": "语义相似度"
        },
        {
            "query": "Agent有什么能力",
            "expected_keyword": "工具调用"
        }
    ]


def build_weakness_report(db: Session, current_user: User):
    rows = (
        db.query(InterviewHistory)
        .filter(InterviewHistory.user_id == current_user.id)
        .order_by(InterviewHistory.created_at.desc())
        .limit(10)
        .all()
    )

    if not rows:
        return {
            "message": "No history yet"
        }

    records = []

    for row in rows:
        records.append({
            "target_role": row.target_role,
            "question": row.question,
            "answer": row.answer,
            "evaluation": row.evaluation,
            "followup_question": row.followup_question
        })

    history_text = json.dumps(records, ensure_ascii=False, indent=2)
    report = generate_weakness_report(history_text)

    return {
        "report": report,
        "source_turns": len(records)
    }


@app.get("/")
def home():
    return {
        "message": "AI Interview Training Platform V2 is running",
        "docs": "/docs",
        "core_features": [
            "JWT auth",
            "RAG knowledge retrieval",
            "stateful interview session",
            "LLM scoring",
            "Agent follow-up",
            "history and weakness report"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "knowledge_count": collection.count(),
        "prompt_version": PROMPT_VERSION
    }


@app.post("/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existed = db.query(User).filter(User.email == data.email).first()

    if existed:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email
    }


@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)

    return TokenResponse(access_token=token)


@app.post("/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    raw = await file.read()

    try:
        text = raw.decode("utf-8")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Only UTF-8 txt files are supported")

    lines = text.splitlines()
    added = 0

    for line in lines:
        line = line.strip()

        if not line:
            continue

        add_knowledge_text(line)
        added += 1

    return {
        "filename": file.filename,
        "added_count": added,
        "total_knowledge_count": collection.count()
    }


@app.post("/ask")
def ask(
    data: AskRequest,
    current_user: User = Depends(get_current_user)
):
    return answer_with_rag(data.question)


@app.post("/interview/start")
def start_interview(
    data: StartInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建一场有状态的面试会话。

    数据流：
    用户选择岗位
    ↓
    RAG检索岗位相关知识
    ↓
    LLM生成第一题
    ↓
    创建 InterviewSession
    ↓
    返回 session_id + first_question
    """
    result = generate_first_question(data.target_role)

    session = InterviewSession(
        user_id=current_user.id,
        target_role=data.target_role,
        status="active",
        current_question=result["first_question"],
        turns_json="[]",
        updated_at=datetime.utcnow()
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "target_role": data.target_role,
        "first_question": result["first_question"],
        "retrieved_context": result["retrieved_context"]
    }


@app.post("/interview/session_step")
def interview_session_step(
    data: SessionStepRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    真正的Agent状态版面试步骤。

    数据流：
    session_id
    ↓
    读取 InterviewSession
    ↓
    得到 current_question + turns历史
    ↓
    LLM评分
    ↓
    LLM基于历史生成追问
    ↓
    更新 turns_json 和 current_question
    ↓
    保存 InterviewHistory
    ↓
    返回 evaluation + next_question
    """
    session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == data.session_id,
            InterviewSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    current_question = session.current_question
    turns = parse_turns(session.turns_json)

    result = run_interview_step(
        target_role=session.target_role,
        question=current_question,
        answer=data.answer,
        turns=turns
    )

    new_turn = {
        "question": current_question,
        "answer": data.answer,
        "evaluation": result["evaluation"],
        "followup_question": result["followup_question"],
        "created_at": datetime.utcnow().isoformat()
    }

    turns.append(new_turn)

    session.turns_json = dump_turns(turns)
    session.current_question = result["followup_question"]
    session.updated_at = datetime.utcnow()

    history = InterviewHistory(
        user_id=current_user.id,
        target_role=session.target_role,
        question=current_question,
        answer=data.answer,
        evaluation=result["evaluation"],
        followup_question=result["followup_question"]
    )

    db.add(history)
    db.commit()
    db.refresh(history)
    db.refresh(session)

    return {
        "session_id": session.id,
        "target_role": session.target_role,
        "answered_question": current_question,
        "answer": data.answer,
        "evaluation": result["evaluation"],
        "next_question": result["followup_question"],
        "turn_count": len(turns)
    }


@app.post("/interview/step")
def interview_step_legacy(
    data: InterviewStepRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    兼容旧版：无session状态的一步评分+追问。
    真实面试请优先用 /interview/start + /interview/session_step。
    """
    result = run_interview_step(
        target_role=data.target_role,
        question=data.question,
        answer=data.answer,
        turns=[]
    )

    history = InterviewHistory(
        user_id=current_user.id,
        target_role=data.target_role,
        question=data.question,
        answer=data.answer,
        evaluation=result["evaluation"],
        followup_question=result["followup_question"]
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    result["history_id"] = history.id

    return result


@app.get("/interview/session/{session_id}")
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.id,
        "target_role": session.target_role,
        "status": session.status,
        "current_question": session.current_question,
        "turns": parse_turns(session.turns_json),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }


@app.post("/interview/session/{session_id}/finish")
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "finished"
    session.updated_at = datetime.utcnow()

    db.commit()

    return {
        "session_id": session.id,
        "status": session.status
    }


@app.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = (
        db.query(InterviewHistory)
        .filter(InterviewHistory.user_id == current_user.id)
        .order_by(InterviewHistory.created_at.desc())
        .limit(30)
        .all()
    )

    history = []

    for row in rows:
        history.append({
            "id": row.id,
            "target_role": row.target_role,
            "question": row.question,
            "answer": row.answer,
            "evaluation": row.evaluation,
            "followup_question": row.followup_question,
            "created_at": row.created_at.isoformat()
        })

    return {
        "count": len(history),
        "history": history
    }


@app.get("/report/weakness")
def weakness_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return build_weakness_report(db, current_user)


@app.get("/prompts")
def get_prompts(current_user: User = Depends(get_current_user)):
    """
    查看当前Prompt版本。
    这用于展示Prompt版本管理思想。
    """
    return {
        "prompt_version": PROMPT_VERSION,
        "prompts": PROMPTS
    }


@app.get("/eval/retrieval")
def eval_retrieval(current_user: User = Depends(get_current_user)):
    """
    检索评测接口。

    这不是为了给用户用，而是为了给面试官看：
    项目不是只调API，而是开始有AI系统评测意识。
    """
    return evaluate_retrieval(load_retrieval_eval_cases())



@app.get("/admin/logs")
def admin_logs(current_user: User = Depends(get_current_user)):
    return {
        "logs": read_logs(limit=100)
    }


@app.get("/agent/tools")
def agent_tools(current_user: User = Depends(get_current_user)):
    return {
        "tools": available_agent_tools()
    }


@app.post("/agent/tool-call")
def agent_tool_call(
    data: AgentToolRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lightweight Tool Calling demo.

    This keeps the project dependency-light and testable while showing the same
    production idea used by Agent frameworks: infer intent, choose a tool,
    execute it, and return a trace.
    """
    decision = select_agent_tool(data.intent)
    selected_tool = decision["selected_tool"]
    query = data.question or data.intent

    if selected_tool == "ask_rag":
        result = answer_with_rag(query)

    elif selected_tool == "retrieval_eval":
        result = evaluate_retrieval(load_retrieval_eval_cases())

    elif selected_tool == "weakness_report":
        result = build_weakness_report(db, current_user)

    elif selected_tool == "logs":
        result = {
            "logs": read_logs(limit=20)
        }

    else:
        raise HTTPException(status_code=400, detail="Unsupported agent tool")

    log_event("agent_tool_executed", {
        "selected_tool": selected_tool,
        "intent_preview": data.intent[:200]
    })

    return {
        "intent": data.intent,
        "selected_tool": selected_tool,
        "reason": decision["reason"],
        "tool_scores": decision["scores"],
        "tool_trace": {
            "available_tools": decision["available_tools"],
            "executed_tool": selected_tool
        },
        "result": result
    }


@app.get("/interview/session/{session_id}/summary")
def session_summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turns = parse_turns(session.turns_json)
    turns_text = json.dumps(turns, ensure_ascii=False, indent=2)

    report = generate_weakness_report(turns_text)

    return {
        "session_id": session.id,
        "target_role": session.target_role,
        "turn_count": len(turns),
        "summary": report
    }
