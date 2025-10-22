"""
Simplified orchestrator: LIST-only.

Removes RAG answering and any feed/export/indexing behavior. The handler parses
the user's intent for a listing request, runs a library search, and returns a
formatted list. No side effects, no vector DB, no LLM calls.
"""

from typing import List
from core.schemas import AgentInput, AgentOutput, SearchBreif
from core.utils import extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search
from core.logging_utils import get_logger


# -------------------------
# (optional) process-local memory (kept for future use, but not used now)
# -------------------------
_log = get_logger(__name__)


def _format_list(briefs: List[SearchBreif], terms: str) -> str:
    lines = []
    for i, b in enumerate(briefs, 1):
        creators = ", ".join(b.creators) if b.creators else "—"
        link = b.permalink or ""
        rtype = (b.resource_type or "").lower()
        rtype_tag = f"[{rtype}] " if rtype else ""
        lines.append(f"{i}. {rtype_tag}**{b.title}** ({b.creation_date}) — *{creators}* — {link}")
    return f"Top {len(briefs)} results for **{terms}**:\n\n" + "\n".join(lines)

# -------------------------
# Public API (LIST-only)
# -------------------------
def handle(input: AgentInput) -> AgentOutput:
    """Handle a listing request.

    Extracts search terms and top-N from the user's input, runs a library
    search, and returns a formatted text response. No export/index/LLM.
    """
    try:
        user = (input.user_input or "").strip()
        topn = extract_top_n(user, 10)
        terms = strip_to_search_terms(user)
        if not terms:
            return AgentOutput(text="Please provide search terms, e.g., 'List top 10 machine learning articles'.")

        _log.info("LIST handler: terms='%s' topn=%d", terms, topn)
        briefs: List[SearchBreif] = search(terms, n=topn, peer_reviewed=False, sort="rank")
        if not briefs:
            return AgentOutput(text=f"No results found for **{terms}**.")

        msg = _format_list(briefs, terms)
        return AgentOutput(text=msg, briefs=briefs)
    except Exception as e:
        return AgentOutput(text=f"Error handling request: {e}")
