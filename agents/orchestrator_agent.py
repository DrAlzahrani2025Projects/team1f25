# agents/orchestrator_agent.py
from functools import lru_cache
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from core.schemas import AgentInput, AgentOutput, ArticleBrief
from core.utils import detect_intent, extract_top_n, strip_to_search_terms
from agents.retrieval_agent import search_articles, export_briefs_with_pnx
from agents.embedding_agent import (
    index_jsonl,
    index_jsonl_recent,
    index_jsonl_incremental,
)
from agents.rag_agent import rag_answer
from core.logging_utils import get_logger


# -------------------------
# (optional) process-local memory (kept for future use, but not used now)
# -------------------------
_LAST_BRIEFS: List[ArticleBrief] = []
_log = get_logger(__name__)


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
    _log.info("Orchestrator LIST start: terms='%s' topn=%d", terms, topn)

    # 1) search
    briefs = search_articles(terms, n=topn, peer_reviewed=False, sort="rank")
    if not briefs:
        _log.info("Orchestrator LIST: no results for terms='%s'", terms)
        # reset cache on no results
        global _LAST_BRIEFS
        _LAST_BRIEFS = []
        return {**state, "briefs": [], "message": f"No results found for **{terms}**."}

    # Build preview once for reuse
    preview = _format_list(briefs, terms)

    # Fast-path: if results are the same as last time, avoid re-export / re-index
    try:
        last_ids = {b.record_id for b in _LAST_BRIEFS}
        curr_ids = {b.record_id for b in briefs}
        if last_ids and curr_ids and last_ids == curr_ids:
            _log.info("Orchestrator LIST: identical results as last run; skipping export/index")
            return {**state, "briefs": briefs, "message": f"{preview}\n\n"}
    except Exception:
        # Non-fatal; proceed normally
        pass

    # 2) export (writes /data/primo/records.jsonl, deduped)
    try:
        exported = export_briefs_with_pnx(briefs)
        _log.info("Orchestrator LIST: exported=%d", exported)
    except Exception as e:
        return {
            **state,
            "briefs": briefs,
            "message": f"{preview}\n\n⚠️ Export error: {e}",
        }

    # 3) index to Chroma
    # Skip indexing if nothing new was exported as a quick optimization
    if exported == 0:
        _log.info("Orchestrator LIST: no new records to index; skipping indexing step")
        # Update cache
        _LAST_BRIEFS = briefs
        msg = (f"{preview}\n\n")
        return {
            **state,
            "briefs": briefs,
            "export_count": exported,
            "message": msg,
        }

    # Prefer incremental indexing; if we just appended N records, try a tail-only pass first.
    try:
        if isinstance(exported, int) and exported > 0:
            try:
                stats = index_jsonl_recent(exported)
            except Exception as e_recent:
                _log.warning(
                    "Orchestrator LIST: recent index failed (%s); falling back to incremental",
                    e_recent,
                )
                stats = index_jsonl_incremental()
        else:
            stats = index_jsonl_incremental()
        _log.info("Orchestrator LIST: index stats=%s", stats)
    except Exception as e_incr:
        _log.warning(
            "Orchestrator LIST: incremental index failed (%s); falling back to full scan",
            e_incr,
        )
        try:
            stats = index_jsonl()  # full scan as last resort
            _log.info("Orchestrator LIST: full index stats=%s", stats)
        except Exception as e_full:
            return {
                **state,
                "briefs": briefs,
                "export_count": exported,
                "message": f"{preview}\n\n⚠️ Indexing error after export: {e_full}",
            }

    # Success message + preview
    msg = (
        f"{preview}\n\n"
    )

    # Update cache
    _LAST_BRIEFS = briefs

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
