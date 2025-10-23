"""
Simplified orchestrator: LIST-only.

Removes RAG answering and any feed/export/indexing behavior. The handler parses
the user's intent for a listing request, runs a library search, and returns a
formatted list. No side effects, no vector DB, no LLM calls.
"""

from typing import List
from core.schemas import AgentInput, AgentOutput, SearchBreif
from core.utils import extract_top_n, strip_to_search_terms, strip_to_search_type, strip_to_authors, parse_date_range, parse_peer_review_flag
from agents.retrieval_agent import search
from core.logging_utils import get_logger


# -------------------------
# (optional) process-local memory (kept for future use, but not used now)
# -------------------------
_log = get_logger(__name__)


def _format_list(briefs: List[SearchBreif], terms: str) -> str:
    """Render results as a Markdown table with type, title, authors, created date, and link."""
    header = f"Top {len(briefs)} results for **{terms}**:\n\n"
    lines = ["| # | Type | Title | Authors | Year | Link |", "|---|------|-------|---------|------|------|"]
    for i, b in enumerate(briefs, 1):
        rtype = b.resource_type or "—"
        title = b.title or "Untitled"
        authors = ", ".join(b.creators) if b.creators else "—"
        year = b.creation_date or ""
        link = b.permalink or ""
        link_cell = f"[{link}]({link})" if link else ""
        lines.append(f"| {i} | {rtype} | {title} | {authors} | {year} | {link_cell} |")
    return header + "\n".join(lines)

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
        stype = strip_to_search_type(user) or None
        authors = strip_to_authors(user) or None
        yfrom, yto = parse_date_range(user, 1900, 2100)
        pr = parse_peer_review_flag(user)
        if not terms:
            return AgentOutput(text="Please provide search terms, e.g., 'List top 10 machine learning articles'.")

        _log.info("LIST handler: terms='%s' topn=%d type=%s authors=%s yfrom=%s yto=%s pr=%s", terms, topn, stype, authors, yfrom, yto, pr)
        briefs: List[SearchBreif] = search(terms, n=topn, peer_reviewed=pr, sort="rank", search_type=stype, year_from=yfrom, year_to=yto, authors=authors)
        if not briefs:
            return AgentOutput(text=f"No results found for **{terms}**.")

        msg = _format_list(briefs, terms)
        return AgentOutput(text=msg, briefs=briefs)
    except Exception as e:
        return AgentOutput(text=f"Error handling request: {e}")
