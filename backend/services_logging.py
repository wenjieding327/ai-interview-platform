import json
import os
from datetime import datetime
from typing import Dict, Any

LOG_PATH = "./storage/app_events.jsonl"
os.makedirs("./storage", exist_ok=True)


def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    record = {
        "time": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "payload": payload
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_logs(limit: int = 100):
    if not os.path.exists(LOG_PATH):
        return []

    rows = []

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows[-limit:]
