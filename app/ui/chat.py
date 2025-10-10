# app/ui/chat.py
import streamlit as st
from app.core.llm_client import GroqLLM

SYSTEM_PROMPT = (
    "You are Scholar AI Assistant. "
    "Be helpful, concise, and avoid external browsing. "
    "This is a demo chat hooked to Groq."
)

def render_chat():
    st.title("Team1f25 Scholar AI Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Sidebar controls
    with st.sidebar:
        st.subheader("Model settings")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05)
        max_tokens = st.slider("Max tokens", 128, 4096, 1024, 64)
        model_override = st.text_input(
            "Model (optional)", placeholder="llama-3.3-70b-versatile"
        )
        st.markdown("---")
        st.caption("Set GROQ_API_KEY via `-e GROQ_API_KEY=...` when running Docker.")

    # Show chat history (system hidden)
    for m in st.session_state.messages:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_text = st.chat_input("Ask me anything about research…")
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            llm = GroqLLM(model=model_override or None)
            placeholder = st.empty()
            acc = ""
            for token in llm.chat(
                st.session_state.messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            ):
                acc += token
                placeholder.markdown(acc)
            st.session_state.messages.append({"role": "assistant", "content": acc})
