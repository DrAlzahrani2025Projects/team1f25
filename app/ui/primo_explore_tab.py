# app/ui/primo_explore_tab.py
import streamlit as st
from typing import List
from app.ingest.primo_explore_client import explore_search
from app.ingest.primo_schema import brief_from_doc, PrimoFull
from app.ingest.primo_store import append_records

def render_primo_explore_tab():
    st.subheader("OneSearch — Public Explore API")

    q = st.text_input("Query", value="ott subscriber churn")
    col1, col2 = st.columns(2)
    with col1:
        limit = st.slider("Total to fetch", 10, 200, 20, 10)
    with col2:
        page_size = st.selectbox("Per page", [10, 20, 50], index=0)

    if st.button("Search"):
        st.session_state["explore_results"] = []
        fetched, offset = 0, 0
        progress = st.progress(0, text="Searching…")
        while fetched < limit:
            batch = min(page_size, limit - fetched)
            resp = explore_search(query=q, limit=batch, offset=offset)
            docs = resp.get("docs", [])
            if not docs: break
            for d in docs:
                st.session_state["explore_results"].append(brief_from_doc(d))
            fetched += len(docs); offset += len(docs)
            progress.progress(min(100, int((fetched/limit)*100)), text=f"Fetched {fetched}/{limit}")
        progress.empty()

    results: List = st.session_state.get("explore_results", [])
    if results:
        st.write(f"Showing {len(results)} items")
        chosen = []
        for i, r in enumerate(results):
            with st.expander(f"{r.title or '[untitled]'}"):
                st.write(f"**Creators:** {', '.join(r.creators) if r.creators else '—'}")
                st.write(f"**Date:** {r.creation_date or '—'}")
                st.write(f"**Type:** {r.resource_type or '—'}")
                if r.permalink:
                    st.write(f"[Open record]({r.permalink})")
                if st.checkbox("Select", key=f"expl_sel_{i}"):
                    chosen.append(r)
        if st.button("Export selected → /data/primo/records.jsonl"):
            payload = [PrimoFull(brief=b, pnx={}, links={}, raw={}) for b in chosen]
            wrote = append_records(payload, dedupe=True)
            st.success(f"Exported {wrote} new records.")
