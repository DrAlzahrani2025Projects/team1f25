# core/chroma_client.py
import os
import chromadb
from typing import List, Dict, Any, Iterable, Optional
from core.logging_utils import get_logger

DATA_DIR = os.getenv("DATA_DIR", "/data")
if os.name == "posix" and (":" in DATA_DIR or DATA_DIR.startswith(("C:\\", "C:/"))):
    DATA_DIR = "/data"
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "csusb_primo")

_log = get_logger(__name__)

def get_collection():
    _log.info("Chroma: open collection name=%s path=%s", COLLECTION, CHROMA_DIR)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(COLLECTION)


def _batched(xs: List[Any], n: int) -> Iterable[List[Any]]:
    for i in range(0, len(xs), n):
        yield xs[i : i + n]

def get_existing_ids(coll, ids: List[str]) -> set:
    exists = set()
    for batch in _batched(ids, 200):
        res = coll.get(ids=batch)
        for iid in (res.get("ids") or []):
            exists.add(iid)
    return exists


def upsert(
    coll,
    ids: List[str],
    docs: List[str],
    metas: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> int:
    if hasattr(coll, "upsert"):
        _log.debug("Chroma upsert fast-path: n=%d", len(ids))
        coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
        return len(ids)

    # Fallback path (older clients): try add, then filter duplicates if needed
    try:
        _log.debug("Chroma add: n=%d", len(ids))
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
        return len(ids)
    except Exception:
        existing = get_existing_ids(coll, ids)
        keep_idx = [i for i, _id in enumerate(ids) if _id not in existing]
        if not keep_idx:
            return 0
        _log.debug("Chroma add filtered: total=%d new=%d", len(ids), len(keep_idx))
        coll.add(
            ids=[ids[i] for i in keep_idx],
            documents=[docs[i] for i in keep_idx],
            metadatas=[metas[i] for i in keep_idx],
            embeddings=[embeddings[i] for i in keep_idx],
        )
        return len(keep_idx)


def query(
    coll,
    q_emb: List[float],
    top_k: int = 6,
    *,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    include_vectors: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run a nearest-neighbor query against the collection using a single embedding.

    Returns a list of hits: {
        "id": str,
        "text": str,
        "meta": Dict[str, Any],
        "score": float | None,     # distance if available
        # "embedding": List[float]  # present only if include_vectors=True
    }
    """
    include = ["documents", "metadatas", "distances"]
    if include_vectors:
        include.append("embeddings")

    _log.debug("Chroma query: top_k=%d include_vectors=%s", int(top_k), include_vectors)
    res = coll.query(
        query_embeddings=[q_emb],
        n_results=int(top_k),
        where=where,
        where_document=where_document,
        include=include,
    )

    ids = (res.get("ids") or [[]])[0] or []
    docs = (res.get("documents") or [[]])[0] or []
    metas = (res.get("metadatas") or [[]])[0] or []
    dists = (res.get("distances") or [[]])[0] if "distances" in res else []
    embs = (res.get("embeddings") or [[]])[0] if "embeddings" in res else []

    hits: List[Dict[str, Any]] = []
    for i, _id in enumerate(ids):
        hit = {
            "id": _id,
            "text": docs[i] if i < len(docs) else "",
            "meta": metas[i] if i < len(metas) else {},
            "score": float(dists[i]) if i < len(dists) and dists[i] is not None else None,
        }
        if include_vectors:
            hit["embedding"] = embs[i] if i < len(embs) else None
        hits.append(hit)

    _log.debug("Chroma query: returned=%d", len(hits))
    return hits
