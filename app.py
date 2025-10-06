import os
import json
import requests
import streamlit as st

# --- Config ---
st.set_page_config(page_title="Team1f25 LLM Chat", page_icon="💬", layout="centered")

# Environment + defaults
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "llama3.1:8b")

# --- Sidebar controls ---
with st.sidebar:
    st.title("⚙️ Settings")
    model = st.text_input(
        "Model",
        value=DEFAULT_MODEL,
        help="Must be pulled in your Ollama instance (e.g., llama3.1:8b, mistral:7b, phi3:mini)."
    )
    st.markdown("---")
    st.caption(f"🔌 Ollama endpoint: `{OLLAMA_URL}`")
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.experimental_rerun()

# --- Session state for chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Team1f25 LLM Chat")
st.caption("Backed by a locally running open-source model via Ollama. Your messages stay on your machine.")

# --- Render chat history ---
for m in st.session_state.messages:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"])

# --- Chat input ---
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Placeholder for streaming assistant response
    with st.chat_message("assistant"):
        resp_area = st.empty()
        full_text = ""

        try:
            payload = {
                "model": model,
                "messages": st.session_state.messages,
                "stream": True
            }
            url = f"{OLLAMA_URL}/api/chat"
            # Stream JSON lines from Ollama
            with requests.post(url, json=payload, stream=True, timeout=600) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content_piece = data.get("message", {}).get("content", "")
                    if content_piece:
                        full_text += content_piece
                        resp_area.markdown(full_text)
                    if data.get("done"):
                        break
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()

        # Save final assistant message
        st.session_state.messages.append({"role": "assistant", "content": full_text})
