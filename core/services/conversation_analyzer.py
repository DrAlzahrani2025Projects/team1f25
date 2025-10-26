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
        """Heuristic date extraction from plain text.

        Returns tuple (date_from, date_to) where each value is an int (YYYY or YYYYMMDD)
        or None if not found.
        """
        import re
        from datetime import datetime

        if not text:
            return None, None

        text = text.lower()

        # Full date: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD, or 'March 5, 2020'
        m = re.search(r"(\d{4})[\-/]?(\d{1,2})[\-/]?(\d{1,2})", text)
        if m:
            y, mm, dd = m.groups()
            try:
                return int(f"{int(y):04d}{int(mm):02d}{int(dd):02d}"), None
            except Exception:
                pass

        # Month name formats: 'March 2020', 'Mar 2020', 'March 5, 2020'
        month_names = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        m = re.search(rf"{month_names}\s+(\d{{1,2}}),?\s+(\d{{4}})", text)
        if m:
            mon, day, yr = m.groups()
            try:
                month_idx = datetime.strptime(mon, "%b").month if len(mon) == 3 else datetime.strptime(mon, "%B").month
            except Exception:
                try:
                    month_idx = datetime.strptime(mon[:3], "%b").month
                except Exception:
                    month_idx = None
            if month_idx:
                try:
                    return int(f"{int(yr):04d}{int(month_idx):02d}{int(day):02d}"), None
                except Exception:
                    pass

        # Month + year (no day)
        m = re.search(rf"{month_names}\s+(\d{{4}})", text)
        if m:
            mon, yr = m.groups()
            try:
                month_idx = datetime.strptime(mon[:3], "%b").month
                return int(f"{int(yr):04d}{int(month_idx):02d}01"), None
            except Exception:
                pass

        # Range like: from 2015 to 2020, between 2010 and 2015, 2015-2020
        m = re.search(r"from\s+(\d{4})\s+(?:to|-)\s+(\d{4})", text)
        if not m:
            m = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", text)
        if not m:
            m = re.search(r"(\d{4})\s*[-–]\s*(\d{4})", text)
        if m:
            y1, y2 = m.groups()
            return int(y1), int(y2)

        # Since 2018
        m = re.search(r"since\s+(\d{4})", text)
        if m:
            y = int(m.group(1))
            return y, None

        # Last N years
        m = re.search(r"last\s+(\d{1,2})\s+years", text)
        if m:
            n = int(m.group(1))
            now = datetime.utcnow().year
            return now - n + 1, now

        # Last N months or 'last month'
        m = re.search(r"last\s+(\d{1,2})\s+months", text)
        if m:
            n = int(m.group(1))
            now_dt = datetime.utcnow()
            start_month = (now_dt.month - n + 1)
            start_year = now_dt.year
            while start_month <= 0:
                start_month += 12
                start_year -= 1
            start = int(f"{start_year:04d}{start_month:02d}01")
            end = int(now_dt.strftime("%Y%m%d"))
            return start, end

        if re.search(r"last\s+month", text):
            now_dt = datetime.utcnow()
            mth = now_dt.month - 1
            yr = now_dt.year
            if mth == 0:
                mth = 12
                yr -= 1
            start = int(f"{yr:04d}{mth:02d}01")
            end = int(now_dt.strftime("%Y%m%d"))
            return start, end

        # Quarter like Q1 2018
        m = re.search(r"q([1-4])\s*(\d{4})", text)
        if m:
            q, yr = m.groups()
            q = int(q)
            yr = int(yr)
            quarter_map = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
            start_m, end_m = quarter_map[q]
            start = int(f"{yr:04d}{start_m:02d}01")
            end = int(f"{yr:04d}{end_m:02d}31")
            return start, end

        # Single year mention
        m = re.search(r"\b(19|20)\d{2}\b", text)
        if m:
            return int(m.group(0)), None

        return None, None

    def extract_date_parameters(self, text: str) -> dict:
        """Public helper to extract date_from/date_to from a short text reply.

        Returns a dict: {"date_from": Optional[int], "date_to": Optional[int]}.
        """
        d_from, d_to = self._extract_dates_from_text(text)
        return {"date_from": d_from, "date_to": d_to}
