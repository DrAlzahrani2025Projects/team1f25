# ui/chat_handler.py
import streamlit as st
from typing import Optional
from core.clients.groq_client import GroqClient
from core.services.conversation_analyzer import ConversationAnalyzer
from core.services.suggestion_service import SuggestionService
from core.utils.prompts import PromptManager
from core.services.search_service import perform_library_search
from core.utils.logging_utils import get_logger
from ui.theme import get_assistant_avatar, get_user_avatar

logger = get_logger(__name__)

# Initialize Groq client
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
        # Date filters: prefer explicit LLM-extracted params, else use sidebar selections
        date_from = params.get("date_from") if params.get("date_from") is not None else st.session_state.user_requirements.get("date_from")
        date_to = params.get("date_to") if params.get("date_to") is not None else st.session_state.user_requirements.get("date_to")
        
        logger.info(f"Search params - query: {search_query}, limit: {limit}, type: {resource_type}")

        # If user explicitly answered 'any time' previously, don't ask again
        date_any = st.session_state.user_requirements.get("date_any", False)

        # If no date information was provided, ask a clarifying question
        if date_from is None and date_to is None and not date_any:
            # use a properly pluralized resource label (default to 'articles')
            if resource_type:
                resource_label = resource_type if resource_type.endswith('s') else f"{resource_type}s"
            else:
                resource_label = "articles"

            clarifying = (
                f"When would you like the {resource_label} from? "
                "You can answer with examples like: 'last 5 years', '2015-2018', 'since 2019', '2020', or 'any time'."
            )
            logger.info(f"Requesting date clarification: {clarifying}")
            st.markdown(clarifying)
            st.session_state.messages.append({"role": "assistant", "content": clarifying})
            # store pending conversation and params so we can continue after clarification
            st.session_state.pending_conversation = conversation_history
            st.session_state.pending_search_params = params
            st.session_state.conversation_stage = "awaiting_date_range"
            return

        # If the user had indicated 'any time', clear that transient flag now
        if date_any:
            st.session_state.user_requirements.pop("date_any", None)

        # Show search message
        self._display_search_message(search_query, limit, resource_type)

        # Perform search with progress bar
        import time
        import threading
        
        progress_text = "Searching library database..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Thread-safe storage for search results
        search_data = {"done": False, "results": None}
        
        def perform_search():
            search_data["results"] = perform_library_search(
                search_query, limit=limit, resource_type=resource_type, 
                date_from=date_from, date_to=date_to
            )
            search_data["done"] = True
        
        # Start search in background thread
        search_thread = threading.Thread(target=perform_search)
        search_thread.start()
        
        # Animate progress bar while search is running
        progress = 0
        while not search_data["done"]:
            progress = min(progress + 10, 90)  # Cap at 90% until complete
            progress_bar.progress(progress, text=progress_text)
            time.sleep(0.2)
        
        # Complete the progress bar
        progress_bar.progress(100, text="Search complete!")
        search_thread.join()
        time.sleep(0.3)  # Brief pause to show completion
        progress_bar.empty()  # Remove progress bar
        
        results = search_data["results"]

        # Handle results
        self._handle_search_results(results, search_query, resource_type)
    # Display search initiation message
    def _display_search_message(self, query: str, limit: int, resource_type: Optional[str]):
        """Display search initiation message."""
        parts = ["Great! Let me search for"]
        
        if limit:
            parts.append(f"**{limit}**")
        
        if resource_type:
            # avoid doubling an 's' if the resource_type is already plural
            base = resource_type if resource_type.endswith('s') else f"{resource_type}s"
            type_text = f"**{base}**" if limit != 1 else f"**{resource_type}**"
            parts.append(type_text)
        else:
            parts.append("resources")
        
        parts.append(f"on: **{query}**")
        
        message = " ".join(parts) + "\n\nSearching the library database..."
        logger.info(f"AI search message: {message}")
        st.markdown(message)
        st.session_state.messages.append({"role": "assistant", "content": message})
    
    def _handle_search_results(self, results, query: str, resource_type: Optional[str]):
        """Handle search results - success, no results, or error."""
        if results is None:
            # API error
            logger.error(f"Search API error for query: {query}")
            self._handle_search_error()
        elif len(results.get("docs", [])) == 0:
            # No results found
            logger.info(f"No results found for query: {query}, resource_type: {resource_type}")
            self._handle_no_results(query, resource_type)
        else:
            # Success
            doc_count = len(results.get("docs", []))
            logger.info(f"Search successful: Found {doc_count} results for query: {query}")
            st.session_state.search_results = results
            st.rerun()
    
    def _handle_search_error(self):
        """Handle search API errors."""
        error_msg = "I encountered an issue searching the library. Please try again or refine your search."
        logger.error(f"Search error response sent to user: {error_msg}")
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    def _handle_no_results(self, query: str, resource_type: Optional[str]):
        """Handle when no results are found."""
        logger.info(f"Generating search suggestions for: {query}")
        suggestions = self.suggestion_service.generate_suggestions(query)
        
        message = f"I searched the library but couldn't find any results for **'{query}'**"
        if resource_type:
            message += f" (filtering by {resource_type}s)"
        message += ".\n\n**Try these alternative searches:**\n"
        message += suggestions
        
        logger.info(f"AI no-results message with suggestions: {message[:100]}...")
        st.warning("No results found")
        st.markdown(message)
        st.session_state.messages.append({"role": "assistant", "content": message})


def handle_user_message(prompt: str, groq_client: GroqClient):
    """
    Handle user message and generate appropriate response.
    Simplified to delegate to ChatOrchestrator.
    """
    # Log user message
    logger.info(f"User message: {prompt}")
    
    # Create orchestrator
    orchestrator = ChatOrchestrator(groq_client)

    # If we're awaiting a date range clarification, treat this message as the date answer
    if st.session_state.get("conversation_stage") == "awaiting_date_range":
        logger.info("Processing date range clarification response")
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=get_user_avatar()):
            st.markdown(prompt)

        # Parse the user's short reply for dates using the analyzer heuristics
        date_params = orchestrator.analyzer.extract_date_parameters(prompt)

        # If the user explicitly answered 'any time' (or similar), mark it so we don't re-ask
        lower = prompt.strip().lower()
        any_time_patterns = ["any time", "anytime", "no time", "no preference", "no date", "don't care", "dont care"]
        is_any = any(p in lower for p in any_time_patterns)
        if is_any:
            st.session_state.user_requirements["date_from"] = None
            st.session_state.user_requirements["date_to"] = None
            st.session_state.user_requirements["date_any"] = True
        else:
            # Update session-level user requirements so execute_search can pick them up
            if "date_from" in date_params:
                st.session_state.user_requirements["date_from"] = date_params.get("date_from")
            if "date_to" in date_params:
                st.session_state.user_requirements["date_to"] = date_params.get("date_to")

        # reset awaiting state and resume the pending search
        pending_conv = st.session_state.pop("pending_conversation", None)
        st.session_state.pop("pending_search_params", None)
        st.session_state.conversation_stage = "initial"

        # Resume the search using the stored pending conversation context
        with st.chat_message("assistant", avatar=get_assistant_avatar()):
            orchestrator.execute_search(pending_conv or st.session_state.messages.copy())
        return

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=get_user_avatar()):
        st.markdown(prompt)

    # Process message
    with st.chat_message("assistant", avatar=get_assistant_avatar()):
        import time
        import threading
        
        conversation_history = st.session_state.messages.copy()

        # Check if trigger keywords present (indicates intent to search)
        has_trigger = orchestrator.analyzer.should_trigger_search(prompt)
        if has_trigger:
            logger.info("Trigger keyword detected - checking if query is complete")
        
        # Show progress bar while getting AI response
        progress_text = "Thinking..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Thread-safe storage for AI response
        response_data = {"done": False, "response": None}
        
        def get_ai_response():
            response_data["response"] = orchestrator.get_conversation_response(conversation_history)
            response_data["done"] = True
        
        # Start AI processing in background thread
        response_thread = threading.Thread(target=get_ai_response)
        response_thread.start()
        
        # Animate progress bar while AI is thinking
        progress = 0
        while not response_data["done"]:
            progress = min(progress + 15, 85)  # Cap at 85% until complete
            progress_bar.progress(progress, text=progress_text)
            time.sleep(0.15)
        
        # Complete the progress bar
        progress_bar.progress(100, text="Done!")
        response_thread.join()
        time.sleep(0.2)  # Brief pause to show completion
        progress_bar.empty()  # Remove progress bar
        
        ai_response = response_data["response"]
        logger.info(f"AI response: {ai_response}")

        # Check if ready to search
        if "READY_TO_SEARCH" in ai_response:
            logger.info("AI indicated READY_TO_SEARCH - executing search")
            orchestrator.execute_search(conversation_history)
        else:
            # Continue conversation (ask for clarification)
            logger.info(f"AI continuing conversation with follow-up question")
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})


# Legacy function kept for backward compatibility
def suggest_alternative_search(groq_client: GroqClient, original_query: str) -> str:
    """Legacy function - delegates to SuggestionService."""
    prompt_manager = PromptManager()
    service = SuggestionService(groq_client, prompt_manager)
    return service.generate_suggestions(original_query)
