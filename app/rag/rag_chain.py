# app/rag/rag_chain.py
from typing import List, Dict
from app.core.llm_client import GroqLLM
from app.rag.retriever import Retriever

SYSTEM = (
    "You are Scholar AI Assistant. Answer ONLY using the provided context. "
    "Cite each claim with [title](permalink) where possible. If unsure, say you don't know."
)

def format_context(hits: List[Dict]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        m = h["meta"] or {}
        title = m.get("title") or "Untitled"
        link = m.get("permalink", [""])[0] if isinstance(m.get("permalink"), list) else (m.get("permalink") or "")
        lines.append(f"[{i}] {title} — {link}\n{h['text']}\n")
    return "\n".join(lines)

def answer(question: str, top_k: int = 6, temperature: float = 0.2, max_tokens: int = 700) -> Dict:
    retriever = Retriever(top_k=top_k)
    hits = retriever.query(question)
    ctx = format_context(hits)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{ctx}\n\nAnswer:"}
    ]

    llm = GroqLLM()
    out = ""
    for tok in llm.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=True):
        out += tok

    return {"answer": out, "hits": hits}
