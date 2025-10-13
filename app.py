# app.py
from __future__ import annotations
import streamlit as st
from typing import List

from core.schemas import AgentInput, ArticleBrief
from agents.orchestrator_agent import handle
from agents.retrieval_agent import search_articles, export_briefs_with_pnx
from agents.embedding_agent import index_jsonl

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")


def _init_state():
    st.session_state.setdefault("chat", [])                 # [(role, content)]
    st.session_state.setdefault("pending_briefs", None)     # type: List[ArticleBrief] | None
    st.session_state.setdefault("last_export_count", 0)
    st.session_state.setdefault("last_index_stats", {})


def _render_history():
    for role, content in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(content)


def _do_feed_from_pending():
    """Export & index using the current pending briefs (if any)."""
    briefs: List[ArticleBrief] | None = st.session_state.get("pending_briefs")
    if not briefs:
        return None, None, "No results are pending export. First ask me to list some articles, or type `feed <your terms>`."
    wrote = export_briefs_with_pnx(briefs)
    stats = index_jsonl()
    st.session_state["pending_briefs"] = None
    return wrote, stats, None


def _do_feed_from_terms(terms: str, n: int = 20):
    """Search -> export -> index in one shot when user types: feed ott churn"""
    briefs = search_articles(terms, n=n, peer_reviewed=False, sort="rank")
    if not briefs:
        return 0, {"added": 0, "skipped_empty": 0}, f"No articles found for **{terms}**."
    wrote = export_briefs_with_pnx(briefs)
    stats = index_jsonl()
    return wrote, stats, None


def main():
    _init_state()

    st.subheader("Scholar AI Assistant")
    st.caption(
        "Ask me to **list** articles (English + Articles enforced). "
        "To persist them to the vector DB, type **`feed`**. "
        "You can also type **`feed your terms`** to search, export, and index in one shot."
    )

    # Render prior turns
    _render_history()

    # Chat input
    prompt = st.chat_input("Try: 'List top 10 ott subscriber churn articles' • 'What is ott churn?' • 'feed'")
    if not prompt:
        return

    # Add user message
    st.session_state["chat"].append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    lower = prompt.strip().lower()

    # --- FEED COMMANDS ---
    if lower == "feed" or lower.startswith("feed "):
        with st.chat_message("assistant"):
            with st.spinner("Feeding vector DB…"):
                # If user typed 'feed <terms>', run search->export->index; else use pending
                if lower == "feed":
                    wrote, stats, msg = _do_feed_from_pending()
                else:
                    terms = prompt.strip()[len("feed"):].strip()
                    wrote, stats, msg = _do_feed_from_terms(terms, n=20)

            if msg:
                st.markdown(msg)
                st.session_state["chat"].append(("assistant", msg))
                return

            added = (stats or {}).get("added", 0)
            skipped = (stats or {}).get("skipped_empty", 0)
            reply = (
                f"✅ Exported **{wrote or 0}** new records and indexed "
                f"`added={added}` · `skipped_empty={skipped}`."
            )
            st.markdown(reply)
            st.session_state["chat"].append(("assistant", reply))
        return

    # --- NORMAL ORCHESTRATED TURN ---
    with st.chat_message("assistant"):
        with st.spinner("Working…"):
            out = handle(AgentInput(user_input=prompt))
        st.markdown(out.text)

        # If orchestrator returned a preview list, stash it so a later `feed` will export+index
        if getattr(out, "await_export", False) and getattr(out, "briefs", None):
            st.session_state["pending_briefs"] = out.briefs
            st.caption("Type **`feed`** to export these results and index them into the vector DB.")

    st.session_state["chat"].append(("assistant", out.text))


if __name__ == "__main__":
    main()
