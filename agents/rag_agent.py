# agents/rag_agent.py
from __future__ import annotations
from typing import Dict, Any

def answer(question: str, top_k: int = 6) -> Dict[str, Any]:
    return {"answer": "RAG agent will answer coming sprint", "hits": []}
