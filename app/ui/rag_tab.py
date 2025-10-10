# app/ui/rag_tab.py
import streamlit as st
from app.rag.indexer import index_jsonl
from app.rag.rag_chain import answer

def render_rag_tab():
    st.subheader("RAG — Ask questions about your OneSearch corpus")
    st.caption("Indexes /data/primo/records.jsonl into /data/chroma and answers with citations.")

    with st.expander("Build / Refresh Index"):
        if st.button("Run indexer"):
            with st.spinner("Indexing…"):
                info = index_jsonl()
            st.success(f"Indexed to {info['path']} (collection: {info['collection']})")

    q = st.text_input("Your question", placeholder="e.g., What factors drive OTT subscriber churn?")
    col1, col2 = st.columns(2)
    with col1:
        k = st.slider("Top-k passages", 3, 12, 6, 1)
    with col2:
        temp = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)

    if st.button("Ask"):
        with st.spinner("Thinking…"):
            res = answer(q, top_k=k, temperature=temp)
        st.markdown("### Answer")
        st.write(res["answer"])

        st.markdown("### Sources")
        for i, h in enumerate(res["hits"], 1):
            m = h["meta"]
            title = m.get("title") or "Untitled"
            link = m.get("permalink", [""])[0] if isinstance(m.get("permalink"), list) else (m.get("permalink") or "")
            st.markdown(f"**[{i}] {title}** — {link}")
            st.caption(f"score: {h['score']:.4f} · chunk: {m.get('chunk_index')}")
