# agents/orchestrator_agent.py
from __future__ import annotations
from typing import List, Optional
from core.schemas import AgentInput, AgentOutput, ArticleBrief
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles, export_briefs_with_pnx
from agents.embedding_agent import index_jsonl
from agents.rag_agent_stub import answer as rag_answer  # replace in week 4

# In-memory stash of the last listed briefs (per process).
_LAST_BRIEFS: List[ArticleBrief] = []

def _set_last_briefs(briefs: List[ArticleBrief]) -> None:
    global _LAST_BRIEFS
    _LAST_BRIEFS = briefs or []

def _get_last_briefs() -> List[ArticleBrief]:
    return list(_LAST_BRIEFS)

def _is_feed_command(text: str) -> bool:
    return text.strip().lower().startswith("feed")

def _parse_feed_query(text: str) -> Optional[str]:
    t = text.strip()
    if t.lower() == "feed":
        return None
    if t.lower().startswith("feed "):
        return t[len("feed "):].strip() or None
    return None

def _format_list(briefs: List[ArticleBrief], terms: str) -> str:
    lines = []
    for i, b in enumerate(briefs, 1):
        creators = ", ".join(b.creators) if b.creators else "—"
        link = b.permalink or ""
        lines.append(f"{i}. **{b.title}** ({b.creation_date}) — *{creators}* — {link}")
    return f"Top {len(briefs)} results for **{terms}**:\n\n" + "\n".join(lines)

def handle(input: AgentInput) -> AgentOutput:
    user = input.user_input.strip()

    # --- FEED commands (export + index) ---
    if _is_feed_command(user):
        q = _parse_feed_query(user)
        # Case A: feed <query> — search now, stash, then export+index
        if q:
            n = extract_top_n(q, 20)
            terms = strip_to_search_terms(q)
            briefs = search_articles(terms, n=n, peer_reviewed=False, sort="rank")
            if not briefs:
                return AgentOutput(text=f"No results found for **{terms}**.")
            _set_last_briefs(briefs)
            exported = export_briefs_with_pnx(briefs)
            stats = index_jsonl()
            preview = _format_list(briefs, terms)
            msg = (
                f"{preview}\n\n"
                f"✅ Feed complete — Exported **{exported}** new records and indexed "
                f"`added={stats.get('added',0)}` · `skipped_empty={stats.get('skipped_empty',0)}`."
            )
            return AgentOutput(text=msg, list_items=[], briefs=[], hits=[])
        # Case B: feed — use last listed briefs
        last = _get_last_briefs()
        if not last:
            return AgentOutput(text="Nothing to feed yet. Ask me to **list** some articles first, then type **feed**.")
        exported = export_briefs_with_pnx(last)
        stats = index_jsonl()
        msg = (
            f"✅ Feed complete — Exported **{exported}** new records and indexed "
            f"`added={stats.get('added',0)}` · `skipped_empty={stats.get('skipped_empty',0)}`."
        )
        return AgentOutput(text=msg)

    # --- Route normal intents ---
    intent = detect_intent(user)

    if intent == "LIST":
        topn = extract_top_n(user, 10)
        terms = strip_to_search_terms(user)
        briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")
        _set_last_briefs(briefs)
        preview = _format_list(briefs, terms)
        # Tell the user they can now type 'feed' (UI doesn't need to implement it)
        preview += "\n\n_(Type **feed** to export these results and index them to the vector DB.)_"
        return AgentOutput(text=preview, list_items=[], briefs=[])

    # ANSWER intent (RAG stub; week 4 will replace)
    ans = rag_answer(user)
    return AgentOutput(text=ans.get("answer") or "I don’t know yet.", hits=[])
