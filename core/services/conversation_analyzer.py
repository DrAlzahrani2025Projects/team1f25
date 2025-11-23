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
    
    # Keywords that indicate search refinement
    REFINEMENT_KEYWORDS = [
        "only", "just", "filter", "narrow", "refine", "change to",
        "instead", "from", "between", "published in", "in year"
    ]
    
    # Off-topic/meta question patterns that should be redirected
    OFF_TOPIC_PATTERNS = [
        "how many", "tell me", "what is", "who is", "where is", "when is",
        "why is", "can you", "could you", "would you", "do you have",
        "are there", "is there", "how are", "how do", "what are",
        "help me", "thank you", "thanks", "hello", "hi there", "hey"
    ]
    
    def __init__(self, llm_client: ILLMClient, prompt_provider: IPromptProvider):
        """Initialize with dependencies (Dependency Injection)."""
        self.llm_client = llm_client
        self.prompt_provider = prompt_provider
    
    def is_off_topic_question(self, user_input: str) -> bool:
        """Check if user input is an off-topic or meta question that should be redirected."""
        user_input_lower = user_input.lower().strip()
        
        # Check for off-topic patterns
        for pattern in self.OFF_TOPIC_PATTERNS:
            if user_input_lower.startswith(pattern):
                return True
        
        # Check for questions about the system/results rather than research topics
        meta_phrases = [
            "more do you have", "many results", "show me more", "more results",
            "can you show", "do you know", "are you", "what can you"
        ]
        if any(phrase in user_input_lower for phrase in meta_phrases):
            return True
        
        # Check if it's a question without any research-related keywords
        if "?" in user_input and len(user_input.split()) < 8:
            # Short questions without research context are likely off-topic
            research_keywords = ["research", "study", "article", "paper", "book", "thesis", 
                               "journal", "publication", "find", "search", "looking for"]
            if not any(keyword in user_input_lower for keyword in research_keywords):
                return True
        
        return False
    
    def is_metadata_question(self, user_input: str) -> bool:
        """Check if user is asking about metadata or search result statistics."""
        user_input_lower = user_input.lower().strip()
        
        # Metadata question patterns
        metadata_patterns = [
            "how many", "total", "count", "number of", "all the results",
            "show all", "display all", "list all", "what's the",
            "more do you have", "many results", "many more", "how much"
        ]
        
        # Result-related keywords
        result_keywords = ["result", "results", "article", "articles", "record", "records"]
        
        # Check if it's asking about metadata
        has_metadata_pattern = any(pattern in user_input_lower for pattern in metadata_patterns)
        has_result_keyword = any(keyword in user_input_lower for keyword in result_keywords)
        
        # It's a metadata question if it has both patterns
        return has_metadata_pattern and (has_result_keyword or len(user_input.split()) < 8)
    
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
    
    def is_refinement_query(self, user_input: str) -> bool:
        """Detect if user is trying to refine/filter existing search results."""
        user_input_lower = user_input.lower().strip()
        
        # Check for refinement keywords
        if any(keyword in user_input_lower for keyword in self.REFINEMENT_KEYWORDS):
            return True
        
        # Check for year-only patterns (e.g., "2022", "only 2020", "just 2019")
        import re
        year_only_pattern = r'^\s*(only|just)?\s*\d{4}\s*$'
        if re.match(year_only_pattern, user_input_lower):
            return True
        
        # Check for date range patterns without topic keywords
        date_range_pattern = r'^\s*\d{4}\s*(to|-)\s*\d{4}\s*$'
        if re.match(date_range_pattern, user_input_lower):
            return True
        
        # Check for "last N years" patterns
        last_years_pattern = r'^\s*(last|past)\s+\d+\s+years?\s*$'
        if re.match(last_years_pattern, user_input_lower):
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
    
    def extract_search_parameters(self, conversation_history: List[Dict], previous_params: Optional[Dict] = None) -> Dict[str, any]:
        """Extract search query, limit, and resource type from conversation.
        
        Args:
            conversation_history: List of conversation messages
            previous_params: Previous search parameters to merge with (for refinements)
        
        Returns:
            Dict with search parameters
        """
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
            
            # Parse JSON - handle potential errors
            try:
                params = json.loads(response)
                
                # Ensure it's a dict, not a list or other type
                if not isinstance(params, dict):
                    logger.warning(f"LLM returned non-dict response: {type(params)}. Using fallback.")
                    return self._fallback_extraction(conversation_history, previous_params)
                    
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {je}. Response was: {response[:200]}")
                return self._fallback_extraction(conversation_history, previous_params)
            
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
            
            # Merge with previous parameters if provided (for refinements)
            if previous_params:
                params = self._merge_with_previous(params, previous_params, conversation_history)
            
            logger.info(f"Extracted parameters: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error extracting search parameters: {e}")
            # Fallback: use last user message
            return self._fallback_extraction(conversation_history, previous_params)
    
    def _fallback_extraction(self, conversation_history: List[Dict], previous_params: Optional[Dict] = None) -> Dict[str, any]:
        """Fallback parameter extraction when AI fails.
        
        Args:
            conversation_history: List of conversation messages
            previous_params: Previous search parameters to merge with
        """
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        last_message = user_messages[-1] if user_messages else "research"
        all_text = "\n".join(user_messages)
        
        # Always check if this is a refinement query (don't gate on previous_params)
        is_refinement = self.is_refinement_query(last_message)
        
        if is_refinement and previous_params:
            # For refinements with available previous params, merge them
            logger.info("Detected refinement query - merging with previous params")
            
            # Extract dates from the refinement query
            d_from, d_to = self._extract_dates_from_text(last_message)
            d_from = self._normalize_date_param(d_from, is_start=True)
            d_to = self._normalize_date_param(d_to, is_start=False)
            
            # Extract resource type if mentioned
            resource_type = self._extract_resource_type_heuristic(last_message)
            
            # Extract limit if mentioned
            limit = self._extract_limit_heuristic(last_message)
            
            # Merge with previous params, only updating what was specified
            refined_params = previous_params.copy()
            
            if d_from is not None or d_to is not None:
                refined_params["date_from"] = d_from
                refined_params["date_to"] = d_to
            
            if resource_type is not None:
                refined_params["resource_type"] = resource_type
            
            # Only update limit if explicitly mentioned in refinement
            if limit != 10 or any(word in last_message.lower() for word in ["limit", "results", "show"]):
                refined_params["limit"] = limit
            
            logger.info(f"Refined parameters: {refined_params}")
            return refined_params
        elif is_refinement and not previous_params:
            # Looks like refinement but no previous params available
            logger.warning("Detected refinement query but no previous search params available")
            # Try to extract from conversation history instead
            # Look back for a substantial research topic in the conversation
            query = last_message
            
            # Expanded list of resource type phrases to skip
            resource_type_phrases = [
                "articles", "article", "books", "book", "thesis", "theses",
                "peer reviewed articles", "peer reviewed journals", "peer-reviewed articles",
                "peer-reviewed journals", "journal articles", "research articles",
                "research papers", "scholarly articles", "academic articles",
                "any type", "any", "journals", "journal", "ebooks", "e-books",
                "dissertations", "dissertation"
            ]
            
            for i in range(len(user_messages) - 2, -1, -1):
                msg = user_messages[i].strip()
                msg_lower = msg.lower()
                # Skip simple answers and refinement phrases
                if (len(msg.split()) >= 3 and 
                    not self.is_refinement_query(msg) and
                    msg_lower not in resource_type_phrases):
                    query = msg
                    logger.info(f"Found research topic from conversation: {query}")
                    break
            
            # Extract dates and other params from the refinement message
            d_from, d_to = self._extract_dates_from_text(last_message)
            d_from = self._normalize_date_param(d_from, is_start=True)
            d_to = self._normalize_date_param(d_to, is_start=False)
            
            # Get resource type and limit from full conversation
            resource_type = self._extract_resource_type_heuristic(all_text)
            limit = self._extract_limit_heuristic(all_text)
            
            return {
                "query": query,
                "limit": limit,
                "resource_type": resource_type,
                "date_from": d_from,
                "date_to": d_to
            }
        else:
            # Standard fallback for new searches
            # Check if last message is just a clarification answer (resource type, count, etc.)
            last_lower = last_message.lower().strip()
            
            # Expanded list of resource type phrases that shouldn't be treated as queries
            resource_type_phrases = [
                "articles", "article", "books", "book", "thesis", "theses",
                "peer reviewed articles", "peer reviewed journals", "peer-reviewed articles",
                "peer-reviewed journals", "journal articles", "research articles",
                "research papers", "scholarly articles", "academic articles",
                "any type", "any", "journals", "journal", "ebooks", "e-books",
                "dissertations", "dissertation"
            ]
            
            is_simple_answer = (
                last_lower in resource_type_phrases or
                last_lower.isdigit() or
                # Check if it's purely a resource type specification (even with multiple words)
                any(last_lower == phrase for phrase in resource_type_phrases)
            )
            
            # If it's a simple answer, look back for the actual topic
            query = last_message
            if is_simple_answer and len(user_messages) > 1:
                # Search backwards for a message that looks like a research topic
                for i in range(len(user_messages) - 2, -1, -1):
                    msg = user_messages[i].strip()
                    msg_lower = msg.lower()
                    # Skip simple answers and look for substantial topics
                    if (len(msg.split()) >= 3 and 
                        msg_lower not in resource_type_phrases and
                        not msg_lower.startswith("i want to") and
                        not msg_lower.startswith("i need") and
                        "another research" not in msg_lower and
                        "new search" not in msg_lower):
                        query = msg
                        logger.info(f"Found research topic in earlier message: {query}")
                        break
            
            d_from, d_to = self._extract_dates_from_text(all_text)
            d_from = self._normalize_date_param(d_from, is_start=True)
            d_to = self._normalize_date_param(d_to, is_start=False)
            resource_type = self._extract_resource_type_heuristic(all_text)
            limit = self._extract_limit_heuristic(all_text)

            return {
                "query": query,
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
    
    def _merge_with_previous(self, new_params: Dict, previous_params: Dict, conversation_history: List[Dict]) -> Dict:
        """Merge new parameters with previous search parameters.
        
        Used when user is refining an existing search.
        """
        # Get the last user message to check for refinement
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        last_message = user_messages[-1] if user_messages else ""
        
        # Check if this looks like a refinement
        is_refinement = self.is_refinement_query(last_message)
        
        # Also check if the new query is null (LLM detected refinement but didn't provide query)
        new_query = new_params.get("query")
        if new_query is None or new_query == "":
            is_refinement = True
            logger.info("LLM returned null query - treating as refinement")
        
        if not is_refinement:
            # Not a refinement, return new params as-is
            return new_params
        
        logger.info(f"Merging refinement with previous params. Previous: {previous_params}")
        
        # Start with previous params
        merged = previous_params.copy()
        
        # Update only fields that were explicitly changed (not None)
        # Check if query looks like a proper topic or just a refinement phrase
        new_query_lower = str(new_query).strip().lower() if new_query else ""
        refinement_only_phrases = ["only", "just", "filter", "narrow", "refine", "change", "instead"]
        
        # If query doesn't start with refinement phrases and isn't a bare year, update it
        if new_query and not any(new_query_lower.startswith(phrase) for phrase in refinement_only_phrases):
            # Check if it's not just a year
            if not new_query_lower.isdigit() or len(new_query_lower) != 4:
                # Also check it's not just a simple answer like "articles" or "books"
                simple_answers = ["articles", "article", "books", "book", "thesis", "any type", "any"]
                if new_query_lower not in simple_answers:
                    merged["query"] = new_params["query"]
        
        # Update resource type only if it was explicitly provided (not None)
        if new_params.get("resource_type") is not None:
            merged["resource_type"] = new_params["resource_type"]
        # If None, keep previous value (already in merged from copy)
        
        # Update limit only if it was explicitly provided (not None)
        if new_params.get("limit") is not None:
            merged["limit"] = new_params["limit"]
        # If None, keep previous value (already in merged from copy)
        
        # Update dates if specified
        if new_params.get("date_from") is not None:
            merged["date_from"] = new_params["date_from"]
        if new_params.get("date_to") is not None:
            merged["date_to"] = new_params["date_to"]
        
        logger.info(f"Merged parameters: {merged}")
        return merged
    
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
