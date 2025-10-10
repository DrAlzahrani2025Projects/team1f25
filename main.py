# main.py
import streamlit as st
from app.ui.chat import render_chat

st.set_page_config(
    page_title="Scholar AI Assistant",
    page_icon="📚",
    layout="centered",
)

def main():
    render_chat()

if __name__ == "__main__":
    main()
