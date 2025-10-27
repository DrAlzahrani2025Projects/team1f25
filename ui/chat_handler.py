# ui/chat_handler.py
"""
Chat interaction handler for the Streamlit application.
Refactored to follow SOLID principles (SRP, DIP, KISS).
"""
import streamlit as st
import re
from typing import Optional
from core.clients.groq_client import GroqClient
from core.services.conversation_analyzer import ConversationAnalyzer
from core.services.suggestion_service import SuggestionService
from core.utils.prompts import PromptManager
from core.services.search_service import perform_library_search
from core.utils.logging_utils import get_logger

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
        
    def execute_search_with_params(self, params: dict):
        """Execute search with given parameters."""
        search_query = params.get("query", "research")
        limit = params.get("limit", 10)
        resource_type = params.get("resource_type")
        peer_reviewed_only = params.get("peer_reviewed_only", False)
        
        logger.info(f"Search params - query: {search_query}, limit: {limit}, type: {resource_type}, peer_reviewed: {peer_reviewed_only}")
        
        # Show search message
        self._display_search_message(search_query, limit, resource_type, peer_reviewed_only)
        
        # Perform search
        with st.spinner("Searching library database..."):
            results = perform_library_search(
                search_query, 
                limit=limit, 
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only
            )
            
        # Handle results
        self._handle_search_results(results, search_query, resource_type)
    
    def should_search(self, user_input: str, conversation_history: list) -> bool:
        """Determine if a search should be triggered."""
        # Check explicit user request
        if self.analyzer.should_trigger_search(user_input):
            logger.info("User explicitly requested search")
            return True
            
        # Check if this is a follow-up to a resource type question
        if len(conversation_history) >= 2:
            last_assistant = conversation_history[-2]["content"].lower() if conversation_history[-2]["role"] == "assistant" else ""
            if ("what type of" in last_assistant or "what kind of" in last_assistant) and "resources" in last_assistant:
                logger.info("Resource type provided, ready to search")
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
        peer_reviewed_only = params.get("peer_reviewed_only", False)
        
        logger.info(f"Search params - query: {search_query}, limit: {limit}, type: {resource_type}, peer_reviewed: {peer_reviewed_only}")
        
        # Show search message
        self._display_search_message(search_query, limit, resource_type, peer_reviewed_only)
        
        # Perform search
        with st.spinner("Searching library database..."):
            results = perform_library_search(
                search_query, 
                limit=limit, 
                resource_type=resource_type,
                peer_reviewed_only=peer_reviewed_only
            )
        
        # Handle results
        self._handle_search_results(results, search_query, resource_type)
    
    def _display_search_message(self, query: str, limit: int, resource_type: Optional[str], peer_reviewed_only: bool = False):
        """Display search initiation message."""
        parts = ["Great! Let me search for"]
        
        if limit:
            parts.append(f"**{limit}**")
        
        if resource_type:
            type_text = f"**{resource_type}s**" if limit != 1 else f"**{resource_type}**"
            parts.append(type_text)
        else:
            parts.append("resources")
            
        # Add peer review status if applicable
        if peer_reviewed_only:
            parts.append("(peer-reviewed only)")
            
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

            # Check if this is a response to peer review question
            if len(conversation_history) >= 2:
                prev_msg = conversation_history[-2]["content"].lower()
                last_msg = conversation_history[-1]["content"].lower().strip()

                if "do you want these articles to be peer-reviewed?" in prev_msg:
                    # Get the saved query from session state
                    saved_query = st.session_state.get("saved_query", "")
                    # Debug log saved query and user answer
                    logger.info(f"Saved query: {saved_query!r}, user answer: {last_msg!r}")

                    if saved_query:
                        # Create parameters with the saved query
                        search_params = orchestrator.analyzer.extract_search_parameters(
                            [{"role": "user", "content": saved_query}]
                        )

                        # Update peer review preference based on yes/no response
                        search_params["peer_reviewed_only"] = last_msg in ["yes", "y"]

                        # Execute search with the updated parameters
                        orchestrator.execute_search_with_params(search_params)
                        # Clear saved query so it's not reused accidentally
                        st.session_state.pop("saved_query", None)
                    else:
                        # If no saved query, ask for the research topic
                        response = "What topic would you like to research?"
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    return
                    
            # Check for broad topics first
            last_msg = conversation_history[-1]["content"].lower().strip()
            broad_topics = {
                "research": "Research is a broad category. What specific topic would you like to explore?",
                "research papers": "Research papers is a broad area. Could you specify what subject or field you're interested in?",
                "articles": "I'd be happy to help you find articles. What topic would you like to search for?",
                "papers": "I can help you find papers. What specific subject are you interested in?"
            }
            
            if last_msg in broad_topics:
                response = broad_topics[last_msg]
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                return
            
            # Check if we need to ask about peer review or ask for topic first
            article_keywords = ["article", "articles", "paper", "papers", "research", "publication"]
            has_article_intent = any(keyword in last_msg for keyword in article_keywords)
            is_not_response = last_msg not in ["yes", "y", "no", "n"]

            # Use analyzer helper to check for generic article requests (DRY)
            is_generic = orchestrator.analyzer.is_generic_article_request(last_msg)

            # If we are awaiting a topic (previously asked for specification), treat this as the topic
            if st.session_state.get("awaiting_topic"):
                topic = last_msg
                st.session_state.pop("awaiting_topic", None)
                # Save the resolved query for search and ask about peer review next
                st.session_state["saved_query"] = topic
                response = "Do you want these articles to be peer-reviewed? (yes/no)"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                return
            if has_article_intent and is_not_response and "peer-reviewed?" not in last_msg:
                # If the user input is generic (e.g. "I need articles"), ask for topic first
                if is_generic:
                    st.session_state["awaiting_topic"] = True
                    response = "What specific topic or field are you interested in? For example: 'machine learning in healthcare' or 'genomics'."
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    return

                # Otherwise treat the message as a specific query and ask about peer review
                st.session_state["saved_query"] = last_msg
                response = "Do you want these articles to be peer-reviewed? (yes/no)"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                return
            
            # Check if we're in a topic refinement loop
            if len(conversation_history) >= 4:  # Need at least 2 exchanges
                last_two_assistant = [
                    msg["content"] for msg in conversation_history[-4:] 
                    if msg["role"] == "assistant"
                ]
                last_two_user = [
                    msg["content"] for msg in conversation_history[-4:] 
                    if msg["role"] == "user"
                ]
                
                # If user repeats the same topic and we keep asking for refinement
                if len(last_two_user) >= 2 and len(last_two_assistant) >= 2:
                    if (last_two_user[0].lower() == last_two_user[1].lower() and
                        all("what research topic" in msg.lower() for msg in last_two_assistant)):
                        # Break the loop by asking for resource type
                        response = f"I see you're interested in {last_two_user[0]}. What type of resources would you like to explore? (articles, books, journals, or any type)"
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        return
            
            # Check if should search
            if orchestrator.analyzer.should_trigger_search(prompt):
                # If it's a single-word response, combine with previous context
                if len(prompt.split()) == 1 and len(conversation_history) > 1:
                    last_context = conversation_history[-2]["content"]
                    if "type of resources" in last_context.lower():
                        # This is a resource type response, proceed with search using previous topic
                        orchestrator.execute_search(conversation_history)
                        return
            
                orchestrator.execute_search(conversation_history)
                return
            
            # Get AI response
            ai_response = orchestrator.get_conversation_response(conversation_history)
            logger.info(f"AI response: {ai_response}")
            
            # Check if ready to search
            if "READY_TO_SEARCH" in ai_response:
                orchestrator.execute_search(conversation_history)
            else:
                # If the last few exchanges are just repeating the topic
                if len(conversation_history) >= 4:
                    last_few_msgs = [msg["content"].lower() for msg in conversation_history[-4:]]
                    if any(msg == prompt.lower() for msg in last_few_msgs[:-1]):
                        # Break the loop by asking for specifics
                        response = f"Could you tell me what specific aspect of {prompt} you're interested in? For example:"
                        
                        # Add relevant examples based on the topic
                        if "biology" in prompt.lower():
                            response += "\n- Molecular biology\n- Genetics\n- Ecology\n- Cell biology\n- Evolution"
                        elif "computer science" in prompt.lower():
                            response += "\n- Algorithms\n- Machine Learning\n- Software Engineering\n- Database Systems\n- Cybersecurity"
                        else:
                            # Generic prompt for other topics
                            response += " theories, applications, recent developments, or specific sub-fields?"
                        
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        return
                
                # Continue conversation
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})


# Legacy function kept for backward compatibility
def suggest_alternative_search(groq_client: GroqClient, original_query: str) -> str:
    """Legacy function - delegates to SuggestionService."""
    prompt_manager = PromptManager()
    service = SuggestionService(groq_client, prompt_manager)
    return service.generate_suggestions(original_query)

