from __future__ import annotations
import streamlit as st
from core.schemas import AgentInput
from agents.orchestrator_agent import handle

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")

def main():
    st.subheader("Scholar AI Assistant (Week 1 — Orchestrator)")
    st.caption("Routes requests to the right agent. Retrieval/Embedding/RAG are stubbed this week.")

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    for role, content in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(content)

    prompt = st.chat_input("Try: 'List top 5 ott subscriber churn articles' or 'What is ott churn?'")
    if prompt:
        st.session_state["chat"].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            out = handle(AgentInput(user_input=prompt))
            st.markdown(out.text)

        st.session_state["chat"].append(("assistant", out.text))

if __name__ == "__main__":
    main()
