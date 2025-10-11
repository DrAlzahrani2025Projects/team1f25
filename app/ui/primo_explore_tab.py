# app/ui/primo_explore_tab.py
"""
OneSearch (Public 'pub/pnxs') — simplified UI
- Language is always English (eng) — no language control shown
- Resource type is always Articles — no rtype control shown
- "Per request" control removed from UI
- Still supports: query, peer-reviewed toggle, sort, year range
- Export fetches FULL PNX per record using context fallback (hint -> 'L' -> 'PC')
- Writes (deduped) to: /data/primo/records.jsonl
"""

from __future__ import annotations
import streamlit as st
from typing import List

from app.ingest.primo_explore_client import (
    search_with_filters,
    fetch_full_with_fallback,
)
from app.ingest.primo_schema import PrimoFull, brief_from_doc
from app.ingest.primo_store import append_records


# --- Session helpers ---
def _init_state():
    st.session_state.setdefault("explore_docs", [])      # raw search docs
    st.session_state.setdefault("explore_briefs", [])    # PrimoBrief objects
    st.session_state.setdefault("explore_run_id", 0)     # increments each search
    st.session_state.setdefault("explore_last_q", "")    # last query string

def _sel_key(i: int) -> str:
    return f"expl_sel_{st.session_state['explore_run_id']}_{i}"

def _get_selected_indices(n: int) -> List[int]:
    return [i for i in range(n) if st.session_state.get(_sel_key(i), False)]


# --- UI ---
def render_primo_explore_tab():
    _init_state()

    st.subheader("OneSearch — Public Explore API (keyless)")
    st.caption(
        "Search CSUSB OneSearch via the Primo VE public endpoint. "
        "Language is fixed to English; Resource type fixed to Articles. "
        "Export fetches FULL PNX per record for RAG."
    )

    # -------- Controls (fixed language/rtype; not shown) --------
    q = st.text_input("Query", value=st.session_state.get("explore_last_q") or "ott subscriber churn")

    c1, c2, c3 = st.columns(3)
    with c1:
        peer_rev = st.toggle("Peer-reviewed only", value=False,
                             help="Adds 'tlevel,exact,peer_reviewed' facet")
    with c2:
        sort = st.selectbox("Sort", ["rank", "date"], index=0)
    with c3:
        # Client-side year range filter
        y_from, y_to = st.slider("Year range", 1900, 2100, (2000, 2100))

    # Total items to fetch (after filters)
    limit = st.slider("Total to fetch", 10, 200, 20, 10)

    # Hidden, enforced defaults
    lang_code = "eng"               # always English
    rtypes = ["articles"]           # always Articles
    # per-request page size control is removed from UI (backend handles pagination)

    if st.button("Search", type="primary"):
        st.session_state["explore_docs"] = []
        st.session_state["explore_briefs"] = []
        st.session_state["explore_run_id"] += 1
        st.session_state["explore_last_q"] = q

        prog = st.progress(0, text="Searching…")
        try:
            resp = search_with_filters(
                query=q.strip(),
                limit=limit,
                lang_code=lang_code,
                peer_reviewed=peer_rev,
                rtypes=rtypes,
                year_from=y_from,
                year_to=y_to,
                sort=sort,
            )
            docs = resp.get("docs", []) or []
            st.session_state["explore_docs"] = docs
            st.session_state["explore_briefs"] = [brief_from_doc(d) for d in docs]
            prog.progress(100, text=f"Found {len(docs)} matching docs")
        except Exception as e:
            st.error(f"Explore API error: {e}")
        finally:
            prog.empty()

    # -------- Results & selection --------
    briefs: List = st.session_state.get("explore_briefs", [])
    docs:   List = st.session_state.get("explore_docs", [])

    if briefs:
        st.write(f"Showing **{len(briefs)}** results for **{st.session_state.get('explore_last_q','')}**")

        # Batch selection helpers
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Select all"):
                for i in range(len(briefs)):
                    st.session_state[_sel_key(i)] = True
        with c2:
            if st.button("Clear all"):
                for i in range(len(briefs)):
                    st.session_state[_sel_key(i)] = False
        with c3:
            sel_count = len(_get_selected_indices(len(briefs)))
            st.metric("Selected", sel_count)

        # Listing with checkboxes
        for i, b in enumerate(briefs):
            title = b.title or "[untitled]"
            with st.expander(f"{i+1}. {title}"):
                st.write(f"**Creators:** {', '.join(b.creators) if b.creators else '—'}")
                st.write(f"**Date:** {b.creation_date or '—'}")
                st.write(f"**Type:** {b.resource_type or '—'}")
                if b.permalink:
                    st.write(f"[Open record]({b.permalink})")
                st.checkbox("Select", key=_sel_key(i))

        # Actions
        e1, e2 = st.columns(2)
        with e1:
            if st.button("Export selected → /data/primo/records.jsonl"):
                _export_selected_with_pnx(briefs, docs)
        with e2:
            if st.button("Export ALL results → /data/primo/records.jsonl"):
                _export_indices_with_pnx(list(range(len(briefs))), briefs, docs)


def _export_selected_with_pnx(briefs, docs):
    selected = _get_selected_indices(len(briefs))
    if not selected:
        st.warning("No rows selected. Use the checkboxes, or click “Export ALL results”.")
        return
    _export_indices_with_pnx(selected, briefs, docs)

from app.ingest.primo_schema import PrimoFull  # local import to avoid boot cycles

def _export_indices_with_pnx(indices: List[int], briefs, docs):
    payload: List[PrimoFull] = []
    prog = st.progress(0, text="Fetching full records (PNX)…")
    try:
        for j, idx in enumerate(indices, start=1):
            d = docs[idx]
            b = briefs[idx]
            # Fetch full PNX with robust fallback (hint -> L -> PC)
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
            prog.progress(int(j / max(1, len(indices)) * 100), text=f"Fetched {j}/{len(indices)}")
    finally:
        prog.empty()

    wrote = append_records(payload, dedupe=True)
    if wrote > 0:
        st.success(f"Exported **{wrote}** new records with PNX to `/data/primo/records.jsonl`.")
    else:
        st.warning("No new records written (duplicates or failures).")
