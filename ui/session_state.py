# ui/session_state.py
"""
Session state management for the Streamlit application.
"""
import streamlit as st


def initialize_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_stage" not in st.session_state:
        st.session_state.conversation_stage = "initial"
    
    if "user_requirements" not in st.session_state:
        st.session_state.user_requirements = {
            "topic": None,
            "keywords": [],
            "resource_type": None,
            "year_range": None,
            "additional_info": None
        }
    
    if "search_results" not in st.session_state:
        st.session_state.search_results = None


def reset_session_state():
    """Reset session state for a new search."""
    st.session_state.messages = []
    st.session_state.conversation_stage = "initial"
    st.session_state.user_requirements = {
        "topic": None,
        "keywords": [],
        "resource_type": None,
        "year_range": None,
        "additional_info": None
    }
    st.session_state.search_results = None
