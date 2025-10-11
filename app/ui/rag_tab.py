# app/ui/rag_tab.py
"""
RAG tab (no user-visible knobs)
- No Top-k / α / rerank controls shown
- Uses env defaults for retrieval settings
- LLM rerank is always enabled
"""

from __future__ import annotations
import os
import streamlit as st
from typing import List, Dict, Any

from app.rag.indexer import index_jsonl
from app.rag.rag_chain import answer


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _fmt_link(meta: Dict[str, Any]) -> str:
    # try stored permalink first
    link = meta.get("permalink")
    if isinstance(link, list):
        link = link[0] if link else ""
    if link:
        return link
    # fallback Discovery fulldisplay URL
    vid = os.getenv("PRIMO_VID", "01CALS_USB:01CALS_USB")
    base = os.getenv("PRIMO_DISCOVERY_BASE", "https://csu-sb.primo.exlibrisgroup.com")
    rid = meta.get("record_id") or ""
    ctx = (meta.get("context") or "PC") or "PC"
    return f"{base}/discovery/fulldisplay?vid={vid}&context={ctx}&docid={rid}" if rid else ""

def _fmt_title(meta: Dict[str, Any]) -> str:
    return (meta.get("title") or "").strip() or "Untitled"


def render_rag_tab():
    st.subheader("RAG — Ask questions about your OneSearch corpus")
    st.caption(
        "Retrieves the best passages and answers using ONLY those. "
        "Citations point back to Primo. No model or retrieval settings are shown."
    )

    # ---- Index controls (no knobs) ----
    with st.expander("Indexing"):
        if st.button("Run indexer", type="primary"):
            with st.spinner("Indexing…"):
                info = index_jsonl()
            st.success(
                f"Indexed ✅ collection: `{info['collection']}` · "
                f"added: {info.get('added', 0)} · skipped_empty: {info.get('skipped_empty', 0)}"
            )

    st.markdown("---")

    # ---- Simple question box only ----
    q = st.text_input("Your question", placeholder="e.g., What factors drive OTT subscriber churn?")

    if st.button("Ask", type="primary", disabled=not q.strip()):
        # Hidden defaults from env
        top_k = _env_int("RAG_TOP_K", 6)
        alpha = _env_float("RAG_ALPHA", 0.7)
        rerank_topN = _env_int("RAG_RERANK_TOPN", 12)

        with st.spinner("Thinking…"):
            res = answer(
                question=q.strip(),
                top_k=top_k,
                alpha=alpha,
                use_rerank=True,         # always on
                rerank_topN=rerank_topN, # from env
                # temperature not passed; taken from GROQ_TEMPERATURE in llm_client
            )

        st.markdown("### Answer")
        st.write(res.get("answer", "") or "I couldn’t generate a response right now.")

        st.markdown("### Sources")
        hits: List[Dict[str, Any]] = res.get("hits", []) or []
        if not hits:
            st.warning("No passages retrieved. Re-run the indexer or export more records with PNX.")
        for i, h in enumerate(hits, 1):
            meta = h.get("meta", {}) or {}
            title = _fmt_title(meta)
            link = _fmt_link(meta)
            st.markdown(f"**[{i}] {title}** — {link if link else 'no link'}")
            with st.expander("Show snippet"):
                st.write(h.get("text", ""))

    st.markdown("---")
    with st.expander("Help"):
        st.markdown(
            "- Retrieval settings are fixed. To tweak them without UI, set env vars when starting the container:\n"
            "  - `RAG_TOP_K` (default `6`)\n"
            "  - `RAG_ALPHA` (default `0.7`)\n"
            "  - `RAG_RERANK_TOPN` (default `12`)\n"
            "- Model temperature is controlled by `GROQ_TEMPERATURE` (default `0.2`)."
        )
