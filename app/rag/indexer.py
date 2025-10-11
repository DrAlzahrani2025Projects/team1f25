# app/rag/indexer.py
from __future__ import annotations
import json, os, uuid
from typing import Dict, List, Any, Iterable
import chromadb

from app.rag.embedding import Embedder
from app.rag.chunk import split_text

DATA_DIR = os.getenv("DATA_DIR", "/data")
PRIMO_JSONL = os.path.join(DATA_DIR, "primo", "records.jsonl")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "csusb_primo")

# -----------------------
# Helpers (sanitizers)
# -----------------------
def _first_str(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, list): return _first_str(v[0] if v else "")
    if isinstance(v, (str, int, float, bool)): return str(v)
    return str(v)

def _join_str_list(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, list): return ", ".join([_first_str(x) for x in v if _first_str(x)])
    return _first_str(v)

def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for k, v in meta.items():
        if k == "chunk_index":
            try: safe[k] = int(v)
            except Exception: safe[k] = 0
            continue
        if k == "creators":
            safe[k] = _join_str_list(v)
        else:
            safe[k] = _first_str(v)
    return safe

# -----------------------
# Text extraction from PNX
# -----------------------
def _record_to_text(obj: Dict) -> str:
    pnx = obj.get("pnx") or {}
    disp = pnx.get("display") or {}
    add  = pnx.get("addata") or {}
    search = pnx.get("search") or {}
    sort = pnx.get("sort") or {}

    title = _first_str(disp.get("title"))
    creators = _join_str_list(disp.get("creator"))
    year = _first_str(sort.get("creationdate"))
    desc = _first_str(disp.get("description"))
    abst = _first_str(add.get("abstract"))
    subj = _join_str_list(search.get("subject"))

    parts = [title, creators, year, desc, abst, subj]
    return "\n".join([p for p in parts if p]).strip()

def _brief_meta(obj: Dict) -> Dict[str, Any]:
    brief = obj.get("brief") or {}
    links = obj.get("links") or obj.get("link") or {}
    permalink = links.get("record") if isinstance(links, dict) else ""
    return {
        "record_id": brief.get("record_id") or obj.get("id") or str(uuid.uuid4()),
        "title": brief.get("title") or "",
        "permalink": permalink,
        "creators": brief.get("creators") or [],
        "date": brief.get("creation_date") or "",
        "rtype": brief.get("resource_type") or "",
        "context": brief.get("context") or "",
        "source": brief.get("source") or "",
    }

# -----------------------
# Chroma helpers
# -----------------------
def _client_and_coll():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = client.get_or_create_collection(COLLECTION)
    return client, coll

def _batched(iterable: List[Any], n: int) -> Iterable[List[Any]]:
    for i in range(0, len(iterable), n):
        yield iterable[i:i+n]

def _get_existing_ids(coll, ids: List[str]) -> set:
    # Chroma returns subset for ids that exist
    exist = set()
    for batch in _batched(ids, 200):
        res = coll.get(ids=batch)
        for iid in (res.get("ids") or []):
            exist.add(iid)
    return exist

def _safe_upsert(coll, ids: List[str], docs: List[str], metas: List[Dict[str, Any]], embs: List[List[float]]) -> int:
    # Prefer native upsert if available
    if hasattr(coll, "upsert"):
        coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        return len(ids)
    # Fallback: add only missing ids
    try:
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        return len(ids)
    except Exception:
        existing = _get_existing_ids(coll, ids)
        if existing:
            new_idx = [i for i, _id in enumerate(ids) if _id not in existing]
            if new_idx:
                coll.add(
                    ids=[ids[i] for i in new_idx],
                    documents=[docs[i] for i in new_idx],
                    metadatas=[metas[i] for i in new_idx],
                    embeddings=[embs[i] for i in new_idx],
                )
                return len(new_idx)
            return 0
        raise

# -----------------------
# Indexer (incremental)
# -----------------------
def index_jsonl(jsonl_path: str = PRIMO_JSONL, batch: int = 100):
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Run export with PNX first.")

    _, coll = _client_and_coll()
    embedder = Embedder()

    to_ids: List[str] = []
    to_docs: List[str] = []
    to_meta: List[Dict[str, Any]] = []

    added_docs = 0
    skipped_empty = 0
    skipped_existing = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue

            text = _record_to_text(obj)
            if not text:
                skipped_empty += 1
                continue

            base_meta = _brief_meta(obj)
            rid = base_meta["record_id"]

            chunks = split_text(text, chunk_size=900, overlap=150)
            if not chunks:
                skipped_empty += 1
                continue

            for idx, ch in enumerate(chunks):
                to_ids.append(f"{rid}::c{idx}")
                to_docs.append(ch)
                to_meta.append(_sanitize_meta({**base_meta, "chunk_index": idx}))

            # flush by batch
            if len(to_ids) >= batch:
                # incremental: skip already present IDs to avoid re-embedding
                existing = _get_existing_ids(coll, to_ids)
                if existing:
                    new_idx = [i for i, _id in enumerate(to_ids) if _id not in existing]
                    if not new_idx:
                        skipped_existing += len(to_ids)
                        to_ids, to_docs, to_meta = [], [], []
                        continue
                    ids = [to_ids[i] for i in new_idx]
                    docs = [to_docs[i] for i in new_idx]
                    metas = [to_meta[i] for i in new_idx]
                    embs = embedder.embed(docs)
                    added_docs += _safe_upsert(coll, ids, docs, metas, embs)
                    skipped_existing += (len(to_ids) - len(ids))
                else:
                    embs = embedder.embed(to_docs)
                    added_docs += _safe_upsert(coll, to_ids, to_docs, to_meta, embs)
                to_ids, to_docs, to_meta = [], [], []

    # Flush remainder
    if to_ids:
        existing = _get_existing_ids(coll, to_ids)
        if existing:
            new_idx = [i for i, _id in enumerate(to_ids) if _id not in existing]
            if new_idx:
                ids = [to_ids[i] for i in new_idx]
                docs = [to_docs[i] for i in new_idx]
                metas = [to_meta[i] for i in new_idx]
                embs = embedder.embed(docs)
                added_docs += _safe_upsert(coll, ids, docs, metas, embs)
                skipped_existing += (len(to_ids) - len(ids))
        else:
            embs = embedder.embed(to_docs)
            added_docs += _safe_upsert(coll, to_ids, to_docs, to_meta, embs)

    return {
        "ok": True,
        "collection": COLLECTION,
        "path": CHROMA_DIR,
        "added": added_docs,
        "skipped_empty": skipped_empty,
        "skipped_existing": skipped_existing,
    }
