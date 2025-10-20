# agents/embedding_agent.py
import json
import os
import uuid
from typing import Any, Dict, List
from core.logging_utils import get_logger
from core.embedding_model import Embedder
from core.chroma_client import get_collection, get_existing_ids, upsert

DATA_DIR = os.getenv("DATA_DIR", "/data")
PRIMO_JSONL = os.path.join(DATA_DIR, "primo", "records.jsonl")
INDEX_META = os.path.join(DATA_DIR, "primo", "records.index.meta.json")

_log = get_logger(__name__)

# ---------- helpers: safe casting ----------

def _first(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return _first(v[0] if v else "")
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    return str(v)

def _join(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join([_first(x) for x in v if _first(x)])
    return _first(v)

def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for k, v in meta.items():
        if k == "chunk_index":
            try:
                safe[k] = int(v)  # chroma requires primitives
            except Exception:
                safe[k] = 0
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
    _log.info("Upsert start: records=%d batch=%d", len(records), batch)
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
                    _log.debug("Batch flush (partial new): total=%d existing=%d new=%d", len(ids), len(existing), len(keep))
                    emb = embedder.embed([docs[i] for i in keep])
                    added += upsert(
                        coll,
                        [ids[i] for i in keep],
                        [docs[i] for i in keep],
                        [_sanitize_meta(metas[i]) for i in keep],
                        emb,
                    )
            else:
                _log.debug("Batch flush (all new): total=%d", len(ids))
                emb = embedder.embed(docs)
                added += upsert(coll, ids, docs, metas, emb)
            ids, docs, metas = [], [], []

    # flush remainder
    if ids:
        existing = get_existing_ids(coll, ids)
        if existing:
            keep = [i for i, _id in enumerate(ids) if _id not in existing]
            if keep:
                _log.debug("Final flush (partial new): total=%d existing=%d new=%d", len(ids), len(existing), len(keep))
                emb = embedder.embed([docs[i] for i in keep])
                added += upsert(
                    coll,
                    [ids[i] for i in keep],
                    [docs[i] for i in keep],
                    [_sanitize_meta(metas[i]) for i in keep],
                    emb,
                )
        else:
            _log.debug("Final flush (all new): total=%d", len(ids))
            emb = embedder.embed(docs)
            added += upsert(coll, ids, docs, metas, emb)
    stats = {"added": added, "skipped_empty": skipped_empty}
    _log.info("Upsert done: %s", stats)
    return stats

def index_jsonl(jsonl_path: str = PRIMO_JSONL, batch: int = 128) -> Dict[str, int]:
    """
    Read /data/primo/records.jsonl and upsert all chunks.
    Idempotent: skips existing chunk ids (record_id::c{n}).
    """
    _log.info("Index JSONL start: path=%s batch=%d", jsonl_path, batch)
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Export with PNX first.")
    records: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    _log.info("Index JSONL parsed records=%d", len(records))
    res = upsert_records(records, batch=batch)
    _log.info("Index JSONL done: %s", res)
    return res


def index_jsonl_recent(count: int, jsonl_path: str = PRIMO_JSONL, batch: int = 128) -> Dict[str, int]:
    """
    Index only the last `count` records from the JSONL file. Useful right after export
    to avoid rescanning the entire dataset. If `count` <= 0, falls back to full index.
    """
    if count <= 0:
        _log.info("Index recent: count<=0, falling back to full index")
        return index_jsonl(jsonl_path=jsonl_path, batch=batch)

    _log.info("Index JSONL recent start: path=%s last=%d batch=%d", jsonl_path, count, batch)
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Export with PNX first.")

    # Keep only last N lines; for very large files, consider block-based tailing.
    from collections import deque

    q: "deque[str]" = deque(maxlen=count)
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            q.append(line)

    records: List[Dict[str, Any]] = []
    for line in q:
        try:
            records.append(json.loads(line))
        except Exception:
            continue

    _log.info("Index JSONL recent parsed records=%d", len(records))
    res = upsert_records(records, batch=batch)
    _log.info("Index JSONL recent done: %s", res)
    return res


def _read_index_meta(meta_path: str = INDEX_META) -> int:
    """Return last processed byte offset; 0 if none/invalid."""
    try:
        if not os.path.exists(meta_path):
            return 0
        with open(meta_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        off = int(obj.get("offset", 0))
        return max(0, off)
    except Exception:
        return 0


def _write_index_meta(offset: int, meta_path: str = INDEX_META) -> None:
    try:
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"offset": int(max(0, offset))}, f)
    except Exception:
        # Best-effort; do not fail the indexing because meta write failed
        pass


def index_jsonl_incremental(jsonl_path: str = PRIMO_JSONL, batch: int = 128) -> Dict[str, int]:
    """
    Index only the data appended since the previous incremental run, tracked by a
    sidecar meta file storing the last byte offset processed. If the file was
    rotated/truncated, we restart from the beginning.
    """
    _log.info("Index JSONL incremental start: path=%s batch=%d", jsonl_path, batch)
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Export with PNX first.")

    last_off = _read_index_meta()
    size = os.path.getsize(jsonl_path)
    if last_off > size:
        _log.info("Index incremental: file truncated (last_off=%d > size=%d); resetting to 0", last_off, size)
        last_off = 0

    records: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        if last_off > 0:
            f.seek(last_off)
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                continue
        new_off = f.tell()

    if not records:
        _log.info("Index incremental: no new records since offset=%d", last_off)
        return {"added": 0, "skipped_empty": 0}

    _log.info("Index incremental parsed records=%d", len(records))
    res = upsert_records(records, batch=batch)
    _write_index_meta(new_off)
    _log.info("Index JSONL incremental done: %s (new_off=%d)", res, new_off)
    return res
