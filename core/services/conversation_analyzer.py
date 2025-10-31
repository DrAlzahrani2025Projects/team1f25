"""
Conversation analysis service for extracting search intent.
Follows SRP - Single Responsibility: Analyze user conversations.
"""
import json
from typing import Dict, List, Optional
from core.interfaces import ILLMClient, IPromptProvider
from core.utils.dates import extract_dates_from_text
from core.utils.logging_utils import get_logger
# Keep heuristics in ConversationAnalyzer (SRP). Shared normalization lives in core.utils.dates

logger = get_logger(__name__)


class ConversationAnalyzer:
    """Analyzes conversation to determine search readiness and extract parameters."""
    
    # Keywords that indicate user wants to search 
    
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
            # Normalize and ensure date fields exist
            date_from = params.get("date_from") if isinstance(params, dict) else None
            date_to = params.get("date_to") if isinstance(params, dict) else None
            params.setdefault("date_from", date_from if date_from is not None else None)
            params.setdefault("date_to", date_to if date_to is not None else None)
            # If LLM did not provide dates, attempt heuristic extraction from text
            if params.get("date_from") is None and params.get("date_to") is None:
                d_from, d_to = self._extract_dates_from_text(conversation_text)
                if d_from is not None:
                    params["date_from"] = d_from
                if d_to is not None:
                    params["date_to"] = d_to
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
        # Also attempt to extract dates heuristically from the last message(s)
        d_from, d_to = self._extract_dates_from_text("\n".join(user_messages))

        return {
            "query": last_message,
            "limit": 10,
            "resource_type": None,
            "date_from": d_from,
            "date_to": d_to
        }

    def _extract_dates_from_text(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Delegate to shared utility for heuristic extraction.

        Returns tuple (date_from, date_to) where each value is an int (YYYY or YYYYMMDD)
        or None if not found.
        """
        return extract_dates_from_text(text)

    def extract_date_parameters(self, text: str) -> dict:
        """Public helper to extract date_from/date_to from a short text reply.

        Returns a dict: {"date_from": Optional[int], "date_to": Optional[int]}.
        """
        d_from, d_to = self._extract_dates_from_text(text)
        return {"date_from": d_from, "date_to": d_to}
