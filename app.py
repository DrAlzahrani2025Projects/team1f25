# app.py
from __future__ import annotations
import streamlit as st
from core.schemas import AgentInput
from agents.orchestrator_agent import handle

st.set_page_config(page_title="Scholar Article Lister", page_icon="📚", layout="wide")

def main():
    st.subheader("Scholar Article Lister")
    st.caption("Type queries like: **List top 10 climate change articles**")

    # Initialize chat with a friendly first-time greeting
    if "chat" not in st.session_state:
        st.session_state["chat"] = [("assistant", "Hi, how can I help you?")]

    # Render history
    for role, content in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(content)

    prompt = st.chat_input("Enter your request here...")
    if not prompt:
        return

    # User turn
    st.session_state["chat"].append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Single call to orchestrator (LIST only)
    with st.chat_message("assistant"):
        with st.spinner("Working…"):
            out = handle(AgentInput(user_input=prompt))
        st.markdown(out.text)

    st.session_state["chat"].append(("assistant", out.text))

if __name__ == "__main__":
    main()
