# app/ui/rag_tab.py
"""
RAG tab (Sprint 4, rerank always ON)
- Indexes your OneSearch corpus (/data/primo/records.jsonl) into ChromaDB (/data/chroma)
- Hybrid retrieval (dense + keyword) with α slider
- LLM rerank (Groq) is ALWAYS enabled over top-N
- Answers with numbered citations and viewable snippets
"""

from __future__ import annotations
import os
import streamlit as st
from typing import List, Dict, Any

from app.rag.indexer import index_jsonl
from app.rag.rag_chain import answer


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
        "Indexes `/data/primo/records.jsonl` into `/data/chroma`, retrieves the best passages, "
        "and answers using ONLY those passages. Citations point back to Primo. "
        "**LLM rerank is always enabled.**"
    )

    # ---- Index controls ----
    with st.expander("Indexing"):
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Run indexer", type="primary", help="Build / refresh the Chroma index from JSONL"):
                with st.spinner("Indexing…"):
                    info = index_jsonl()
                st.success(
                    f"Indexed ✅  collection: `{info['collection']}`  "
                    f"added: {info.get('added', 0)}  "
                    f"skipped_empty: {info.get('skipped_empty', 0)}  "
                    f"path: {info['path']}"
                )
        with c2:
            if st.button("Show corpus tips"):
                st.info(
                    "Make sure your JSONL has PNX (abstract/subjects). "
                    "Use the OneSearch tab’s Export (with PNX fallback) or the CLI ingester."
                )
        with c3:
            st.caption(
                f"DATA_DIR: `{os.getenv('DATA_DIR','/data')}` · "
                f"Collection: `{os.getenv('CHROMA_COLLECTION','csusb_primo')}`"
            )

    st.markdown("---")

    # ---- Query controls ----
    q = st.text_input("Your question", placeholder="e.g., What factors drive OTT subscriber churn?")

    c1, c2, c3 = st.columns(3)
    with c1:
        top_k = st.slider("Top-k passages", 3, 12, 6, 1)
    with c2:
        alpha = st.slider("Hybrid α (dense ↔ keyword)", 0.0, 1.0, 0.7, 0.05,
                          help="0 = keyword only, 1 = dense only; default blends both")
    with c3:
        rerank_topN = st.selectbox("LLM rerank top-N (always on)", [8, 10, 12, 15, 20], index=2)

    temp = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)

    # ---- Ask ----
    if st.button("Ask", type="primary", disabled=not q.strip()):
        with st.spinner("Thinking…"):
            res = answer(
                question=q.strip(),
                top_k=top_k,
                alpha=alpha,
                use_rerank=True,            # <- always enabled
                rerank_topN=rerank_topN,    # user can still pick top-N
                temperature=temp,
            )

        st.markdown("### Answer")
        st.write(res.get("answer", ""))

        # ---- Sources / Diagnostics ----
        st.markdown("### Sources")
        hits: List[Dict[str, Any]] = res.get("hits", []) or []
        if not hits:
            st.warning("No passages retrieved. Re-run the indexer or export more records with PNX.")
        for i, h in enumerate(hits, 1):
            meta = h.get("meta", {}) or {}
            title = _fmt_title(meta)
            link = _fmt_link(meta)

            # Score readout (hybrid / dense / kw if present; rerank score is not exposed in chain by default)
            score_bits = []
            if "hybrid" in h:
                score_bits.append(f"hybrid={h['hybrid']:.3f}")
            if "dense_sim" in h:
                score_bits.append(f"dense={h['dense_sim']:.3f}")
            if "kw" in h:
                score_bits.append(f"kw={h['kw']:.3f}")
            if "rerank" in h:
                score_bits.append(f"rerank={h['rerank']:.1f}")
            score_str = " · ".join(score_bits)

            st.markdown(f"**[{i}] {title}** — {link if link else 'no link'}")
            if score_str:
                st.caption(score_str)

            with st.expander("Show snippet"):
                st.write(h.get("text", ""))

    st.markdown("---")
    with st.expander("Help"):
        st.markdown(
            "- **LLM rerank is always on** to maximize precision on the final set of passages.\n"
            "- Tune **α**: start at 0.7; slide toward 0.5 if keyword overlap helps your queries.\n"
            "- Increase **rerank top-N** (e.g., 15–20) if relevant passages aren’t bubbling up, "
            "noting it adds a bit more LLM latency."
        )