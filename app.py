import os
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Team1F25 Chatbot", page_icon="🤖")
st.title("🤖 Team1F25 Chatbot (Full Answers)")

# --- Require API key (no fallback) ---
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key:
    st.error("❌ OPENAI_API_KEY not set in the container. Start the container with --env-file .env or -e OPENAI_API_KEY=...")
    st.stop()

client = OpenAI(api_key=api_key)

def ask_llm(message: str) -> str:
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":message}],
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"(OpenAI error: {e})"

if "history" not in st.session_state: st.session_state.history = []

msg = st.chat_input("Ask me anything…")
if msg:
    st.session_state.history.append(("You", msg))
    st.session_state.history.append(("Bot", ask_llm(msg)))

for who, text in st.session_state.history:
    st.markdown(f"**{'🧑 You' if who=='You' else '🤖 Bot'}:** {text}")
