import os, sqlite3, secrets, datetime as dt
import streamlit as st
from groq import Groq

DB_PATH = "data/chat.db"

# ---------- persistence helpers ----------
def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts TEXT NOT NULL
        )""")
        conn.commit()

def load_history(session_id):
    ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM chats WHERE session=? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    return [{"role": r, "content": c} for (r, c) in rows]

def save_message(session_id, role, content):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO chats(session, role, content, ts) VALUES(?,?,?,?)",
            (session_id, role, content, dt.datetime.utcnow().isoformat())
        )
        conn.commit()

# ---------- page config ----------
st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")

# minimal styling to center and spacious chat area
st.markdown("""
<style>
.block-container { max-width: 900px; padding-top: 3vh; }
.chat-wrap { border: 1px solid #eee; border-radius: 14px; padding: 12px; min-height: 60vh; }
h1 { margin-bottom: 6px; }
.topbar { display:flex; justify-content:space-between; align-items:center; }
</style>
""", unsafe_allow_html=True)

# ---------- session bootstrap ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = secrets.token_urlsafe(12)
if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.session_id)

# ---------- header ----------
col_a, col_b = st.columns([1, 1])
with col_a:
    st.markdown("<div class='topbar'><h1>What can I help with?</h1></div>", unsafe_allow_html=True)
with col_b:
    if st.button("🆕 New chat", use_container_width=True):
        st.session_state.session_id = secrets.token_urlsafe(12)
        st.session_state.messages = []
        st.rerun()

# ---------- chat history (true chat UI) ----------
with st.container():
    st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
    # stream history as chat bubbles
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- chat input at the bottom ----------
prompt = st.chat_input("Ask anything")

if prompt:
    # show user bubble immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.session_id, "user", prompt)

    # call Groq with full context
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        with st.chat_message("assistant"):
            st.error("Missing GROQ_API_KEY (set it in Docker env or .env).")
    else:
        try:
            client = Groq(api_key=api_key)
            model = "llama-3.3-70b-versatile"
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful, concise assistant."}] +
                         st.session_state.messages,
                temperature=0.3,
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ API error: {e}"

        # show assistant bubble + persist
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(st.session_state.session_id, "assistant", answer)

