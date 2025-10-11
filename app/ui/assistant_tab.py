# app/ui/assistant_tab.py
from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List
from app.graph.assistant_graph import run_assistant

def _init_state():
    st.session_state.setdefault("assistant_chat", [])

def _render_sources_from_answer_state(state: Dict[str, Any]):
    # If the graph answered via RAG, we can optionally render sources here.
    hits: List[Dict[str, Any]] = state.get("hits") or []
    if not hits:
        return
    st.markdown("### Sources")
    for i, h in enumerate(hits, 1):
        m = h.get("meta", {}) or {}
        title = (m.get("title") or "Untitled").strip()
        link = m.get("permalink")
        if isinstance(link, list):
            link = link[0] if link else ""
        link = link or m.get("link") or ""
        st.markdown(f"**[{i}] {title}** — {link if link else 'no link'}")
        with st.expander("Show snippet"):
            st.write(h.get("text", ""))

def render_assistant_tab():
    _init_state()
    st.subheader("Scholar AI Assistant Chatbot")
    st.caption("One tab that can search, export+index, and answer — orchestrated by LangGraph. (English + Articles enforced)")

    # Show conversation (simple)
    for role, content in st.session_state["assistant_chat"]:
        with st.chat_message(role):
            st.markdown(content)

    if prompt := st.chat_input("Ask me anything research-related…"):
        st.session_state["assistant_chat"].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Working…"):
                state = run_assistant(prompt)
            reply = state.get("response_markdown") or "I couldn’t produce a response."
            st.markdown(reply)
            # Optional: show sources if this was a RAG answer
            _render_sources_from_answer_state(state)
        st.session_state["assistant_chat"].append(("assistant", reply))
