# agents/rag_agent.py
from typing import Any, Dict, List, Tuple
from core.embedding_model import Embedder
from core.chroma_client import get_collection, query
from core.qroq_client import QroqClient

# --- System prompt for the assistant used in RAG ---
SYSTEM_PROMPT = (
    "You are a precise, helpful assistant.\n"
    "Use the provided context to answer the user's question.\n"
    "If the context is insufficient, say so and explain what is missing.\n"
    "Cite sources inline using bracketed numbers that map to the context items, e.g., [1], [2].\n"
    "Do not invent citations or links. Keep the answer concise and accurate."
)


def _build_context(hits: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Return a formatted context string and a normalized hits list.

    Each context block is formatted as:
        [k] Title — optional_link\n
        document text
    """
    lines: List[str] = []
    normalized: List[Dict[str, Any]] = []
    for i, h in enumerate(hits, start=1):
        meta = h.get("meta") or {}
        title = (
            meta.get("title")
            or meta.get("source")
            or meta.get("file")
            or h.get("id")
            or f"doc-{i}"
        )
        link = meta.get("link") or meta.get("url") or meta.get("source_url")
        header = f"[{i}] {title}"
        if link:
            header += f" — {link}"
        text = (h.get("text") or "").strip()
        lines.append(f"{header}\n\n{text}")

        # Keep only stable keys in the returned hits
        normalized.append(
            {
                "id": h.get("id"),
                "text": text,
                "meta": meta,
                "score": h.get("score"),
            }
        )

    return "\n\n".join(lines), normalized


def rag_answer(question: str, top_k: int = 6) -> Dict[str, Any]:
    """Run a RAG query against Chroma and answer with a Groq LLM.

    Args:
        question: The user's question.
        top_k: Number of nearest neighbors to retrieve.

    Returns:
        A dict with keys:
            - "answer": str, the LLM's final answer text
            - "hits": List[Dict], the retrieved documents with minimal fields
    """
    # 1) Embed the question
    embedder = Embedder()
    q_vec = embedder.embed([question])[0]

    # 2) Get Chroma collection and retrieve neighbors
    coll = get_collection()
    hits = query(coll, q_vec, top_k=int(top_k))

    # 3) Build formatted context for the LLM and normalize hits
    context_str, norm_hits = _build_context(hits)

    # 4) Compose messages and query Groq
    client = QroqClient()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Answer the question using the context below.\n\n"
                f"Question: {question}\n\n"
                f"Context:\n{context_str}\n\n"
                "When you cite, use [n] where n matches the context item."
            ),
        },
    ]

    answer = client.chat(messages)

    return {"answer": answer, "hits": norm_hits}


__all__ = ["rag_answer", "SYSTEM_PROMPT"]
