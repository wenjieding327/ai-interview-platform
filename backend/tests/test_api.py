import json
import os
import sys
import tempfile
import time
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="ai_interview_tests_"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("USE_FAKE_LLM", "true")
os.environ.setdefault("USE_FAKE_EMBEDDINGS", "true")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_ROOT / 'test.db'}")
os.environ.setdefault("CHROMA_PATH", str(TEST_ROOT / "chroma"))
os.environ.setdefault("LOG_PATH", str(TEST_ROOT / "app_events.jsonl"))
os.environ.setdefault("DATA_PATH", str(BACKEND_ROOT / "data" / "interview_qa.txt"))
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

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
    assert isinstance(body["details"], list)


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
