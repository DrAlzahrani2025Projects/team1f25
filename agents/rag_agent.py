# agents/rag_agent.py


# Define SYSTEM prompt for the AI assistant
#
# Define function rag_answer(question, top_k=6):
#     Create embedding model instance
#     Embed the question to get its vector
#     Get Chroma collection
#     Query the collection with the question vector for top_k results
#
#     For each hit in results:
#         Extract metadata (title, link)
#         Format context line with citation and text
#
#     Join context lines into a single context string
#
#     Create QroqClient instance
#     Build messages list with system and user messages (including context)
#     Call chat method on QroqClient with messages
#     Return dictionary with answer and hits

from typing import Any, Dict, List, Optional
from core.embedding_model import Embedder
from core.chroma_client import get_collection
from core.schemas import QAHit

_embedder: Optional[Embedder] = None

def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()  # uses your existing fastembed model
    return _embedder

def _hits_from_query_results(results: Dict[str, List], top_k: int) -> List[QAHit]:
    """
    Convert Chroma query() results to a list[QAHit].
    results keys: 'ids','documents','metadatas','distances' (per-query lists).
    """
    hits: List[QAHit] = []
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    dists = (results.get("distances") or [[]])[0]

    for i, doc in enumerate(docs):
        meta = (metas[i] if i < len(metas) else {}) or {}
        if i < len(dists) and dists[i] is not None:
            # Convert cosine *distance* to a rough similarity score in [0,1]
            try:
                meta["score"] = round(1 - float(dists[i]) / 2, 4)
            except Exception:
                pass
        hits.append(QAHit(text=doc, meta=meta))
        if len(hits) >= top_k:
            break
    return hits

def _synthesize_answer(question: str, hits: List[QAHit]) -> str:
    """
    Lightweight extractive “answer”: show top snippets + sources.
    """
    if not hits:
        return (
            "I couldn't find relevant passages in your indexed library yet. "
            "Try **feed** first to export results and index them, then ask again."
        )

    bullets = []
    for h in hits[:3]:
        m = h.meta or {}
        title = m.get("title") or "Untitled"
        creators = ", ".join(m.get("creators") or []) if isinstance(m.get("creators"), list) else (m.get("creators") or "")
        year = str(m.get("date") or "").strip()
        pieces = [p for p in [creators, year] if p]
        label = f"**{title}**" + (f" — {', '.join(pieces)}" if pieces else "")
        if m.get("permalink"):
            label = f"[{label}]({m['permalink']})"
        snippet = (h.text or "").strip().replace("\n", " ")
        if len(snippet) > 300:
            snippet = snippet[:297] + "…"
        bullets.append(f"- {snippet}\n  \n  Source: {label}")

    return "Here’s what your indexed library says:\n\n" + "\n".join(bullets)

def answer(question: str, top_k: int = 6) -> Dict[str, Any]:
    """
    Simple RAG over your local Chroma DB (populated by agents/embedding_agent.py).
    Returns: { 'answer': str, 'hits': List[{text, meta}] }
    """
    coll = get_collection()
    embedder = _get_embedder()
    q_emb = embedder.embed([question])[0]
    results = coll.query(query_embeddings=[q_emb], n_results=max(1, top_k))
    hits = _hits_from_query_results(results, top_k)
    return {
        "answer": _synthesize_answer(question, hits),
        "hits": [{"text": h.text, "meta": dict(h.meta or {})} for h in hits],
    }

# Orchestrator expects `rag_answer`; expose a small wrapper.
def rag_answer(question: str, top_k: int = 6) -> Dict[str, Any]:
    return answer(question, top_k=top_k)

