# app/ingest/primo_cache.py
from __future__ import annotations
import json, os, tempfile, shutil
from typing import Optional, Dict

DATA_DIR = os.getenv("DATA_DIR", "/data")
CACHE_ROOT = os.path.join(DATA_DIR, "primo", "cache")

def _safe_name(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in s or "")

def cache_path(record_id: str, context: str) -> str:
    ctx = _safe_name(context or "PC")
    rid = _safe_name(record_id or "unknown")
    d = os.path.join(CACHE_ROOT, ctx)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{rid}.json")

def load_cached(record_id: str, context: str) -> Optional[Dict]:
    try:
        p = cache_path(record_id, context)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_cached(record_id: str, context: str, data: Dict) -> None:
    p = cache_path(record_id, context)
    tmp_fd, tmp_name = tempfile.mkstemp(prefix=".cache_", dir=os.path.dirname(p))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        shutil.move(tmp_name, p)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass
