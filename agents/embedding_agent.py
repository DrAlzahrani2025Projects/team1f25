# agents/embedding_agent.py
from __future__ import annotations
import os, json, uuid
from typing import List, Dict, Any, Iterable, Tuple
from core.embedding_model import Embedder
from core.chroma_client import get_collection, get_existing_ids, upsert

DATA_DIR = os.getenv("DATA_DIR", "/data")
PRIMO_JSONL = os.path.join(DATA_DIR, "primo", "records.jsonl")

# ---------- helpers: safe casting ----------

def _first(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, list): return _first(v[0] if v else "")
    if isinstance(v, (str, int, float, bool)): return str(v)
    return str(v)

def _join(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, list): return ", ".join([_first(x) for x in v if _first(x)])
    return _first(v)

def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for k, v in meta.items():
        if k == "chunk_index":
            try: safe[k] = int(v)  # chroma requires primitives
            except Exception: safe[k] = 0
            continue
        if isinstance(v, bool):
            safe[k] = v
        elif isinstance(v, (int, float)):
            safe[k] = v
        elif isinstance(v, dict):
            # best-effort stringification
            safe[k] = {str(kk): _first(vv) for kk, vv in v.items()}
        elif isinstance(v, list):
            safe[k] = _join(v)
        else:
            safe[k] = _first(v)
    return safe

# ---------- text extraction from PNX ----------

def _record_to_text(obj: Dict[str, Any]) -> str:
    pnx = obj.get("pnx") or {}
    disp = pnx.get("display") or {}
    add  = pnx.get("addata") or {}
    search = pnx.get("search") or {}
    sort = pnx.get("sort") or {}

    title = _first(disp.get("title"))
    creators = _join(disp.get("creator"))
    year = _first(sort.get("creationdate"))
    desc = _first(disp.get("description"))
    abst = _first(add.get("abstract"))
    subj = _join(search.get("subject"))

    parts = [title, creators, year, desc, abst, subj]
    text = "\n".join([p for p in parts if p]).strip()
    return text

def _brief_meta(obj: Dict[str, Any]) -> Dict[str, Any]:
    brief = obj.get("brief") or {}
    links = obj.get("links") or obj.get("link") or {}
    permalink = links.get("record") if isinstance(links, dict) else ""
    return {
        "record_id": brief.get("record_id") or obj.get("id") or str(uuid.uuid4()),
        "title": brief.get("title") or "",
        "permalink": permalink or "",
        "creators": brief.get("creators") or [],
        "date": brief.get("creation_date") or "",
        "rtype": brief.get("resource_type") or "",
        "context": brief.get("context") or "",
        "source": brief.get("source") or "",
    }

# ---------- chunking ----------

def _chunks(text: str, size: int = 900, overlap: int = 150) -> List[str]:
    if not text:
        return []
    words = text.split()
    if not words:
        return []
    out: List[str] = []
    i = 0
    step = max(1, size - overlap)
    while i < len(words):
        out.append(" ".join(words[i:i+size]))
        i += step
    return out

# ---------- core API ----------

def upsert_records(records: List[Dict[str, Any]], batch: int = 128) -> Dict[str, int]:
    """
    Upsert a list of full records (with PNX) to Chroma.
    Returns counts of added chunks and skipped empties.
    """
    coll = get_collection()
    embedder = Embedder()

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict[str, Any]] = []

    added, skipped_empty = 0, 0

    for rec in records:
        text = _record_to_text(rec)
        if not text:
            skipped_empty += 1
            continue
        meta_base = _brief_meta(rec)
        rid = meta_base["record_id"]
        for idx, ch in enumerate(_chunks(text)):
            ids.append(f"{rid}::c{idx}")
            docs.append(ch)
            metas.append(_sanitize_meta({**meta_base, "chunk_index": idx}))

        # flush
        if len(ids) >= batch:
            existing = get_existing_ids(coll, ids)
            if existing:
                keep = [i for i, _id in enumerate(ids) if _id not in existing]
                if keep:
                    emb = embedder.embed([docs[i] for i in keep])
                    added += upsert(
                        coll,
                        [ids[i] for i in keep],
                        [docs[i] for i in keep],
                        [_sanitize_meta(metas[i]) for i in keep],
                        emb,
                    )
            else:
                emb = embedder.embed(docs)
                added += upsert(coll, ids, docs, metas, emb)
            ids, docs, metas = [], [], []

    # flush remainder
    if ids:
        existing = get_existing_ids(coll, ids)
        if existing:
            keep = [i for i, _id in enumerate(ids) if _id not in existing]
            if keep:
                emb = embedder.embed([docs[i] for i in keep])
                added += upsert(
                    coll,
                    [ids[i] for i in keep],
                    [docs[i] for i in keep],
                    [_sanitize_meta(metas[i]) for i in keep],
                    emb,
                )
        else:
            emb = embedder.embed(docs)
            added += upsert(coll, ids, docs, metas, emb)

    return {"added": added, "skipped_empty": skipped_empty}

def index_jsonl(jsonl_path: str = PRIMO_JSONL, batch: int = 128) -> Dict[str, int]:
    """
    Read /data/primo/records.jsonl and upsert all chunks.
    Idempotent: skips existing chunk ids (record_id::c{n}).
    """
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Export with PNX first.")
    records: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    return upsert_records(records, batch=batch)

# ---------- tiny CLI ----------

if __name__ == "__main__":
    import argparse, json as _json
    p = argparse.ArgumentParser(description="Week 3 Embedding Agent — index exported JSONL")
    p.add_argument("--file", default=PRIMO_JSONL, help="Path to records.jsonl")
    p.add_argument("--batch", type=int, default=128, help="Batch size")
    args = p.parse_args()
    stats = index_jsonl(args.file, batch=args.batch)
    print(_json.dumps({"ok": True, **stats}, indent=2))
