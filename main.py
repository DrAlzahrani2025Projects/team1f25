# main.py
import streamlit as st
from app.ui.chat import render_chat
from app.ui.primo_explore_tab import render_primo_explore_tab

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")

def main():
    tab1, tab2 = st.tabs(["Chat", "OneSearch (Explore API)"])
    with tab1:
        render_chat()
    with tab2:
        render_primo_explore_tab()

if __name__ == "__main__":
    main()
