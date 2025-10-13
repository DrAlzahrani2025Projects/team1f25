from __future__ import annotations
from core.schemas import AgentInput, AgentOutput
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles, fetch_pnx_for_briefs
from agents.embedding_agent import upsert_records
from agents.rag_agent_stub import answer as rag_answer

def handle(input: AgentInput) -> AgentOutput:
    """
    Week 1 orchestrator:
      - LIST intent -> call retrieval stub, (stub) embed/upsert, return a formatted list
      - ANSWER intent -> call RAG stub; if weak, simulate refresh via retrieval+upsert then answer again
    """
    user = input.user_input.strip()
    intent = detect_intent(user)

    if intent == "LIST":
        topn = extract_top_n(user, 10)
        terms = strip_to_search_terms(user)
        briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")
        # (Week 2+) fetch PNX & (Week 3+) upsert embeddings; here stubs:
        records = fetch_pnx_for_briefs(briefs)
        _ = upsert_records(records)

        lines = []
        for i, b in enumerate(briefs, 1):
            creators = ", ".join(b.creators) if b.creators else "—"
            link = b.permalink or ""
            lines.append(f"{i}. **{b.title}** ({b.creation_date}) — *{creators}* — {link}")
        text = f"Top {len(briefs)} results for **{terms}**:\n\n" + "\n".join(lines)
        return AgentOutput(text=text, list_items=lines)

    # ANSWER
    ans = rag_answer(user)
    if not ans.get("answer"):
        # simulate corpus refresh path (Week 2–3 real logic)
        terms = strip_to_search_terms(user)
        briefs = search_articles(terms, n=10)
        records = fetch_pnx_for_briefs(briefs)
        _ = upsert_records(records)
        ans = rag_answer(user)

    return AgentOutput(text=ans.get("answer") or "I don’t know yet.", hits=[])
