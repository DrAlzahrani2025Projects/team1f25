# ui/chat_handler.py
"""
Chat interaction handler for the Streamlit application.
"""
import streamlit as st
from typing import Optional
from core.groq_client import GroqClient
from core.ai_assistant import generate_follow_up_question, extract_search_parameters, check_user_wants_search
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


def suggest_alternative_search(groq_client: GroqClient, original_query: str) -> str:
    """Use AI to suggest alternative search terms when no results found."""
    prompt = f"""The user searched for "{original_query}" in an academic library database but got 0 results.

Suggest 2-3 alternative, broader search terms that might work better. Keep suggestions short and relevant.

Format your response as a simple list:
- suggestion 1
- suggestion 2
- suggestion 3

Example:
If user searched: "ott churn causes"
Suggest:
- customer churn
- subscriber retention
- streaming service analytics"""

    try:
        suggestions = groq_client.chat(prompt)
        return suggestions.strip()
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return "- Try using broader search terms\n- Check spelling and try synonyms"


def handle_search_execution(groq_client: GroqClient, conversation_history: list):
    """Execute a library search and handle the results."""
    # Extract search parameters (query, limit, resource_type)
    params = extract_search_parameters(groq_client, conversation_history)
    search_query = params.get("query", "research")
    limit = params.get("limit", 10)
    resource_type = params.get("resource_type")
    
    logger.info(f"Extracted parameters - query: {search_query}, limit: {limit}, type: {resource_type}")
    
    # Build response text
    response_parts = [f"Great! Let me search for"]
    if limit:
        response_parts.append(f"**{limit}**")
    if resource_type:
        response_parts.append(f"**{resource_type}s**" if limit != 1 else f"**{resource_type}**")
    else:
        response_parts.append("resources")
    response_parts.append(f"on: **{search_query}**")
    
    response_text = " ".join(response_parts) + "\n\nSearching the library database..."
    st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Perform search with parameters
    with st.spinner("Searching library database..."):
        results = perform_library_search(search_query, limit=limit, resource_type=resource_type)
        
    # Handle results
    if results is None:
        # Actual error occurred (API failure, network issue, etc.)
        error_msg = "I encountered an issue searching the library. Please try again or refine your search."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    elif len(results.get("docs", [])) == 0:
        # Search succeeded but no results found
        # Get AI suggestions for alternative searches
        suggestions = suggest_alternative_search(groq_client, search_query)
        
        no_results_msg = f"I searched the library but couldn't find any results for **'{search_query}'**"
        if resource_type:
            no_results_msg += f" (filtering by {resource_type}s)"
        no_results_msg += ".\n\n**Try these alternative searches:**\n"
        no_results_msg += suggestions
        
        st.warning("No results found")
        st.markdown(no_results_msg)
        st.session_state.messages.append({"role": "assistant", "content": no_results_msg})
    else:
        # Success - results found
        st.session_state.search_results = results
        st.rerun()


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
