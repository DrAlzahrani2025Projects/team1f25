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

# ---------- page config & styles ----------
st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
st.markdown("""
<style>
/* page width & spacing */
.block-container { max-width: 900px; padding-top: 3vh; }

/* Header row */
.header-row { display:flex; align-items:center; gap:16px; }
.header-title { font-size: 42px; font-weight: 800; margin: 0; }
.header-spacer { flex:1; }
.new-btn .stButton>button {
  border-radius: 10px; padding: 10px 14px; font-weight: 600;
}

/* Chat message spacing */
.chat-area { margin-top: 8px; }
.stChatMessage { padding-top: 6px; padding-bottom: 6px; }

/* Make input look elevated */
.stChatInputContainer { padding-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------- session bootstrap ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = secrets.token_urlsafe(12)
if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.session_id)

# ---------- header ----------
header_col = st.container()
with header_col:
    st.markdown(
        """
        <div class="header-row">
          <div class="header-title">What can I help with?</div>
          <div class="header-spacer"></div>
          <div class="new-btn">
            <!-- placeholder for button -->
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Render the button right after the HTML so it lands in the same row visually
    new_chat = st.button("🆕 New chat", key="new_chat_btn")
    if new_chat:
        st.session_state.session_id = secrets.token_urlsafe(12)
        st.session_state.messages = []
        st.rerun()

st.divider()

# ---------- chat history (only render if exists) ----------
if st.session_state.messages:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
else:
    # nice subtle hint instead of a big empty box
    st.info("Start a conversation below — your messages and replies will appear here.")

# ---------- input ----------
prompt = st.chat_input("Ask anything")
if prompt:
    # show user bubble immediately & persist
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.session_id, "user", prompt)

    # call Groq
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        with st.chat_message("assistant"):
            st.error("Missing GROQ_API_KEY (set it in Docker env or .env).")
    else:
        try:
            client = Groq(api_key=api_key)
            model = "llama-3.3-70b-versatile"  # current recommended
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful, concise assistant."}]
                         + st.session_state.messages,
                temperature=0.3,
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ API error: {e}"

        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(st.session_state.session_id, "assistant", answer)
