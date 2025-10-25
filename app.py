# app.py
"""
Scholar AI Assistant - Main Application Entry Point

A conversational AI chatbot that helps users discover academic resources
from the CSUSB library by understanding their research needs and presenting
results in an organized table format.
"""
import streamlit as st
from ui.session_state import initialize_session_state, reset_session_state
from ui.components import (
    render_sidebar,
    render_chat_messages,
    display_search_results_section,
    get_initial_greeting
)
from ui.chat_handler import initialize_groq_client, handle_user_message

# Configure the Streamlit page
st.set_page_config(
    page_title="Scholar AI Assistant",
    page_icon="📚",
    layout="wide"
)


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render page header
    st.title("📚 Scholar AI Assistant")
    st.markdown("*Your intelligent research companion for discovering academic resources*")
    
    # Initialize Groq client
    groq_client = initialize_groq_client()
    
    if not groq_client:
        st.warning("⚠️ Please set your GROQ_API_KEY environment variable to use this chatbot.")
        return
    
    # Render sidebar and check for new search request
    if render_sidebar():
        reset_session_state()
        st.rerun()
    
    # Display chat messages
    render_chat_messages()
    
    # Display search results if available
    display_search_results_section()
    
    # Display initial greeting if no messages
    if len(st.session_state.messages) == 0:
        initial_message = get_initial_greeting()
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
        with st.chat_message("assistant"):
            st.markdown(initial_message)
    
    # Handle chat input
    if prompt := st.chat_input("Enter your research query..."):
        handle_user_message(prompt, groq_client)


if __name__ == "__main__":
    main()
