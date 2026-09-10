import json
import os
import sys
import tempfile
import time
import subprocess
import pytest
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="ai_interview_tests_"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_ROOT))

os.environ["USE_FAKE_LLM"] = "true"
os.environ["RETRIEVAL_MODE"] = "lexical"
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{TEST_ROOT / 'test.db'}")
os.environ["RUN_DB_MIGRATIONS"] = "true"
os.environ["LOG_PATH"] = str(TEST_ROOT / "app_events.jsonl")
os.environ["DATA_PATH"] = str(BACKEND_ROOT / "data" / "interview_qa.txt")
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from services_interview import is_low_effort_answer, normalize_evaluation  # noqa: E402

client = TestClient(app)


def unique_email() -> str:
    return f"pytest+{time.time_ns()}@example.com"


def register_and_login():
    email = unique_email()
    password = "123456"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password}
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "headers": {"Authorization": f"Bearer {token}"}
    }


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "knowledge_count" in body
    assert "prompt_version" in body


def test_register_login_and_duplicate_register():
    email = unique_email()
    password = "123456"

    response = client.post(
        "/auth/register",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email

    duplicate = client.post(
        "/auth/register",
        json={"email": email, "password": password}
    )
    assert duplicate.status_code == 400

    login = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_invalid_inputs_and_auth_boundaries():
    assert client.post(
        "/auth/register",
        json={"email": "", "password": "123456"}
    ).status_code == 422

    assert client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "123456"}
    ).status_code == 422

    assert client.post(
        "/auth/register",
        json={"email": unique_email(), "password": "x" * 129}
    ).status_code == 422

    assert client.post(
        "/interview/start",
        json={"target_role": "AI应用开发实习生"}
    ).status_code == 401

    assert client.post(
        "/interview/start",
        headers={"Authorization": "Bearer bad-token"},
        json={"target_role": "AI应用开发实习生"}
    ).status_code == 401


def test_interview_session_flow_and_evaluation_json_contract():
    auth = register_and_login()

    start = client.post(
        "/interview/start",
        headers=auth["headers"],
        json={"target_role": "AI应用开发实习生"}
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    assert start.json()["first_question"]

    empty_answer = client.post(
        "/interview/session_step",
        headers=auth["headers"],
        json={"session_id": session_id, "answer": "   "}
    )
    assert empty_answer.status_code == 422

    step = client.post(
        "/interview/session_step",
        headers=auth["headers"],
        json={
            "session_id": session_id,
            "answer": "我会用 FastAPI 暴露接口，用 Chroma 保存向量，并用 Recall@K 评估召回。"
        }
    )
    assert step.status_code == 200
    body = step.json()
    assert body["turn_count"] == 1
    assert body["next_question"]

    evaluation = json.loads(body["evaluation"])
    assert evaluation["score"] == 82
    assert "technical_accuracy" in evaluation
    assert "suggestion" in evaluation


def test_rag_and_retrieval_eval_metrics():
    auth = register_and_login()

    ask = client.post(
        "/ask",
        headers=auth["headers"],
        json={"question": "什么是RAG？"}
    )
    assert ask.status_code == 200
    assert ask.json()["answer"]

    retrieval = client.get("/eval/retrieval", headers=auth["headers"])
    assert retrieval.status_code == 200
    body = retrieval.json()

    assert "hit_rate" in body
    assert "recall_at_1" in body
    assert "recall_at_3" in body
    assert "recall_at_5" in body
    assert "average_similarity" in body
    assert "total_cases" in body
    assert "category_summary" in body
    assert "misses" in body
    assert isinstance(body["details"], list)
    assert body["total_cases"] >= 30


def test_llm_evaluation_normalization_fallback():
    normalized = json.loads(normalize_evaluation("模型临时返回了一段普通中文评价。"))

    assert normalized["score"] is None
    assert "weaknesses" in normalized
    assert normalized["suggestion"] == "模型临时返回了一段普通中文评价。"

    non_numeric = json.loads(normalize_evaluation('{"score":"high","strengths":"结构清楚"}'))
    assert non_numeric["score"] is None
    assert non_numeric["strengths"] == ["结构清楚"]


def test_low_effort_answer_gets_zero_score():
    auth = register_and_login()
    assert is_low_effort_answer("我知道")
    assert is_low_effort_answer("?")

    start = client.post(
        "/interview/start",
        headers=auth["headers"],
        json={"target_role": "AI应用开发实习生"}
    )
    assert start.status_code == 200

    step = client.post(
        "/interview/session_step",
        headers=auth["headers"],
        json={"session_id": start.json()["session_id"], "answer": "我知道"}
    )
    assert step.status_code == 200

    evaluation = json.loads(step.json()["evaluation"])
    assert evaluation["score"] == 0
    assert evaluation["technical_accuracy"] == 0
    assert "刚才的回答信息不足" not in step.json()["next_question"]
    assert "上一题" not in step.json()["next_question"]


def test_agent_tool_router_selects_and_executes_tools():
    auth = register_and_login()

    tools = client.get("/agent/tools", headers=auth["headers"])
    assert tools.status_code == 200
    tool_names = {tool["name"] for tool in tools.json()["tools"]}
    assert {"ask_rag", "retrieval_eval", "weakness_report", "logs"}.issubset(tool_names)

    retrieval = client.post(
        "/agent/tool-call",
        headers=auth["headers"],
        json={"intent": "请检查RAG检索评估，给我Recall@K和Hit Rate"}
    )
    assert retrieval.status_code == 200
    retrieval_body = retrieval.json()
    assert retrieval_body["selected_tool"] == "retrieval_eval"
    assert retrieval_body["result"]["total_cases"] >= 30

    rag = client.post(
        "/agent/tool-call",
        headers=auth["headers"],
        json={"intent": "什么是Function Calling？"}
    )
    assert rag.status_code == 200
    rag_body = rag.json()
    assert rag_body["selected_tool"] == "ask_rag"
    assert rag_body["result"]["answer"]

    logs = client.post(
        "/agent/tool-call",
        headers=auth["headers"],
        json={"intent": "Railway后端报错了，帮我看日志"}
    )
    assert logs.status_code == 403


def test_fresh_container_migrations_and_restart(tmp_path):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'fresh' / 'storage' / 'app.db'}"}
    for _ in range(2):
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                                cwd=BACKEND_ROOT, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    assert (tmp_path / "fresh" / "storage" / "app.db").is_file()


def test_idempotent_answers_auto_finish_and_user_isolation():
    auth = register_and_login()
    other = register_and_login()
    start = client.post("/interview/start", headers=auth["headers"], json={"target_role": "RAG工程师"}).json()
    sid = start["session_id"]
    questions = [start["first_question"]]
    assert client.get(f"/interview/session/{sid}", headers=other["headers"]).status_code == 404
    for i in range(start["max_turns"]):
        payload = {"session_id": sid, "answer": "不知道", "request_id": f"round-{i}", "expected_turn": i}
        response = client.post("/interview/session_step", headers=auth["headers"], json=payload)
        assert response.status_code == 200
        body = response.json()
        assert json.loads(body["evaluation"])["score"] == 0
        replay = client.post("/interview/session_step", headers=auth["headers"], json=payload)
        assert replay.status_code == 200
        assert replay.json()["turn_count"] == i + 1
        if body["next_question"]:
            assert body["next_question"] not in questions
            questions.append(body["next_question"])
    assert body["status"] == "finished"
    assert body["summary"]["average_score"] == 0
    assert body["next_question"] == ""
    finish = client.post(f"/interview/session/{sid}/finish", headers=auth["headers"])
    assert finish.json()["average_score"] == 0
    assert client.post("/interview/session_step", headers=auth["headers"],
                       json={"session_id": sid, "answer": "再答一次"}).status_code == 409
    memory = client.get(f"/interview/session/{sid}", headers=auth["headers"]).json()
    assert len(memory["turns"]) == start["max_turns"]
    assert client.get("/interview/sessions", headers=other["headers"]).json()["sessions"] == []


def test_upstream_failure_does_not_consume_answer(monkeypatch):
    import main
    from fastapi import HTTPException
    auth = register_and_login()
    sid = client.post("/interview/start", headers=auth["headers"], json={"target_role": "工程师"}).json()["session_id"]
    def fail(**kwargs):
        raise HTTPException(status_code=503, detail="AI unavailable")
    monkeypatch.setattr(main, "run_interview_step", fail)
    response = client.post("/interview/session_step", headers=auth["headers"],
                           json={"session_id": sid, "answer": "一个尚未提交成功的回答"})
    assert response.status_code == 503
    assert client.get(f"/interview/session/{sid}", headers=auth["headers"]).json()["turns"] == []


@pytest.mark.parametrize("value", ["NaN", "Infinity", "not-a-number", None])
def test_invalid_scores_excluded_from_average(value):
    from services_interview import summarize_turns
    summary = summarize_turns([{"evaluation": {"score": value}}, {"evaluation": {"score": 20}}])
    assert summary["average_score"] == 20
    assert summary["scored_turns"] == 1


def test_private_knowledge_and_admin_logs(monkeypatch):
    import main
    from services_rag import retrieve_context
    from jose import jwt
    auth = register_and_login()
    other = register_and_login()
    marker = f"privateproject{time.time_ns()}"
    uploaded = client.post("/knowledge/upload", headers=auth["headers"],
                           files={"file": ("private.txt", marker.encode(), "text/plain")})
    assert uploaded.status_code == 200
    owner = int(jwt.get_unverified_claims(auth["headers"]["Authorization"].split()[1])["sub"])
    stranger = int(jwt.get_unverified_claims(other["headers"]["Authorization"].split()[1])["sub"])
    assert marker in retrieve_context(marker, user_id=owner)["context"]
    assert marker not in retrieve_context(marker, user_id=stranger)["context"]
    assert client.get("/admin/logs", headers=auth["headers"]).status_code == 403
    monkeypatch.setattr(main, "ADMIN_EMAILS", {auth["email"]})
    assert client.get("/admin/logs", headers=auth["headers"]).status_code == 200
    assert client.post("/knowledge/upload", headers=auth["headers"],
                       files={"file": ("large.txt", b"x" * (512 * 1024 + 1))}).status_code == 413


def test_stale_turn_and_malformed_jwt_subject():
    from jose import jwt
    auth = register_and_login()
    sid = client.post("/interview/start", headers=auth["headers"], json={"target_role": "工程师"}).json()["session_id"]
    assert client.post("/interview/session_step", headers=auth["headers"],
                       json={"session_id": sid, "answer": "不知道", "expected_turn": 2}).status_code == 409
    token = jwt.encode({"sub": "not-an-int"}, "test-secret", algorithm="HS256")
    assert client.get("/interview/sessions", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_model_outage_is_explicit_practice_not_fake_scoring(monkeypatch):
    import services_interview
    from fastapi import HTTPException
    def unavailable(**kwargs):
        raise HTTPException(status_code=503, detail="AI unavailable")
    monkeypatch.setattr(services_interview, "call_llm", unavailable)
    auth = register_and_login()
    start = client.post("/interview/start", headers=auth["headers"], json={"target_role": "RAG工程师"}).json()
    assert start["warning"] == "practice_mode"
    step = client.post("/interview/session_step", headers=auth["headers"], json={
        "session_id": start["session_id"], "answer": "我会通过多路召回、重排以及评测集来优化知识库的检索质量。"
    }).json()
    assert json.loads(step["evaluation"])["score"] is None
    assert step["warning"] == "practice_mode"
    finish = client.post(f"/interview/session/{start['session_id']}/finish", headers=auth["headers"]).json()
    assert finish["average_score"] is None
    assert finish["scored_turns"] == 0
    assert "暂无可用评分" in finish["summary"]


def test_concurrent_round_writes_do_not_overwrite_history(monkeypatch):
    import main
    import threading
    from concurrent.futures import ThreadPoolExecutor
    auth = register_and_login()
    start = client.post("/interview/start", headers=auth["headers"], json={"target_role": "工程师"}).json()
    gate = threading.Barrier(2)
    original = main.run_interview_step
    def synchronized(**kwargs):
        gate.wait(timeout=10)
        return original(**kwargs)
    monkeypatch.setattr(main, "run_interview_step", synchronized)
    def submit(i):
        return client.post("/interview/session_step", headers=auth["headers"], json={
            "session_id": start["session_id"], "answer": "不知道", "expected_turn": 0, "request_id": f"concurrent-{i}"
        }).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(results) == [200, 409]
    memory = client.get(f"/interview/session/{start['session_id']}", headers=auth["headers"]).json()
    assert len(memory["turns"]) == 1
