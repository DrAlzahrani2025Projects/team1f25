"""
Conversation analysis service for extracting search intent.
Follows SRP - Single Responsibility: Analyze user conversations.
"""
import json
from typing import Dict, List, Optional
from core.interfaces import ILLMClient, IPromptProvider
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConversationAnalyzer:
    """Analyzes conversation to determine search readiness and extract parameters."""
    
    # Keywords that indicate user wants to search immediately
    SEARCH_TRIGGER_KEYWORDS = [
        "search now", "find articles", "show me", "search for", 
        "look for", "get articles", "retrieve", "fetch"
    ]
    
    def __init__(self, llm_client: ILLMClient, prompt_provider: IPromptProvider):
        """Initialize with dependencies (Dependency Injection)."""
        self.llm_client = llm_client
        self.prompt_provider = prompt_provider
    
    def should_trigger_search(self, user_input: str) -> bool:
        """Check if user explicitly wants to trigger a search."""
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in self.SEARCH_TRIGGER_KEYWORDS)
    
    def get_follow_up_response(self, conversation_history: List[Dict]) -> str:
        """Generate a follow-up question or indicate search readiness."""
        try:
            system_prompt = self.prompt_provider.get_follow_up_prompt()
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
            response = self.llm_client.chat(messages, system=system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            return "What research topic would you like to explore today?"
    
    def extract_search_parameters(self, conversation_history: List[Dict]) -> Dict[str, any]:
        """Extract search query, limit, and resource type from conversation."""
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in conversation_history
            ])
            
            # Get extraction prompt
            prompt = self.prompt_provider.get_parameter_extraction_prompt(conversation_text)
            
            # Get LLM response
            response = self.llm_client.chat(prompt)
            
            # Parse JSON
            params = json.loads(response)
            logger.info(f"Extracted parameters: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error extracting search parameters: {e}")
            # Fallback: use last user message
            return self._fallback_extraction(conversation_history)
    
    def _fallback_extraction(self, conversation_history: List[Dict]) -> Dict[str, any]:
        """Fallback parameter extraction when AI fails."""
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        last_message = user_messages[-1] if user_messages else "research"
        
        return {
            "query": last_message,
            "limit": 10,
            "resource_type": None
        }
