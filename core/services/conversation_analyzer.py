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
    
    # Keywords that indicate user wants to search immediately
    SEARCH_TRIGGER_KEYWORDS = [
        "search now", "find articles", "show me", "search for", 
        "look for", "get articles", "retrieve", "fetch", "give me",
        "find me", "get me"
    ]
    
    # Additional trigger patterns that indicate search intent
    SEARCH_VERBS = ["i need", "i want", "get me", "give me", "find me"]
    RESOURCE_TYPES = ["article", "book", "journal", "thesis"]
    
    def __init__(self, llm_client: ILLMClient, prompt_provider: IPromptProvider):
        """Initialize with dependencies (Dependency Injection)."""
        self.llm_client = llm_client
        self.prompt_provider = prompt_provider
    
    def should_trigger_search(self, user_input: str) -> bool:
        """Check if user explicitly wants to trigger a search."""
        user_input_lower = user_input.lower()
        
        # Check simple trigger keywords
        if any(keyword in user_input_lower for keyword in self.SEARCH_TRIGGER_KEYWORDS):
            return True
        
        # Check for verb + resource type pattern (e.g., "I need books", "I want articles")
        for verb in self.SEARCH_VERBS:
            if verb in user_input_lower:
                # Check if any resource type appears after the verb
                verb_pos = user_input_lower.find(verb)
                text_after_verb = user_input_lower[verb_pos:]
                if any(resource in text_after_verb for resource in self.RESOURCE_TYPES):
                    return True
        
        return False
    
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
            
            # Convert dates to proper YYYYMMDD string format if they're integers or years
            date_from = self._normalize_date_param(date_from, is_start=True)
            date_to = self._normalize_date_param(date_to, is_start=False)
            
            params["date_from"] = date_from
            params["date_to"] = date_to
            # If LLM did not provide dates, attempt heuristic extraction from text
            if params.get("date_from") is None and params.get("date_to") is None:
                d_from, d_to = self._extract_dates_from_text(conversation_text)
                if d_from is not None:
                    params["date_from"] = self._normalize_date_param(d_from, is_start=True)
                if d_to is not None:
                    params["date_to"] = self._normalize_date_param(d_to, is_start=False)
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
        all_text = "\n".join(user_messages)
        
        # Also attempt to extract dates heuristically from the last message(s)
        d_from, d_to = self._extract_dates_from_text(all_text)
        
        # Normalize dates to YYYYMMDD string format
        d_from = self._normalize_date_param(d_from, is_start=True)
        d_to = self._normalize_date_param(d_to, is_start=False)
        
        # Try to extract resource type using simple heuristics
        resource_type = self._extract_resource_type_heuristic(all_text)
        
        # Try to extract limit using simple heuristics
        limit = self._extract_limit_heuristic(all_text)

        return {
            "query": last_message,
            "limit": limit,
            "resource_type": resource_type,
            "date_from": d_from,
            "date_to": d_to
        }
    
    def _extract_resource_type_heuristic(self, text: str) -> Optional[str]:
        """Extract resource type using simple keyword matching."""
        text_lower = text.lower()
        
        # Check for each resource type keyword
        # Order matters - check more specific terms first
        if any(word in text_lower for word in ["journal articles", "peer reviewed articles", "research articles"]):
            return "article"
        if any(word in text_lower for word in ["articles", "article"]):
            return "article"
        if any(word in text_lower for word in ["journals", "journal", "peer reviewed journals"]):
            return "article"  # journals map to article
        if any(word in text_lower for word in ["books", "book", "ebooks", "ebook"]):
            return "book"
        if any(word in text_lower for word in ["thesis", "theses", "dissertation", "dissertations"]):
            return "thesis"
        
        return None
    
    def _extract_limit_heuristic(self, text: str) -> int:
        """Extract limit (number of results) using simple pattern matching."""
        import re
        
        # Look for patterns like "5 articles", "find 3 books", "I need 10 papers"
        patterns = [
            r'\b(\d+)\s+(?:articles|books|journals|papers|thesis|theses|dissertations|results)',
            r'(?:find|get|show|need|want)\s+(\d+)',
            r'(\d+)\s+(?:of|for)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    limit = int(match.group(1))
                    if 1 <= limit <= 100:  # Reasonable range
                        return limit
                except (ValueError, IndexError):
                    pass
        
        return 10  # Default

    def _normalize_date_param(self, date_val, is_start: bool) -> Optional[str]:
        """Normalize date parameter to YYYYMMDD string format.
        
        Args:
            date_val: Date value (could be int, str, or None)
            is_start: True if start date (use 0101), False if end date (use 1231 or today)
        
        Returns:
            YYYYMMDD string or None
        """
        if date_val is None:
            return None
        
        # Convert to string if it's an integer
        date_str = str(date_val)
        
        # If it's already 8 digits, return as-is
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        
        # If it's 4 digits (year only), expand to YYYYMMDD
        if len(date_str) == 4 and date_str.isdigit():
            if is_start:
                return f"{date_str}0101"  # January 1st
            else:
                # For end date, use today's date if it's current year, otherwise Dec 31
                from datetime import datetime
                current_year = datetime.now().year
                if int(date_str) >= current_year:
                    return datetime.now().strftime("%Y%m%d")
                else:
                    return f"{date_str}1231"  # December 31st
        
        # If it's 6 digits (YYYYMM), expand to YYYYMMDD
        if len(date_str) == 6 and date_str.isdigit():
            if is_start:
                return f"{date_str}01"  # First day of month
            else:
                # Last day of month
                year = int(date_str[:4])
                month = int(date_str[4:6])
                if month in [1, 3, 5, 7, 8, 10, 12]:
                    return f"{date_str}31"
                elif month in [4, 6, 9, 11]:
                    return f"{date_str}30"
                else:  # February
                    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                    return f"{date_str}29" if is_leap else f"{date_str}28"
        
        # If we can't parse it, return None
        logger.warning(f"Could not normalize date value: {date_val}")
        return None
    
    def _extract_dates_from_text(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Delegate to shared utility for heuristic extraction.

        Returns tuple (date_from, date_to) where each value is an int (YYYY or YYYYMMDD)
        or None if not found.
        """
        return extract_dates_from_text(text)

    def extract_date_parameters(self, text: str) -> dict:
        """Public helper to extract date_from/date_to from a short text reply.

        Returns a dict: {"date_from": Optional[str], "date_to": Optional[str]} in YYYYMMDD format.
        """
        d_from, d_to = self._extract_dates_from_text(text)
        # Normalize to YYYYMMDD string format
        d_from = self._normalize_date_param(d_from, is_start=True)
        d_to = self._normalize_date_param(d_to, is_start=False)
        return {"date_from": d_from, "date_to": d_to}
