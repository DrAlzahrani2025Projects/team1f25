# app/ui/chat.py
from __future__ import annotations
import streamlit as st
from app.core.llm_client import GroqLLM

SYSTEM_PROMPT = (
    "You are Scholar AI Assistant. Be concise, cite sources when provided, "
    "and help with academic/research tasks."
)

def _init_state():
    st.session_state.setdefault("chat_history", [
        {"role": "system", "content": SYSTEM_PROMPT}
    ])

def render_chat():
    _init_state()
    st.subheader("Chat")
    st.caption("Ask research questions, drafting help, or workflow tips. (Model settings are hidden.)")

    # display history (skip system)
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your message…"):
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                llm = GroqLLM()
                # send last ~20 turns to keep context light
                history = st.session_state["chat_history"][-20:]
                out = llm.chat(history, stream=False)
                if not (out or "").strip():
                    out = "I couldn’t generate a response right now."
            except Exception as e:
                out = f"(LLM error: {e})"
            st.markdown(out)

        st.session_state["chat_history"].append({"role": "assistant", "content": out})
