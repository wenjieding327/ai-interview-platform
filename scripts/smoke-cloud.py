"""Explicit live smoke test. Creates one synthetic account, never logs its token."""
import argparse
import json
import secrets
import uuid
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", required=True)
    parser.add_argument("--proxy")
    parser.add_argument("--state", type=Path, required=True, help="Private local file for synthetic credentials")
    parser.add_argument("--resume", action="store_true", help="Verify persistence after restart")
    args = parser.parse_args()
    with httpx.Client(base_url=args.api.rstrip("/"), proxy=args.proxy, timeout=90) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        print("Health:", request("GET", "/health"), flush=True)
        if args.resume:
            account = json.loads(args.state.read_text(encoding="utf-8"))
        else:
            account = {"email": f"smoke+{uuid.uuid4().hex}@example.com", "password": secrets.token_urlsafe(24)}
            request("POST", "/auth/register", json=account)
        token = request("POST", "/auth/login", json={key: account[key] for key in ("email", "password")})["access_token"]
        client.headers["Authorization"] = "Bearer " + token
        if args.resume:
            session = request("GET", f"/interview/session/{account['session_id']}")
            assert len(session["turns"]) == account["turn_count"]
            assert session["status"] == "finished"
            print("PASS: account and finished session survived redeployment", flush=True)
            return
        start = request("POST", "/interview/start", json={"target_role": "RAG工程师"})
        print("Start:", {key: start.get(key) for key in ("session_id", "warning", "max_turns")}, flush=True)
        sid = start["session_id"]
        payload = {"session_id": sid, "answer": "我会根据文档结构切分数据，并通过向量召回、关键词检索和重排来优化RAG效果。",
                   "expected_turn": 0, "request_id": uuid.uuid4().hex}
        first = request("POST", "/interview/session_step", json=payload)
        replay = request("POST", "/interview/session_step", json=payload)
        assert first["turn_count"] == replay["turn_count"] == 1
        print("First review:", {"score": json.loads(first["evaluation"])["score"], "warning": first.get("warning")}, flush=True)
        second = request("POST", "/interview/session_step", json={"session_id": sid, "answer": "不知道", "expected_turn": 1})
        assert json.loads(second["evaluation"])["score"] == 0
        final = request("POST", f"/interview/session/{sid}/finish")
        assert final["turn_count"] == 2
        assert final["status"] == "finished"
        assert request("GET", f"/interview/session/{sid}")["status"] == "finished"
        rag = request("POST", "/ask", json={"question": "什么是RAG？"})
        assert rag["answer"]
        evaluation = request("GET", "/eval/retrieval")
        assert evaluation["total_cases"] >= 30
        print("PASS: auth, saved answers, idempotency, rule-based zero, finish, RAG, evaluation", flush=True)
        print("Summary:", {key: final[key] for key in ("average_score", "scored_turns", "turn_count")}, flush=True)
        account.update(session_id=sid, turn_count=2)
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(json.dumps(account), encoding="utf-8")


if __name__ == "__main__":
    main()
