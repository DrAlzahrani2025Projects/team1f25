# core/chroma_client.py
import os
import chromadb
from typing import List, Dict, Any, Iterable

DATA_DIR = os.getenv("DATA_DIR", "/data")
if os.name == "posix" and (":" in DATA_DIR or DATA_DIR.startswith(("C:\\", "C:/"))):
    DATA_DIR = "/data"
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "csusb_primo")

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(COLLECTION)

def _batched(xs: List, n: int) -> Iterable[List]:
    for i in range(0, len(xs), n):
        yield xs[i:i+n]

def get_existing_ids(coll, ids: List[str]) -> set:
    exists = set()
    for batch in _batched(ids, 200):
        res = coll.get(ids=batch)
        for iid in res.get("ids", []) or []:
            exists.add(iid)
    return exists

def upsert(coll, ids: List[str], docs: List[str], metas: List[Dict[str, Any]], embs: List[List[float]]) -> int:
    # Prefer native upsert if available
    if hasattr(coll, "upsert"):
        coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        return len(ids)
    # Fallback: add only non-existing
    try:
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        return len(ids)
    except Exception:
        existing = get_existing_ids(coll, ids)
        if existing:
            idx = [i for i, _id in enumerate(ids) if _id not in existing]
            if not idx:
                return 0
            coll.add(
                ids=[ids[i] for i in idx],
                documents=[docs[i] for i in idx],
                metadatas=[metas[i] for i in idx],
                embeddings=[embs[i] for i in idx],
            )
            return len(idx)
        raise
