# main.py (snippet)
import streamlit as st
from app.ui.assistant_tab import render_assistant_tab

st.set_page_config(page_title="Scholar AI Assistant", page_icon="📚", layout="wide")

def main():
    render_assistant_tab()

if __name__ == "__main__":
    main()
