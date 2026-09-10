import json
import os
from datetime import datetime
from typing import Dict, Any
import logging
from logging.handlers import RotatingFileHandler
from collections import deque

from config import LOG_PATH

os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
logger = logging.getLogger("interview.events")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    logger.addHandler(RotatingFileHandler(LOG_PATH, maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8"))


def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    record = {
        "time": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "payload": payload
    }

    logger.info(json.dumps(record, ensure_ascii=False))


def read_logs(limit: int = 100):
    if not os.path.exists(LOG_PATH):
        return []

    rows = deque(maxlen=limit)

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return list(rows)
