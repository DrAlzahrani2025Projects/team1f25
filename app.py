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

# ---------- page + styling ----------
st.set_page_config(page_title="Ask anything", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.block-container { max-width: 820px; padding-top: 6vh; }
.chat-bubble { padding: 12px 16px; border-radius: 14px; margin: 6px 0; }
.user   { background: #eef3ff; }
.assistant { background: #f6f6f6; }
.msg-wrap { display: flex; }
.msg-wrap.user { justify-content: flex-end; }
.msg-wrap.assistant { justify-content: flex-start; }
h1 { font-size: 44px; }
</style>
""", unsafe_allow_html=True)

# ---------- session bootstrap ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = secrets.token_urlsafe(12)
if "messages" not in st.session_state:
    # load persisted history into memory
    st.session_state.messages = load_history(st.session_state.session_id)

# ---------- header actions ----------
col1, col2 = st.columns([1, 1])
with col1:
    st.title("What can I help with?")
with col2:
    if st.button("🆕 New chat", help="Start a fresh conversation"):
        # new session id, empty messages (keeps old chats in DB)
        st.session_state.session_id = secrets.token_urlsafe(12)
        st.session_state.messages = []
        st.rerun()

# ---------- show history ----------
for m in st.session_state.messages:
    css = "user" if m["role"] == "user" else "assistant"
    with st.container():
        st.markdown(f"<div class='msg-wrap {css}'><div class='chat-bubble {css}'>{m['content']}</div></div>", unsafe_allow_html=True)

# ---------- input form ----------
with st.form("ask_form", clear_on_submit=True):
    q = st.text_input("Ask anything", label_visibility="collapsed", placeholder="Ask anything")
    submitted = st.form_submit_button("Ask")

# ---------- on submit: call Groq with history ----------
if submitted and q.strip():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("Missing GROQ_API_KEY. Set it in your Docker run command.")
        st.stop()

    # update memory + persist user msg
    user_msg = {"role": "user", "content": q.strip()}
    st.session_state.messages.append(user_msg)
    save_message(st.session_state.session_id, "user", user_msg["content"])

    # build full conversation for the API
    messages_for_llm = [{"role": "system", "content": "You are a helpful, concise assistant."}]
    messages_for_llm.extend(st.session_state.messages)

    try:
        client = Groq(api_key=api_key)
        # Use a current Groq model (3.3-70B is the replacement for the deprecated 3.1-70B)
        model = "llama-3.3-70b-versatile"
        resp = client.chat.completions.create(
            model=model,
            messages=messages_for_llm,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        answer = f"⚠️ API error: {e}"

    asst_msg = {"role": "assistant", "content": answer}
    st.session_state.messages.append(asst_msg)
    save_message(st.session_state.session_id, "assistant", answer)

    # render last turn immediately
    st.markdown(f"<div class='msg-wrap assistant'><div class='chat-bubble assistant'>{answer}</div></div>", unsafe_allow_html=True)



