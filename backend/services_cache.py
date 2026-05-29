import hashlib
import json
import os
from typing import Optional, Any

CACHE_PATH = "./storage/cache.json"

os.makedirs("./storage", exist_ok=True)


def _load_cache() -> dict:
    if not os.path.exists(CACHE_PATH):
        return {}

    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def make_key(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def get_cache(key: str) -> Optional[Any]:
    cache = _load_cache()
    return cache.get(key)


def set_cache(key: str, value: Any) -> None:
    cache = _load_cache()
    cache[key] = value
    _save_cache(cache)
