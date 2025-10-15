# agents/orchestrator_agent.py
from __future__ import annotations
from functools import lru_cache
from typing import List, Optional, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
# (optional) in-memory checkpoint; not strictly needed here
# from langgraph.checkpoint.memory import MemorySaver
from core.schemas import AgentInput, AgentOutput, ArticleBrief
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles, export_briefs_with_pnx
from agents.embedding_agent import index_jsonl
from agents.rag_agent import rag_answer


# -------------------------
# Process-local memory (used by `feed` without query)
# -------------------------
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
        q = t[len("feed "):].strip()
        return q or None
    return None


def _format_list(briefs: List[ArticleBrief], terms: str) -> str:
    lines = []
    for i, b in enumerate(briefs, 1):
        creators = ", ".join(b.creators) if b.creators else "—"
        link = b.permalink or ""
        lines.append(f"{i}. **{b.title}** ({b.creation_date}) — *{creators}* — {link}")
    return f"Top {len(briefs)} results for **{terms}**:\n\n" + "\n".join(lines)


# -------------------------
# LangGraph state
# -------------------------
class OrchestratorState(TypedDict, total=False):
    user_input: str
    intent: str                 # "LIST" | "ANSWER" | "FEED"
    feed_query: Optional[str]   # for "feed <query>"
    terms: str
    topn: int
    briefs: List[ArticleBrief]
    message: str                # final text message
    answer_hits: List[Dict[str, Any]]
    export_count: int
    index_stats: Dict[str, Any]


# -------------------------
# Nodes
# -------------------------
def route_node(state: OrchestratorState) -> OrchestratorState:
    user = (state.get("user_input") or "").strip()
    out: OrchestratorState = dict(state)

    # FEED has priority
    if _is_feed_command(user):
        out["intent"] = "FEED"
        out["feed_query"] = _parse_feed_query(user)
        return out

    # Otherwise LIST / ANSWER
    out["intent"] = detect_intent(user)
    if out["intent"] == "LIST":
        out["topn"] = extract_top_n(user, 10)
        out["terms"] = strip_to_search_terms(user)
    return out


def list_node(state: OrchestratorState) -> OrchestratorState:
    terms = state.get("terms") or ""
    topn = int(state.get("topn") or 10)

    briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")
    _set_last_briefs(briefs)
    preview = _format_list(briefs, terms)
    preview += "\n\n_(Type **feed** to export these results and index them to the vector DB.)_"

    return {
        **state,
        "briefs": briefs,
        "message": preview,
    }


def feed_query_node(state: OrchestratorState) -> OrchestratorState:
    raw_q = state.get("feed_query") or ""
    n = extract_top_n(raw_q, 20)
    terms = strip_to_search_terms(raw_q)

    briefs = search_articles(terms, n=n, peer_reviewed=False, sort="rank")
    if not briefs:
        return {**state, "message": f"No results found for **{terms}**."}

    _set_last_briefs(briefs)

    exported = export_briefs_with_pnx(briefs)
    stats = index_jsonl()  # {'added': X, 'skipped_empty': Y}

    preview = _format_list(briefs, terms)
    msg = (
        f"{preview}\n\n"
        f"✅ Feed complete — Exported **{exported}** new records and indexed "
        f"`added={stats.get('added',0)}` · `skipped_empty={stats.get('skipped_empty',0)}`."
    )
    return {
        **state,
        "briefs": briefs,
        "export_count": exported,
        "index_stats": stats,
        "message": msg,
    }


def feed_last_node(state: OrchestratorState) -> OrchestratorState:
    last = _get_last_briefs()
    if not last:
        return {**state, "message": "Nothing to feed yet. Ask me to **list** some articles first, then type **feed**."}

    exported = export_briefs_with_pnx(last)
    stats = index_jsonl()
    msg = (
        f"✅ Feed complete — Exported **{exported}** new records and indexed "
        f"`added={stats.get('added',0)}` · `skipped_empty={stats.get('skipped_empty',0)}`."
    )
    return {**state, "export_count": exported, "index_stats": stats, "message": msg}


def answer_node(state: OrchestratorState) -> OrchestratorState:
    user = state.get("user_input") or ""
    ans = rag_answer(user)
    # ans: {"answer": str, "hits": [...]}
    return {
        **state,
        "message": ans.get("answer") or "I don’t know.",
        "answer_hits": ans.get("hits") or [],
    }


# -------------------------
# Graph assembly
# -------------------------
@lru_cache(maxsize=1)
def _compile_graph():
    g = StateGraph(OrchestratorState)

    g.add_node("route", route_node)
    g.add_node("list", list_node)
    g.add_node("feed_query", feed_query_node)
    g.add_node("feed_last", feed_last_node)
    g.add_node("answer", answer_node)

    g.set_entry_point("route")

    # Conditional edges from route
    def _branch(state: OrchestratorState):
        intent = state.get("intent")
        if intent == "FEED":
            return "feed_query" if state.get("feed_query") else "feed_last"
        if intent == "LIST":
            return "list"
        return "answer"

    g.add_conditional_edges("route", _branch, {
        "feed_query": "feed_query",
        "feed_last": "feed_last",
        "list": "list",
        "answer": "answer",
    })

    # All leaf nodes end
    g.add_edge("list", END)
    g.add_edge("feed_query", END)
    g.add_edge("feed_last", END)
    g.add_edge("answer", END)

    # If you want checkpointing across turns, enable a checkpointer:
    # memory = MemorySaver()
    # return g.compile(checkpointer=memory)

    return g.compile()


# -------------------------
# Public API (unchanged)
# -------------------------
def handle(input: AgentInput) -> AgentOutput:
    """
    Orchestrate the user's request using a LangGraph.
    Keeps the same return type used by the Streamlit UI.
    """
    graph = _compile_graph()
    try:
        final_state: OrchestratorState = graph.invoke({"user_input": input.user_input})
    except Exception as e:
        return AgentOutput(text=f"Orchestration error: {e}")

    txt = final_state.get("message") or "I don’t know."
    # Optionally surface RAG hits later if your UI wants them:
    hits = final_state.get("answer_hits") or []
    return AgentOutput(text=txt, hits=hits, list_items=[])
