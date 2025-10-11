# app/rag/rag_chain.py
from __future__ import annotations
import os
from typing import List, Dict
from app.core.llm_client import GroqLLM
from app.rag.retriever import Retriever
from app.rag.hybrid import hybrid_rank
from app.rag.rerank import rerank_llm

SYSTEM = (
    "You are Scholar AI Assistant. Use ONLY the provided context.\n"
    "Cite with [n] and include (Title — Link). If unsure, say you don't know."
)

def format_context(hits: List[Dict]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        m = h.get("meta", {}) or {}
        title = m.get("title") or "Untitled"
        link = m.get("permalink", [""])[0] if isinstance(m.get("permalink"), list) else (m.get("permalink") or "")
        lines.append(f"[{i}] {title} — {link}\n{h.get('text','')}\n")
    return "\n".join(lines)

def answer(
    question: str,
    top_k: int = 6,
    alpha: float = 0.7,
    use_rerank: bool = True,          # rerank stays on
    rerank_topN: int = 12,
    temperature: float | None = None, # <— optional; default from env
    max_tokens: int = 700
) -> Dict:
    # figure out temp without exposing it in UI
    if temperature is None:
        try:
            temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
        except Exception:
            temperature = 0.2

    # 1) dense retrieve
    r = Retriever(top_k=max(top_k, rerank_topN))
    dense_hits = r.query(question)

    # 2) hybrid combine
    hybrid_hits = hybrid_rank(dense_hits, question, alpha=alpha)

    # 3) optional LLM rerank (always True by default)
    ranked = rerank_llm(question, hybrid_hits, topN=rerank_topN) if use_rerank else hybrid_hits

    final_hits = ranked[:top_k]
    ctx = format_context(final_hits)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{ctx}\n\nAnswer with citations [n]:"}
    ]

    try:
        llm = GroqLLM()
        out = llm.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=False)
        if not (out or "").strip():
            titles = [ (h.get("meta",{}) or {}).get("title") or "Untitled" for h in final_hits ]
            out = ("I don’t know based on the retrieved sources.\n\n"
                   "Top sources considered:\n- " + "\n- ".join(titles[:min(3,len(titles))]))
    except Exception as e:
        out = f"(LLM error: {e})"

    return {"answer": out, "hits": final_hits}
