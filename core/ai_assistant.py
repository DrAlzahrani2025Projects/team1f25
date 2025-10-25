# core/ai_assistant.py
"""
AI Assistant module - Simplified facade for AI-related operations.
Follows Facade pattern and delegates to specialized services.
Refactored to follow SOLID principles (SRP, DIP).
"""
from typing import List, Dict
from core.interfaces import ILLMClient, IPromptProvider
from core.services.conversation_analyzer import ConversationAnalyzer
from core.utils.prompts import PromptManager
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)


# Default instances for backward compatibility
_default_prompt_manager = PromptManager()


def generate_follow_up_question(llm_client: ILLMClient, conversation_history: List[Dict]) -> str:
    """
    Generate intelligent follow-up questions based on conversation history.
    Legacy function - delegates to ConversationAnalyzer.
    """
    analyzer = ConversationAnalyzer(llm_client, _default_prompt_manager)
    return analyzer.get_follow_up_response(conversation_history)


def extract_search_parameters(llm_client: ILLMClient, conversation_history: List[Dict]) -> Dict[str, any]:
    """
    Extract search query, number of results, and resource type from conversation.
    Legacy function - delegates to ConversationAnalyzer.
    """
    analyzer = ConversationAnalyzer(llm_client, _default_prompt_manager)
    return analyzer.extract_search_parameters(conversation_history)


def extract_search_query(llm_client: ILLMClient, conversation_history: List[Dict]) -> str:
    """
    Extract and format a search query from conversation history.
    Legacy function - delegates to ConversationAnalyzer.
    """
    params = extract_search_parameters(llm_client, conversation_history)
    return params.get("query", "research")


def check_user_wants_search(user_input: str) -> bool:
    """
    Check if user explicitly wants to trigger a search.
    Legacy function - delegates to ConversationAnalyzer.
    """
    # Use static method since we don't need LLM for this
    return any(
        keyword in user_input.lower() 
        for keyword in ConversationAnalyzer.SEARCH_TRIGGER_KEYWORDS
    )

