# app/ingest/primo_store.py
import json, os
from typing import Iterable, Set
from .primo_schema import PrimoFull

DATA_DIR = os.environ.get("DATA_DIR", "/data")
PRIMO_DIR = os.path.join(DATA_DIR, "primo")
RECORDS_PATH = os.path.join(PRIMO_DIR, "records.jsonl")
os.makedirs(PRIMO_DIR, exist_ok=True)

def _existing_ids() -> Set[str]:
    ids: Set[str] = set()
    if not os.path.exists(RECORDS_PATH):
        return ids
    with open(RECORDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                rid = obj.get("brief", {}).get("record_id")
                if rid: ids.add(rid)
            except Exception:
                continue
    return ids

def append_records(records: Iterable[PrimoFull], dedupe: bool = True) -> int:
    existed = _existing_ids() if dedupe else set()
    wrote = 0
    with open(RECORDS_PATH, "a", encoding="utf-8") as f:
        for rec in records:
            rid = rec.brief.record_id
            if dedupe and rid in existed:
                continue
            f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")
            wrote += 1
    return wrote
