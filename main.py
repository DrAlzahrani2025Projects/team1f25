# main.py
import streamlit as st
from app.ui.chat import render_chat
from app.ui.primo_explore_tab  import render_primo_explore_tab
from app.ui.rag_tab import render_rag_tab

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")

def main():
    t1, t2, t3 = st.tabs(["Chat", "OneSearch (Explore API)", "RAG"])
    with t1: render_chat()
    with t2: render_primo_explore_tab()
    with t3: render_rag_tab()

if __name__ == "__main__":
    main()
