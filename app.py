import os
import requests
import streamlit as st
from dotenv import load_dotenv


# Load API key from local.env (no prompts anywhere)
load_dotenv(dotenv_path="local.env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_ID = "meta-llama/llama-3.3-8b-instruct:free"  # fixed, single model
SYSTEM_PROMPT = "You are a helpful assistant. Answer briefly and clearly."
TEMPERATURE = 0.2  # fixed, tweak here if desired


# Streamlit page setup
st.set_page_config(page_title="Simple Chatbot", page_icon="💬", layout="centered")
st.title("💬 Simple Chatbot (Llama 3.3 8B via OpenRouter)")

# Fail fast if the key isn’t present (no UI or CLI prompt)
if not OPENROUTER_API_KEY:
    st.error(
        "Missing API key.\n\n"
        "Create a file named **local.env** in the same folder as `app.py` with:\n\n"
        "`OPENROUTER_API_KEY=sk-or-...`\n\n"
        "Then restart the app."
    )
    st.stop()

# Minimal conversation state (kept in-memory per session)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Show prior turns (skip the system message)
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat input
user_msg = st.chat_input("Type your question...")


# Simple single-call helper to OpenRouter (no streaming)

def chat_once(api_key: str, model: str, messages: list[str]) -> str:
    """
    Calls OpenRouter's Chat Completions endpoint once and returns the assistant text.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": TEMPERATURE,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

# Handle a new user message
if user_msg:
    # Show the user's turn immediately
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Call the model
    try:
        reply = chat_once(OPENROUTER_API_KEY, MODEL_ID, st.session_state.messages)
    except requests.RequestException as e:
        reply = f"Request failed: {e}"

    # Show assistant reply and store it
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
