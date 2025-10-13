from __future__ import annotations
from core.schemas import AgentInput, AgentOutput
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles
from agents.rag_agent_stub import answer as rag_answer  # real RAG in week 4

def handle(input: AgentInput) -> AgentOutput:
    user = input.user_input.strip()
    intent = detect_intent(user)

    if intent == "LIST":
        topn = extract_top_n(user, 10)
        terms = strip_to_search_terms(user)
        briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")

        # Build a human-readable preview with permalinks (NO EXPORT YET)
        lines = []
        for i, b in enumerate(briefs, 1):
            creators = ", ".join(b.creators) if b.creators else "—"
            link = b.permalink or ""
            lines.append(f"{i}. **{b.title}** ({b.creation_date}) — *{creators}* — {link}")

        txt = (
            f"Top {len(briefs)} results for **{terms}**:\n\n"
            + "\n".join(lines)
        )
        return AgentOutput(
            text=txt,
            list_items=lines,
            briefs=briefs,         # let the UI export these later
            await_export=True,     # UI shows the export button
        )

    # ANSWER intent (RAG stub for now)
    ans = rag_answer(user)
    return AgentOutput(text=ans.get("answer") or "I don’t know yet.", hits=[])
