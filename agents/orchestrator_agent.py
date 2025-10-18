# agents/orchestrator_agent.py
from functools import lru_cache
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from core.schemas import AgentInput, AgentOutput, ArticleBrief
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles, export_briefs_with_pnx
from agents.embedding_agent import index_jsonl
from agents.rag_agent import rag_answer


# -------------------------
# (optional) process-local memory (kept for future use, but not used now)
# -------------------------
_LAST_BRIEFS: List[ArticleBrief] = []


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
    intent: str                 # "LIST" | "ANSWER"
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

    # Only two intents are supported now: LIST or ANSWER
    intent = detect_intent(user)
    if intent == "LIST":
        out["intent"] = "LIST"
        out["topn"] = extract_top_n(user, 10)
        out["terms"] = strip_to_search_terms(user)
    else:
        out["intent"] = "ANSWER"

    return out


def list_node(state: OrchestratorState) -> OrchestratorState:
    """
    Auto-feed on LIST:
      1) Search OneSearch
      2) Export full PNX for found briefs
      3) Index into Chroma (idempotent)
    """
    terms = state.get("terms") or ""
    topn = int(state.get("topn") or 10)

    # 1) search
    briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")
    if not briefs:
        return {**state, "briefs": [], "message": f"No results found for **{terms}**."}

    # 2) export (writes /data/primo/records.jsonl, deduped)
    try:
        exported = export_briefs_with_pnx(briefs)
    except Exception as e:
        preview = _format_list(briefs, terms)
        return {
            **state,
            "briefs": briefs,
            "message": f"{preview}\n\n⚠️ Export error: {e}",
        }

    # 3) index to Chroma
    try:
        stats = index_jsonl()  # {'added': X, 'skipped_empty': Y}
    except Exception as e:
        preview = _format_list(briefs, terms)
        return {
            **state,
            "briefs": briefs,
            "export_count": exported,
            "message": f"{preview}\n\n⚠️ Indexing error after export: {e}",
        }

    # Success message + preview
    preview = _format_list(briefs, terms)
    msg = (
        f"{preview}\n\n"
    )

    return {
        **state,
        "briefs": briefs,
        "export_count": exported,
        "index_stats": stats,
        "message": msg,
    }


def answer_node(state: OrchestratorState) -> OrchestratorState:
    user = state.get("user_input") or ""
    ans = rag_answer(user)  # returns {"answer": str, "hits": [...]}
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
    g.add_node("answer", answer_node)

    g.set_entry_point("route")

    # Conditional edges from route
    def _branch(state: OrchestratorState):
        return "list" if state.get("intent") == "LIST" else "answer"

    g.add_conditional_edges("route", _branch, {
        "list": "list",
        "answer": "answer",
    })

    # Leaves
    g.add_edge("list", END)
    g.add_edge("answer", END)

    return g.compile()


# -------------------------
# Public API
# -------------------------
def handle(input: AgentInput) -> AgentOutput:
    """
    Orchestrate the user's request using a LangGraph.
    LIST -> search + export PNX + index (auto-feed)
    otherwise -> RAG answer
    """
    graph = _compile_graph()
    try:
        final_state: OrchestratorState = graph.invoke({"user_input": input.user_input})
    except Exception as e:
        return AgentOutput(text=f"Orchestration error: {e}")

    txt = final_state.get("message") or "I don’t know."
    hits = final_state.get("answer_hits") or []
    return AgentOutput(text=txt, hits=hits, list_items=[])
