from typing import List, Dict
from app.core.llm_client import GroqLLM

PROMPT = (
"Score how well the passage answers the question on a 0-100 scale.\n"
"Return ONLY the number.\n\n"
"Question:\n{q}\n\nPassage:\n{p}\n"
)

def llm_score(q: str, passage: str, model_temp: float = 0.0) -> float:
    llm = GroqLLM()
    msg = [{"role":"user","content": PROMPT.format(q=q, p=passage[:2000])}]
    out = llm.chat(msg, temperature=model_temp, max_tokens=8, stream=False)
    try:
        return max(0.0, min(100.0, float(out.strip().split()[0])))
    except Exception:
        return 0.0

def rerank_llm(question: str, hits: List[Dict], topN: int = 12) -> List[Dict]:
    cand = hits[:topN]
    scored = []
    for h in cand:
        s = llm_score(question, h.get("text",""))
        scored.append({**h, "rerank": s})
    return sorted(scored, key=lambda x: x["rerank"], reverse=True) + hits[topN:]
