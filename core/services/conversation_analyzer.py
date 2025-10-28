"""
Conversation analysis service for extracting search intent.
Follows SRP - Single Responsibility: Analyze user conversations.
"""
import json
import re
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
        "look for", "get articles", "retrieve", "fetch", 
        "looking for"
    ]
    
    # Resource type keywords that indicate search intent
    RESOURCE_TYPE_KEYWORDS = ["articles", "books", "journals", "about"]
    
    # Intent keywords (need more context to determine if it's a search)
    INTENT_KEYWORDS = ["need", "want"]
    
    def __init__(self, llm_client: ILLMClient, prompt_provider: IPromptProvider):
        """Initialize with dependencies (Dependency Injection)."""
        self.llm_client = llm_client
        self.prompt_provider = prompt_provider
    
    def should_trigger_search(self, user_input: str) -> bool:
        """Check if user explicitly wants to trigger a search."""
        user_input_lower = user_input.lower()
        
        # Check for explicit search triggers (high confidence)
        if any(keyword in user_input_lower for keyword in self.SEARCH_TRIGGER_KEYWORDS):
            return True
            
        # Check if it's a resource type response
        if user_input_lower.strip() in ["articles", "books", "journals", "thesis"]:
            return True
            
        # Check for compound queries (topic + type) - resource type with context
        type_indicators = ["articles about", "books about", "journals about", "papers on", "research on"]
        if any(indicator in user_input_lower for indicator in type_indicators):
            return True
        
        # Check for intent keywords COMBINED with resource types or research terms
        if any(intent in user_input_lower for intent in self.INTENT_KEYWORDS):
            # Only trigger if combined with resource types or research indicators
            research_indicators = ["article", "book", "journal", "paper", "research", "publication", "study", "thesis"]
            if any(indicator in user_input_lower for indicator in research_indicators):
                return True
            
        return False

    @staticmethod
    def is_generic_article_request(msg: str) -> bool:
        """Return True if the message is a generic request for articles (no specific topic)."""
        import re
        text = msg.lower()
        # Common patterns that indicate a generic 'help me find' request
        patterns = [
            r"help me .*find",
            r"help me find",
            r"find (me )?articles?",
            r"help me .*articles?",
            r"i would like .*articles?",
            r"could you find .*articles?",
        ]
        for p in patterns:
            if re.search(p, text):
                return True

        tokens = re.findall(r"\w+", text)
        stopwords = {"i", "need", "want", "please", "find", "search", "for", "about", "the", "would", "like", "you", "to", "help", "me", "with"}
        meaningful = [t for t in tokens if t not in stopwords]
        generic_terms = {"article", "articles", "paper", "papers", "research", "publication", "publications"}
        if not meaningful:
            return False
        non_generic = [t for t in meaningful if t not in generic_terms]
        return len(non_generic) == 0
    
    def get_follow_up_response(self, conversation_history: List[Dict]) -> str:
        """Generate a follow-up question or indicate search readiness."""
        try:
            # Get the last user message
            user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
            if not user_messages:
                return "What research topic would you like to explore today?"
                
            last_user_msg = user_messages[-1]["content"].lower()
            
            # Check if it's a broad topic
            broad_topics = {
                "research": "What specific field of research interests you? For example: computer science, biology, psychology, etc.",
                "research papers": "Research papers is a broad category. What specific topic or subject would you like to explore in your research papers?",
                "articles": "What topic or subject would you like to find articles about?",
                "papers": "What specific topic or subject would you like to explore in these papers?",
                "biology": "Could you tell me what specific aspect of biology you're interested in? For example:\n- Molecular biology\n- Genetics\n- Ecology\n- Cell biology\n- Evolution",
                "computer science": "Could you tell me what specific aspect of computer science you're interested in? For example:\n- Algorithms\n- Machine Learning\n- Software Engineering\n- Database Systems\n- Cybersecurity",
                "physics": "Could you tell me what specific area of physics you're interested in? For example:\n- Quantum mechanics\n- Thermodynamics\n- Relativity\n- Particle physics\n- Optics"
            }
            
            # Check if the last message matches any broad topic
            for topic, response in broad_topics.items():
                if last_user_msg.strip() == topic:
                    return response
            
            # If the message contains specific topic and intent for research/articles
            if any(word in last_user_msg for word in ["research", "article", "paper", "journal"]):
                # Helper to detect generic article requests like "I need articles"
                def is_generic_article_request(msg: str) -> bool:
                    import re
                    tokens = re.findall(r"\w+", msg.lower())
                    stopwords = {"i", "need", "want", "please", "find", "search", "for", "about", "the"}
                    meaningful = [t for t in tokens if t not in stopwords]
                    generic_terms = {"article", "articles", "paper", "papers", "research", "publication", "publications"}
                    non_generic = [t for t in meaningful if t not in generic_terms]
                    return len(non_generic) == 0

                # If peer review preference is not specified and this is not a generic request, ask about it
                if not any(term in last_user_msg for term in ["peer review", "peer-review", "scholarly", "academic"]) and not is_generic_article_request(last_user_msg):
                    return "Do you want these articles to be peer-reviewed? (yes/no)"
                    
            # If we get here, use the LLM for a response
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
        user_messages = [msg["content"].lower() for msg in conversation_history if msg["role"] == "user"]
        assistant_messages = [msg["content"].lower() for msg in conversation_history if msg["role"] == "assistant"]
        
        # Build query from context
        query_parts = []
        resource_type = None
        
        # Look for resource type mentions and search context
        resource_types = {
            "article": ["article", "paper", "publication"],
            "book": ["book", "textbook", "ebook"],
            "journal": ["journal", "periodical"],
            "thesis": ["thesis", "dissertation"]
        }
        
        # Process messages in reverse order to prioritize recent context
        for msg in reversed(user_messages):
            # Skip single-word resource type responses
            if msg.strip().lower() in ["articles", "books", "journals", "thesis"]:
                continue
                
            # Add non-empty message to query parts
            if msg.strip():
                query_parts.append(msg.strip())
                
            # Look for resource type
            if not resource_type:
                for rtype, keywords in resource_types.items():
                    if any(kw in msg for kw in keywords):
                        resource_type = rtype
                        break
            
            # Break after finding first substantial query
            if query_parts:
                break
                
        # If we still don't have a query, check assistant messages for context
        if not query_parts:
            for msg in reversed(assistant_messages):
                if "search for" in msg.lower() or "looking for" in msg.lower():
                    # Extract text after these phrases
                    for phrase in ["search for", "looking for"]:
                        if phrase in msg.lower():
                            parts = msg.lower().split(phrase)
                            if len(parts) > 1:
                                query_parts.append(parts[1].strip())
                                break
                    if query_parts:
                        break
        
        resource_type = None
        for msg in user_messages + assistant_messages:
            for rtype, keywords in resource_types.items():
                if any(kw in msg for kw in keywords):
                    resource_type = rtype
                    break
            if resource_type:
                break
        
        # Clean and build the final query
        final_query = " ".join(query_parts) if query_parts else (user_messages[-1] if user_messages else "research")
        
        # Remove common phrases that aren't part of the actual search
        phrases_to_remove = [
            "i need", "i want", "please find", "search for",
            "articles about", "books about", "papers about",
            "peer reviewed", "peer-reviewed", "not peer reviewed",
            "which are not peer reviewed", "which are peer reviewed"
        ]
        
        cleaned_query = final_query.lower()
        for phrase in phrases_to_remove:
            cleaned_query = cleaned_query.replace(phrase, "")
            
        # Clean up extra spaces and punctuation
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        cleaned_query = re.sub(r'[^\w\s-]', '', cleaned_query)
        
        # Look for peer-review intent
        peer_reviewed = False
        peer_review_keywords = [
            "peer review", "peer-review", "scholarly", "academic",
            "refereed", "peer-reviewed"
        ]
        negative_markers = ["not", "no", "without", "non-", "non ", "exclude"]
        
        for msg in user_messages + assistant_messages:
            msg_lower = msg.lower()
            
            # First check for negatives
            has_negative = any(marker in msg_lower for marker in negative_markers)
            
            # Then check for peer review keywords
            has_peer_review = any(kw in msg_lower for kw in peer_review_keywords)
            
            if has_peer_review:
                # If we find both negative marker and peer review keyword, it means NOT peer reviewed
                # If we only find peer review keyword, it means peer reviewed is requested
                peer_reviewed = not has_negative
                break
                
            # Check for explicit yes/no to peer-review question
            if "peer" in msg_lower and "review" in msg_lower and "?" in msg_lower:
                # Look for user's answer in next message
                idx = assistant_messages.index(msg)
                if idx < len(user_messages) - 1:
                    answer = user_messages[idx + 1].lower()
                    if "yes" in answer and not any(neg in answer for neg in negative_markers):
                        peer_reviewed = True
                        break
                    elif "no" in answer or any(neg in answer for neg in negative_markers):
                        peer_reviewed = False
                        break
        
        # Also attempt to extract dates heuristically from all user messages
        d_from, d_to = self._extract_dates_from_text("\n".join(user_messages))
        
        return {
            "query": cleaned_query,
            "limit": 10,
            "resource_type": resource_type,
            "peer_reviewed_only": peer_reviewed,
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
