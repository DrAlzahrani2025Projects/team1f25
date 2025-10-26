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
            # date filters stored as YYYYMMDD ints or None
            "date_from": None,
            "date_to": None,
            "quick_date_filter": None,
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
        # Keep date fields for compatibility
        "date_from": None,
        "date_to": None,
        "quick_date_filter": None,
        "additional_info": None
    }
    st.session_state.search_results = None

    # track whether filters are active
    if "filters_active" not in st.session_state:
        st.session_state.filters_active = False
    st.session_state.filters_active = False
    # pending conversation params used when clarifying date ranges
    if "pending_conversation" in st.session_state:
        st.session_state.pop("pending_conversation", None)
    if "pending_search_params" in st.session_state:
        st.session_state.pop("pending_search_params", None)
