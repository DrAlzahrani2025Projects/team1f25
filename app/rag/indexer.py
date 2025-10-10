# app/rag/indexer.py
import json, os, uuid
from typing import Dict, List, Any
import chromadb
from app.rag.embedding import Embedder
from app.rag.chunk import split_text

DATA_DIR = os.getenv("DATA_DIR", "/data")
PRIMO_JSONL = os.path.join(DATA_DIR, "primo", "records.jsonl")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "csusb_primo")

# -----------------------
# Helpers
# -----------------------

def _first_str(v: Any) -> str:
    """Return a single string from possibly list/None/primitive."""
    if v is None:
        return ""
    if isinstance(v, list):
        return _first_str(v[0] if v else "")
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    return str(v)

def _join_str_list(v: Any) -> str:
    """Join a list of strings as comma-separated; otherwise return stringified value."""
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join([_first_str(x) for x in v if _first_str(x)])
    return _first_str(v)

def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chroma metadata must be primitives (str/int/float/bool) — no None, no lists.
    Convert everything except 'chunk_index' to string; ensure chunk_index is int.
    """
    safe: Dict[str, Any] = {}
    for k, v in meta.items():
        if k == "chunk_index":
            # default to 0 if missing/invalid
            try:
                safe[k] = int(v)
            except Exception:
                safe[k] = 0
            continue
        # everything else -> string (no None/lists)
        if k == "creators":
            safe[k] = _join_str_list(v)
        else:
            safe[k] = _first_str(v)
    return safe

# -----------------------
# Text extraction from PNX
# -----------------------

def _record_to_text(obj: Dict) -> str:
    """
    Build an indexable text blob from PNX fields.
    We read from obj['pnx'] if present; otherwise fallback to raw/link fields.
    """
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
    text = "\n".join([p for p in parts if p]).strip()
    return text

def _brief_meta(obj: Dict) -> Dict[str, Any]:
    """Pull brief metadata with simple defaults."""
    brief = obj.get("brief") or {}
    # permalink may be under 'links' or 'link' and might be list
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
# Indexer
# -----------------------

def index_jsonl(jsonl_path: str = PRIMO_JSONL, chroma_dir: str = CHROMA_DIR, batch: int = 100):
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Missing {jsonl_path}. Run Sprint-2 ingest/export with PNX first.")

    client = chromadb.PersistentClient(path=chroma_dir)
    coll = client.get_or_create_collection(COLLECTION)

    embedder = Embedder()

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict[str, Any]] = []

    added_docs = 0
    skipped_empty = 0

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
                ids.append(f"{rid}::c{idx}")
                docs.append(ch)
                meta = {**base_meta, "chunk_index": idx}
                metas.append(_sanitize_meta(meta))

            # Batch write for speed and lower memory
            if len(ids) >= batch:
                embs = embedder.embed(docs)
                coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
                added_docs += len(ids)
                ids, docs, metas = [], [], []

    # Flush remainder
    if ids:
        embs = embedder.embed(docs)
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        added_docs += len(ids)

    return {
        "ok": True,
        "collection": COLLECTION,
        "path": chroma_dir,
        "added": added_docs,
        "skipped_empty": skipped_empty,
    }
