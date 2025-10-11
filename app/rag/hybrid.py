from typing import List, Dict
from rapidfuzz import fuzz

def keyword_score(text: str, query: str) -> float:
    # Fast, order-insensitive fuzzy score (0..100)
    return float(fuzz.token_set_ratio((text or "")[:2000], query or "")) / 100.0

def to_similarity(dense_distance: float) -> float:
    # Chroma cosine distance on normalized vectors; smaller is better.
    # Convert to similarity ~ [0..1].
    d = max(0.0, min(2.0, float(dense_distance)))
    return 1.0 - (d / 2.0)

def hybrid_rank(hits: List[Dict], query: str, alpha: float = 0.7) -> List[Dict]:
    """
    hits: [{"text": str, "meta": {...}, "score": distance(float)}] from Retriever
    returns: same hits with 'dense_sim','kw','hybrid' scores, sorted desc by 'hybrid'
    """
    out = []
    for h in hits:
        dense_sim = to_similarity(h.get("score", 0.0))
        kw = keyword_score(h.get("text", ""), query)
        hybrid = alpha * dense_sim + (1 - alpha) * kw
        out.append({**h, "dense_sim": dense_sim, "kw": kw, "hybrid": hybrid})
    return sorted(out, key=lambda x: x["hybrid"], reverse=True)
