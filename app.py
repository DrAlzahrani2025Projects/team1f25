# app.py
import os
import json
import uuid
import requests
import streamlit as st

# ---------------- Config ----------------
# Default to host.docker.internal to avoid Docker DNS issues on Windows.
# You can switch to "http://ollama:11434" if you put both containers on the same user-defined network.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # smaller = faster
TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT_SECS", "180"))

st.set_page_config(page_title="Team1F25 + Ollama", page_icon="🤖")
st.title("🤖 Team1F25 + Ollama (Streaming + Fast Mode)")

# --------------- Sidebar ----------------
with st.sidebar:
    st.subheader("Connection")
    st.write("**OLLAMA_HOST:**", OLLAMA_HOST)
    st.write("**MODEL:**", MODEL)

    FAST_MODE = st.toggle("⚡ Fast mode", value=True, help="Smaller context + shorter replies for speed")
    if FAST_MODE:
        SPEEDY_OPTIONS = {
            "num_predict": 192,    # cap output length for speed
            "num_ctx": 896,        # smaller context → faster
            "temperature": 0.6,
            "top_k": 30,
            "top_p": 0.9,
            "repeat_penalty": 1.08,
        }
    else:
        SPEEDY_OPTIONS = {
            "num_predict": 512,
            "num_ctx": 2048,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.95,
            "repeat_penalty": 1.1,
        }

    KEEP_ALIVE = "1h"  # keep model loaded between calls (faster next response)

    if st.button("🧹 Clear chat"):
        for k in ("history", "last_input_id"):
            st.session_state.pop(k, None)
        st.rerun()

# --------------- State Init -------------
if "history" not in st.session_state:
    # One system prompt (keep short to speed up)
    st.session_state.history = [
        {"role": "system", "content": "You are a helpful, concise assistant."}
    ]
if "last_input_id" not in st.session_state:
    st.session_state.last_input_id = None  # prevents duplicate replies on rerun

# -------- Render previous messages ------
for m in st.session_state.history[1:]:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"])

# ------------- Ollama helpers -----------
def _stream_chat(messages):
    """Stream from /api/chat (newer Ollama)."""
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "options": SPEEDY_OPTIONS,
        "keep_alive": KEEP_ALIVE,
    }
    with requests.post(url, json=payload, stream=True, timeout=TIMEOUT) as r:
        if r.status_code == 404:
            raise FileNotFoundError("chat_endpoint_missing")
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            token = data.get("message", {}).get("content", "")
            if token:
                yield token

def _flatten(messages):
    parts = []
    # Optionally include only recent turns to speed up (keep last 6 turns)
    recent = messages[-12:] if len(messages) > 12 else messages
    for m in recent:
        role, content = m["role"], m["content"]
        if role == "system": parts.append(f"System: {content}")
        elif role == "user": parts.append(f"User: {content}")
        elif role == "assistant": parts.append(f"Assistant: {content}")
    parts.append("Assistant:")
    return "\n".join(parts)

def _stream_generate(messages):
    """Stream from /api/generate (fallback for older servers)."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL,
        "prompt": _flatten(messages),
        "stream": True,
        "options": SPEEDY_OPTIONS,
        "keep_alive": KEEP_ALIVE,
    }
    with requests.post(url, json=payload, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            token = data.get("response", "")
            if token:
                yield token

def stream_reply(messages):
    """Try /api/chat then fallback to /api/generate, yielding tokens."""
    try:
        for tok in _stream_chat(messages):
            yield tok
        return
    except FileNotFoundError:
        pass
    except requests.HTTPError as e:
        st.error(f"/api/chat {e.response.status_code}: {e.response.text[:400]}")
        return

    try:
        for tok in _stream_generate(messages):
            yield tok
    except requests.HTTPError as e:
        st.error(f"/api/generate {e.response.status_code}: {e.response.text[:400]}")

# ------------- Input + streaming --------
user_text = st.chat_input("Ask me anything…")
this_input_id = str(uuid.uuid4()) if user_text else None

# Only respond once per new user input (prevents duplicate replies on rerun)
if user_text and this_input_id != st.session_state.last_input_id:
    st.session_state.last_input_id = this_input_id

    # Record user turn
    st.session_state.history.append({"role": "user", "content": user_text})

    # Stream assistant reply live
    with st.chat_message("assistant"):
        placeholder = st.empty()
        assembled = ""
        for chunk in stream_reply(st.session_state.history):
            if chunk:
                assembled += chunk
                placeholder.markdown(assembled + "▌")
        placeholder.markdown(assembled or "_(no response)_")

    # Save assistant turn
    st.session_state.history.append({"role": "assistant", "content": assembled if 'assembled' in locals() else ""})
