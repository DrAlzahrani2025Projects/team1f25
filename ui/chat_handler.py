# ui/chat_handler.py
"""
Chat interaction handler for the Streamlit application.
Refactored to follow SOLID principles (SRP, DIP, KISS).
"""
import streamlit as st
from typing import Optional
from core.groq_client import GroqClient
from core.conversation_analyzer import ConversationAnalyzer
from core.suggestion_service import SuggestionService
from core.prompts import PromptManager
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


class ChatOrchestrator:
    """
    Orchestrates chat interactions by delegating to specialized services.
    Follows SRP - coordinates but doesn't implement business logic.
    """
    
    def __init__(self, llm_client: GroqClient):
        """Initialize with dependencies."""
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.analyzer = ConversationAnalyzer(llm_client, self.prompt_manager)
        self.suggestion_service = SuggestionService(llm_client, self.prompt_manager)
    
    def should_search(self, user_input: str, conversation_history: list) -> bool:
        """Determine if a search should be triggered."""
        # Check explicit user request
        if self.analyzer.should_trigger_search(user_input):
            logger.info("User explicitly requested search")
            return True
        
        # Check AI readiness
        ai_response = self.analyzer.get_follow_up_response(conversation_history)
        return "READY_TO_SEARCH" in ai_response
    
    def get_conversation_response(self, conversation_history: list) -> str:
        """Get AI response for continuing conversation."""
        return self.analyzer.get_follow_up_response(conversation_history)
    
    def execute_search(self, conversation_history: list):
        """Execute search and handle results."""
        # Extract parameters
        params = self.analyzer.extract_search_parameters(conversation_history)
        search_query = params.get("query", "research")
        limit = params.get("limit", 10)
        resource_type = params.get("resource_type")
        
        logger.info(f"Search params - query: {search_query}, limit: {limit}, type: {resource_type}")
        
        # Show search message
        self._display_search_message(search_query, limit, resource_type)
        
        # Perform search
        with st.spinner("Searching library database..."):
            results = perform_library_search(search_query, limit=limit, resource_type=resource_type)
        
        # Handle results
        self._handle_search_results(results, search_query, resource_type)
    
    def _display_search_message(self, query: str, limit: int, resource_type: Optional[str]):
        """Display search initiation message."""
        parts = ["Great! Let me search for"]
        
        if limit:
            parts.append(f"**{limit}**")
        
        if resource_type:
            type_text = f"**{resource_type}s**" if limit != 1 else f"**{resource_type}**"
            parts.append(type_text)
        else:
            parts.append("resources")
        
        parts.append(f"on: **{query}**")
        
        message = " ".join(parts) + "\n\nSearching the library database..."
        st.markdown(message)
        st.session_state.messages.append({"role": "assistant", "content": message})
    
    def _handle_search_results(self, results, query: str, resource_type: Optional[str]):
        """Handle search results - success, no results, or error."""
        if results is None:
            # API error
            self._handle_search_error()
        elif len(results.get("docs", [])) == 0:
            # No results found
            self._handle_no_results(query, resource_type)
        else:
            # Success
            st.session_state.search_results = results
            st.rerun()
    
    def _handle_search_error(self):
        """Handle search API errors."""
        error_msg = "I encountered an issue searching the library. Please try again or refine your search."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    def _handle_no_results(self, query: str, resource_type: Optional[str]):
        """Handle when no results are found."""
        suggestions = self.suggestion_service.generate_suggestions(query)
        
        message = f"I searched the library but couldn't find any results for **'{query}'**"
        if resource_type:
            message += f" (filtering by {resource_type}s)"
        message += ".\n\n**Try these alternative searches:**\n"
        message += suggestions
        
        st.warning("No results found")
        st.markdown(message)
        st.session_state.messages.append({"role": "assistant", "content": message})


def handle_user_message(prompt: str, groq_client: GroqClient):
    """
    Handle user message and generate appropriate response.
    Simplified to delegate to ChatOrchestrator.
    """
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Create orchestrator
    orchestrator = ChatOrchestrator(groq_client)
    
    # Process message
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            conversation_history = st.session_state.messages.copy()
            
            # Check if should search
            if orchestrator.analyzer.should_trigger_search(prompt):
                orchestrator.execute_search(conversation_history)
                return
            
            # Get AI response
            ai_response = orchestrator.get_conversation_response(conversation_history)
            logger.info(f"AI response: {ai_response}")
            
            # Check if ready to search
            if "READY_TO_SEARCH" in ai_response:
                orchestrator.execute_search(conversation_history)
            else:
                # Continue conversation
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})


# Legacy function kept for backward compatibility
def suggest_alternative_search(groq_client: GroqClient, original_query: str) -> str:
    """Legacy function - delegates to SuggestionService."""
    prompt_manager = PromptManager()
    service = SuggestionService(groq_client, prompt_manager)
    return service.generate_suggestions(original_query)

