from __future__ import annotations
import streamlit as st
from core.schemas import AgentInput
from agents.orchestrator_agent import handle
from agents.retrieval_agent import export_briefs_with_pnx  # <— use for the button/command

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")

def main():
    st.subheader("Scholar AI Assistant (Preview → Export)")
    st.caption("Lists show titles + permalinks first. Export only when you click the button or type 'export'.")

    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "pending_briefs" not in st.session_state:
        st.session_state["pending_briefs"] = None  # stash last list for export

    # render history
    for role, content in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(content)

    # export command via chat
    prompt = st.chat_input("Try: 'List top 10 ott subscriber churn articles' or type 'export' after listing")
    if prompt:
        # If user typed 'export' and we have pending briefs -> export now
        if prompt.strip().lower() in {"export", "export all", "export these", "save"} and st.session_state["pending_briefs"]:
            briefs = st.session_state["pending_briefs"]
            with st.chat_message("assistant"):
                with st.spinner("Exporting selected results to JSONL…"):
                    wrote = export_briefs_with_pnx(briefs)
                st.markdown(f"✅ Exported **{wrote}** new records to `/data/primo/records.jsonl`.")
            st.session_state["chat"].append(("assistant", f"Exported {wrote} new records to /data/primo/records.jsonl."))
            st.session_state["pending_briefs"] = None
        else:
            # normal flow: handle prompt
            st.session_state["chat"].append(("user", prompt))
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                out = handle(AgentInput(user_input=prompt))
                st.markdown(out.text)

                # If this is a LIST preview, stash briefs and show an export button
                if out.await_export and out.briefs:
                    st.session_state["pending_briefs"] = out.briefs
                    if st.button("Export these results → /data/primo/records.jsonl"):
                        with st.spinner("Exporting to JSONL…"):
                            wrote = export_briefs_with_pnx(out.briefs)
                        st.success(f"Exported **{wrote}** new records to `/data/primo/records.jsonl`.")
                        st.session_state["pending_briefs"] = None

            st.session_state["chat"].append(("assistant", out.text))

if __name__ == "__main__":
    main()
