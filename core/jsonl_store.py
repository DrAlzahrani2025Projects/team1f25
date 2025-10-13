# core/jsonl_store.py
from __future__ import annotations
import os, json
from typing import List, Dict, Any, Set

DATA_DIR = os.getenv("DATA_DIR", "/data")
if os.name == "posix" and (":" in DATA_DIR or DATA_DIR.startswith(("C:\\", "C:/"))):
    DATA_DIR = "/data"
PRIMO_JSONL = os.path.join(DATA_DIR, "primo", "records.jsonl")

def _ensure_dirs():
    d = os.path.dirname(PRIMO_JSONL)
    os.makedirs(d, exist_ok=True)

def _existing_ids(path: str) -> Set[str]:
    ids: Set[str] = set()
    if not os.path.exists(path):
        return ids
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                o = json.loads(line)
                rid = (o.get("brief") or {}).get("record_id") or o.get("id")
                if rid:
                    ids.add(str(rid))
            except Exception:
                continue
    return ids

def append_records(docs: List[Dict[str, Any]]) -> int:
    _ensure_dirs()
    seen = _existing_ids(PRIMO_JSONL)
    wrote = 0
    with open(PRIMO_JSONL, "a", encoding="utf-8") as out:
        for obj in docs:
            rid = (obj.get("brief") or {}).get("record_id") or obj.get("id")
            if not rid or str(rid) in seen:
                continue
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            seen.add(str(rid))
            wrote += 1
    return wrote
