# ui/chat_handler.py
"""
Chat interaction handler for the Streamlit application.
"""
import streamlit as st
from typing import Optional
from core.groq_client import GroqClient
from core.ai_assistant import generate_follow_up_question, extract_search_query, check_user_wants_search
from core.search_service import perform_library_search
from core.logging_utils import get_logger

logger = get_logger(__name__)


def initialize_groq_client() -> Optional[GroqClient]:
    """Initialize the Groq client for LLM interactions."""
    try:
        return GroqClient()
    except Exception as e:
        st.error(f"Failed to initialize Groq client: {e}")
        logger.error(f"Groq initialization error: {e}")
        return None


def handle_search_execution(groq_client: GroqClient, conversation_history: list):
    """Execute a library search and handle the results."""
    search_query = extract_search_query(groq_client, conversation_history)
    logger.info(f"Extracted search query: {search_query}")
    
    response_text = f"Great! Let me search for resources on: **{search_query}**\n\nSearching the library database..."
    st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Perform search
    with st.spinner("Searching library database..."):
        results = perform_library_search(search_query)
        
    if results:
        st.session_state.search_results = results
        st.rerun()
    else:
        error_msg = "I encountered an issue searching the library. Please try again or refine your search."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


def handle_user_message(prompt: str, groq_client: GroqClient):
    """Handle user message and generate appropriate response."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            conversation_history = st.session_state.messages.copy()
            
            # Check if user explicitly wants to search now
            if check_user_wants_search(prompt):
                logger.info("User explicitly requested search")
                handle_search_execution(groq_client, conversation_history)
                return
            
            # Get AI response
            ai_response = generate_follow_up_question(groq_client, conversation_history)
            logger.info(f"AI response: {ai_response}")
            
            # Check if AI is ready to search
            if "READY_TO_SEARCH" in ai_response:
                handle_search_execution(groq_client, conversation_history)
            else:
                # Continue conversation
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
