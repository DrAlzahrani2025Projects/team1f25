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

# agents/rag_agent.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.embedding_model import Embedder
from core.chroma_client import get_collection
from core.schemas import QAHit

# If your project exposes a Qroq client from a different path, adjust this import.
try:
    from core.qroq_client import QroqClient
except Exception:  # pragma: no cover
    QroqClient = None  # type: ignore


# -----------------------------------------------------------------------------
# SYSTEM prompt for the AI assistant (concise, retrieval-aware)
# -----------------------------------------------------------------------------
SYSTEM_PROMPT: str = (
    "You are a helpful research assistant. Answer the user's question using the\n"
    "provided CONTEXT first. Cite the most relevant sources inline as [1], [2],\n"
    "etc., mapping to the citations included in the context block. If the\n"
    "context is missing crucial facts, say so briefly and suggest what would\n"
    "help. Prefer direct, accurate, and concise answers.\n\n"
    "Rules:\n"
    "- Do not fabricate citations.\n"
    "- If multiple sources agree, synthesize. If they disagree, note the split.\n"
    "- Keep the final answer in plain text (no Markdown tables unless asked).\n"
)


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


def _format_context_lines(hits: List[QAHit]) -> Tuple[str, List[str]]:
    """Create a context block with inline bracketed citation indices.
    Returns (context_str, bib) where bib maps [n] -> label string.
    """
    ctx_lines: List[str] = []
    bib: List[str] = []

    for idx, h in enumerate(hits, start=1):
        m = h.meta or {}
        title = m.get("title") or "Untitled"
        creators = (
            ", ".join(m.get("creators") or [])
            if isinstance(m.get("creators"), list)
            else (m.get("creators") or "")
        )
        year = (m.get("date") or "").strip()
        pieces = [p for p in [creators, year] if p]
        label = f"{title}" + (f" — {', '.join(pieces)}" if pieces else "")
        link = m.get("permalink") or m.get("link") or ""
        if link:
            label = f"{label} ({link})"
        bib.append(label)

        snippet = (h.text or "").strip().replace("\n", " ")
        if len(snippet) > 600:
            snippet = snippet[:597] + "…"
        score = m.get("score")
        score_prefix = f"[score={score}] " if isinstance(score, (float, int)) else ""
        ctx_lines.append(f"[{idx}] {score_prefix}{snippet}")

    context_str = "\n".join(ctx_lines)
    return context_str, bib


def _build_messages(question: str, hits: List[QAHit]) -> List[Dict[str, str]]:
    context_str, bib = _format_context_lines(hits)

    bib_lines = [f"[{i+1}] {entry}" for i, entry in enumerate(bib)]
    bib_block = "\n".join(bib_lines)

    user_prompt = (
        "Question:\n" + question.strip() + "\n\n"
        "CONTEXT (citations in brackets refer to the list below):\n" + context_str + "\n\n"
        "Citations:\n" + bib_block + "\n\n"
        "Instructions: Use only the information above unless you clearly state that\n"
        "the answer requires outside knowledge. Keep it concise."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _llm_answer(question: str, hits: List[QAHit]) -> str:
    """Call QroqClient chat() with messages built from hits.
    Falls back to extractive bullets if the client is unavailable or fails.
    """
    messages = _build_messages(question, hits)

    if QroqClient is None:
        return _synthesize_answer(question, hits)

    try:
        client = QroqClient()
        resp = client.chat(messages=messages)  # Expecting {'content': str, ...}
        if isinstance(resp, dict) and resp.get("content"):
            return str(resp["content"]).strip()
        # Some clients might return a text string directly
        if isinstance(resp, str) and resp.strip():
            return resp.strip()
    except Exception:
        # Silent fallback to extractive summary on any client error
        pass

    return _synthesize_answer(question, hits)


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

    # Use LLM synthesis (Qroq) with a safe fallback to extractive summary
    final_answer = _llm_answer(question, hits)

    return {
        "answer": final_answer,
        "hits": [{"text": h.text, "meta": dict(h.meta or {})} for h in hits],
    }


# Orchestrator expects `rag_answer`; expose a small wrapper.
def rag_answer(question: str, top_k: int = 6) -> Dict[str, Any]:
    return answer(question, top_k=top_k)
