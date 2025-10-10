# app/ui/primo_explore_tab.py
"""
Streamlit tab for CSUSB OneSearch (Public 'pub/pnxs' endpoint).

- Keyless searches via Primo VE public API.
- Shows brief results; lets you select, select-all, or export-all.
- Export fetches FULL PNX per record using context fallback (hint -> 'L' -> 'PC').

Writes (deduped) to: /data/primo/records.jsonl
"""

from __future__ import annotations
import streamlit as st
from typing import List

from app.ingest.primo_explore_client import (
    explore_search,
    fetch_full_with_fallback,
)
from app.ingest.primo_schema import PrimoFull, brief_from_doc
from app.ingest.primo_store import append_records


def _init_state():
    st.session_state.setdefault("explore_docs", [])      # raw search docs
    st.session_state.setdefault("explore_briefs", [])    # PrimoBrief objects
    st.session_state.setdefault("explore_run_id", 0)     # increments each search
    st.session_state.setdefault("explore_last_q", "")    # last query string


def _sel_key(i: int) -> str:
    """Unique checkbox key for this search run."""
    return f"expl_sel_{st.session_state['explore_run_id']}_{i}"


def _get_selected_indices(n: int) -> List[int]:
    """Read current checkbox states into a list of selected indices."""
    selected = []
    for i in range(n):
        if st.session_state.get(_sel_key(i), False):
            selected.append(i)
    return selected


def render_primo_explore_tab():
    _init_state()

    st.subheader("OneSearch — Public Explore API (keyless)")
    st.caption(
        "Search CSUSB OneSearch via the Primo VE public endpoint. "
        "Export fetches FULL PNX per record (needed for RAG)."
    )

    # -------- Search controls --------
    q = st.text_input("Query", value=st.session_state.get("explore_last_q") or "ott subscriber churn")
    col1, col2 = st.columns(2)
    with col1:
        limit = st.slider("Total to fetch", 10, 200, 20, 10)
    with col2:
        page_size = st.selectbox("Per request", [10, 20, 50], index=0)

    if st.button("Search", type="primary"):
        st.session_state["explore_docs"] = []
        st.session_state["explore_briefs"] = []
        st.session_state["explore_run_id"] += 1           # invalidate old selection keys
        st.session_state["explore_last_q"] = q

        fetched, offset = 0, 0
        prog = st.progress(0, text="Searching…")
        try:
            while fetched < limit:
                batch = min(page_size, limit - fetched)
                resp = explore_search(query=q, limit=batch, offset=offset)
                docs = resp.get("docs", [])
                if not docs:
                    break
                for d in docs:
                    st.session_state["explore_docs"].append(d)
                    st.session_state["explore_briefs"].append(brief_from_doc(d))
                fetched += len(docs)
                offset += len(docs)
                prog.progress(min(100, int((fetched / max(1, limit)) * 100)), text=f"Fetched {fetched}/{limit}")
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
            # live counter
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
                # Persisted across reruns because of unique key per run
                st.checkbox("Select", key=_sel_key(i))

        # Action buttons
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
