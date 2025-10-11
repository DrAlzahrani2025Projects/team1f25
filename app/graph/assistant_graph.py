# app/graph/assistant_graph.py
from __future__ import annotations
import os, re
from typing import TypedDict, List, Dict, Any, Optional

try:
    from langgraph.graph import StateGraph, START, END
except Exception as e:
    raise RuntimeError("Please add 'langgraph' to requirements.txt and rebuild.") from e

from app.ingest.primo_explore_client import (
    search_with_filters,
    fetch_full_with_fallback,
)
from app.ingest.primo_store import append_records
from app.ingest.primo_schema import PrimoFull, brief_from_doc
from app.rag.indexer import index_jsonl
from app.rag.rag_chain import answer as rag_answer

PRIMO_VID = os.getenv("PRIMO_VID", "01CALS_USB:01CALS_USB")
PRIMO_BASE = os.getenv("PRIMO_DISCOVERY_BASE", "https://csu-sb.primo.exlibrisgroup.com")


# ---------------------------
# State
# ---------------------------
class AssistantState(TypedDict, total=False):
    user_input: str
    intent: str                       # "LIST" | "ANSWER"
    search_query: str
    list_n: int
    peer_reviewed: bool
    sort: str                         # "rank" | "date"
    year_from: int
    year_to: int
    docs: List[Dict[str, Any]]        # raw explore docs
    briefs: List[Any]                 # PrimoBrief (we keep 'Any' to avoid import typing hiccups)
    exported: int
    index_info: Dict[str, Any]
    answer: str
    hits: List[Dict[str, Any]]
    needs_refresh: bool
    response_markdown: str


# ---------------------------
# Small helpers
# ---------------------------
def _extract_top_n(text: str, default: int = 10) -> int:
    m = re.search(r"\btop\s+(\d{1,3})\b", text, flags=re.I)
    if m:
        try:
            n = int(m.group(1))
            return max(1, min(50, n))
        except Exception:
            pass
    return default

def _looks_like_list_request(text: str) -> bool:
    text = text.lower()
    return any(w in text for w in ["list ", "top ", "show ", "find articles", "retrieve articles", "search articles"])

def _derive_search_terms(text: str) -> str:
    # strip common framing words
    t = re.sub(r"\b(list|show|find|retrieve)\b", "", text, flags=re.I)
    t = re.sub(r"\b(top\s+\d+)\b", "", t, flags=re.I)
    t = re.sub(r"\b(articles?|papers?|literature|references?)\b", "", t, flags=re.I)
    t = t.replace("about", " ").replace("on", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t or text.strip()

def _fulldisplay_link(record_id: str, context: str = "PC") -> str:
    return f"{PRIMO_BASE}/discovery/fulldisplay?vid={PRIMO_VID}&context={context}&docid={record_id}"


# ---------------------------
# Graph nodes
# ---------------------------
def n_classify(state: AssistantState) -> AssistantState:
    text = state["user_input"]
    if _looks_like_list_request(text):
        state["intent"] = "LIST"
        state["list_n"] = _extract_top_n(text, 10)
        state["search_query"] = _derive_search_terms(text)
    else:
        state["intent"] = "ANSWER"
        state["search_query"] = _derive_search_terms(text)
    # default filters (hidden): English + Articles
    state.setdefault("peer_reviewed", False)
    state.setdefault("sort", "rank")
    state.setdefault("year_from", 1900)
    state.setdefault("year_to", 2100)
    return state


def n_search(state: AssistantState) -> AssistantState:
    q = state["search_query"]
    n = state.get("list_n", 10)
    resp = search_with_filters(
        query=q,
        limit=n,
        lang_code="eng",
        peer_reviewed=state.get("peer_reviewed", False),
        rtypes=["articles"],
        year_from=state.get("year_from", 1900),
        year_to=state.get("year_to", 2100),
        sort=state.get("sort", "rank"),
    )
    docs = resp.get("docs", []) or []
    state["docs"] = docs
    state["briefs"] = [brief_from_doc(d) for d in docs]
    return state


def n_fetch_export_index(state: AssistantState) -> AssistantState:
    briefs = state.get("briefs") or []
    docs = state.get("docs") or []
    payload: List[PrimoFull] = []
    for d, b in zip(docs, briefs):
        # fetch PNX (cache-enabled inside client)
        try:
            full = fetch_full_with_fallback(b.record_id, context_hint=b.context)
            pnx   = full.get("pnx", {}) or d.get("pnx", {})
            links = full.get("link", {}) or d.get("link", {})
            raw   = full if full.get("pnx") else d
        except Exception:
            pnx   = d.get("pnx", {})
            links = d.get("link", {})
            raw   = d
        payload.append(PrimoFull(brief=b, pnx=pnx, links=links, raw=raw))

    written = append_records(payload, dedupe=True)
    state["exported"] = int(written)

    # Incremental (upsert) index
    info = index_jsonl()
    state["index_info"] = info
    return state


def n_list_response(state: AssistantState) -> AssistantState:
    briefs = state.get("briefs") or []
    lines = []
    for i, b in enumerate(briefs, 1):
        rid = b.record_id
        link = b.permalink or _fulldisplay_link(rid, context=b.context or "PC")
        title = b.title or "Untitled"
        creators = ", ".join(b.creators) if b.creators else "—"
        date = b.creation_date or "—"
        lines.append(f"{i}. **{title}** ({date}) — *{creators}* — [{link}]({link})")
    exported = state.get("exported", 0)
    added = state.get("index_info", {}).get("added", 0)
    state["response_markdown"] = (
        f"Here are the top {len(briefs)} articles for **{state.get('search_query','')}**:\n\n"
        + "\n".join(lines)
        + f"\n\n_Exported {exported} new records and indexed {added} chunks to the vector DB._"
    )
    return state


def n_try_answer(state: AssistantState) -> AssistantState:
    q = state["user_input"].strip()
    res = rag_answer(question=q)  # rerank & temps hidden inside your chain
    state["answer"] = res.get("answer", "")
    state["hits"] = res.get("hits", []) or []
    # If retrieval seems weak, trigger refresh (threshold: <3 hits or empty text)
    need = 0
    for h in state["hits"]:
        if h.get("text"):
            need += 1
    state["needs_refresh"] = (need < 3)
    return state


def n_refresh_from_onesearch(state: AssistantState) -> AssistantState:
    # Use derived terms from the question as a search query; fetch more to enrich the corpus.
    state.setdefault("list_n", 20)
    state = n_search(state)                 # reuse search node
    state = n_fetch_export_index(state)     # export + index (incremental)
    return state


def n_answer_response(state: AssistantState) -> AssistantState:
    if state.get("answer"):
        state["response_markdown"] = state["answer"]
    else:
        state["response_markdown"] = "I couldn’t produce an answer yet."
    return state


# ---------------------------
# Graph builder
# ---------------------------
def build_assistant_graph():
    g = StateGraph(AssistantState)

    g.add_node("classify", n_classify)
    g.add_node("search", n_search)
    g.add_node("export_index", n_fetch_export_index)
    g.add_node("list_response", n_list_response)
    g.add_node("try_answer", n_try_answer)
    g.add_node("refresh", n_refresh_from_onesearch)
    g.add_node("answer_response", n_answer_response)

    g.add_edge(START, "classify")

    # Route by intent
    def route_by_intent(state: AssistantState):
        return state["intent"]

    g.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "LIST": "search",
            "ANSWER": "try_answer",
        },
    )

    # LIST path: search -> export_index -> list_response -> END
    g.add_edge("search", "export_index")
    g.add_edge("export_index", "list_response")
    g.add_edge("list_response", END)

    # ANSWER path: try_answer -> (needs_refresh?) -> refresh -> try_answer -> answer_response -> END
    def needs_refresh(state: AssistantState):
        return "refresh" if state.get("needs_refresh") else "done"

    g.add_conditional_edges(
        "try_answer",
        needs_refresh,
        {
            "refresh": "refresh",
            "done": "answer_response",
        },
    )
    g.add_edge("refresh", "try_answer")
    g.add_edge("answer_response", END)

    return g.compile()


# Singleton graph instance
_GRAPH = build_assistant_graph()

def run_assistant(user_input: str) -> Dict[str, Any]:
    init: AssistantState = {"user_input": user_input}
    return _GRAPH.invoke(init)
