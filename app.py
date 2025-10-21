# app.py

from __future__ import annotations
import streamlit as st
from core.schemas import AgentInput
from agents.orchestrator_agent import handle

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Scholar AI Assistant",
    page_icon="📚",
    layout="wide"
)

# ---------------------------
# Global styles (professional look)
# ---------------------------
def apply_custom_style():
    st.markdown(
        """
        <style>
            /* Base page */
            .main {
                background-color: #f7f9fc;
                color: #1f2937;
                font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
            }

            /* Header bar */
            .custom-header {
                background: #0B5ED7;            /* Blue header */
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                text-align: center;
                font-size: 1.25rem;
                font-weight: 650;
                letter-spacing: .2px;
                box-shadow: 0 6px 18px rgba(11,94,215,0.25);
                margin-bottom: 18px;
            }

            /* Subtle cards feel for chat bubbles */
            .stChatMessage {
                border-radius: 12px !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }

            /* Chat text */
            .stChatMessage p, .stChatMessage li {
                line-height: 1.55;
                font-size: 0.98rem;
            }

            /* Input spacing */
            .stChatInput {
                margin-top: .75rem;
            }

            /* Spinner accent */
            .stSpinner > div {
                color: #0B5ED7 !important;
            }

            /* Caption style */
            .pro-caption {
                color: #4b5563;
                margin-bottom: 8px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# UI helpers
# ---------------------------
def render_header():
    apply_custom_style()
    st.markdown('<div class="custom-header">CSE6550 Team 1 AI Agent- Scholar AI Assistant</div>', unsafe_allow_html=True)
    st.caption("Welcome — try queries like **List top 10 OTT subscriber churn articles**.")

def render_history():
    for role, content in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(content)

def chat_input():
    return st.chat_input("Enter your request here...")

# ---------------------------
# App
# ---------------------------
def main():
    render_header()

    # Init session state
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    # Render history
    render_history()

    # Get prompt
    prompt = chat_input()
    if not prompt:
        return

    # User turn
    st.session_state["chat"].append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant turn
    with st.chat_message("assistant"):
        with st.spinner("Working…"):
            try:
                out = handle(AgentInput(user_input=prompt))
                reply_text = out.text
            except Exception as e:
                reply_text = f"⚠️ Sorry, something went wrong:\n\n```\n{e}\n```"
        st.markdown(reply_text)

    # Persist assistant message
    st.session_state["chat"].append(("assistant", reply_text))

if __name__ == "__main__":
    main()
