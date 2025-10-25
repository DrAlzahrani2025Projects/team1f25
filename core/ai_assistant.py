# core/ai_assistant.py
"""
AI Assistant module for handling conversational AI logic and query extraction.
"""
from typing import List, Dict
from core.groq_client import GroqClient
from core.logging_utils import get_logger

logger = get_logger(__name__)


def generate_follow_up_question(groq_client: GroqClient, conversation_history: List[Dict]) -> str:
    """Generate intelligent follow-up questions based on conversation history."""
    system_prompt = """You are a helpful scholarly research assistant. Your job is to ask relevant questions to understand what the user is researching.

IMPORTANT: Gather ALL required information before searching:
1. Research topic (what subject?)
2. Specific aspect or focus area (what specifically?)
3. Resource type (articles, books, journals, thesis, or any type?)
4. Number of results (how many? default to 10 if not specified)

Ask ONE clear question at a time to gather missing information.

Only respond with "READY_TO_SEARCH" when you have at least:
- Clear research topic with specific focus
- Resource type preference (or user confirms "any type is fine")

Required information checklist:
✓ Topic + specific aspect (e.g., "machine learning algorithms")
✓ Resource type (articles/books/journals/thesis) OR user says "any type"

Example conversations:

Conversation 1 - Need more info:
User: "I want to research about machine learning"
Assistant: "Machine learning is a broad field. What specific aspect are you interested in? For example, algorithms, applications, deep learning, or something else?"
User: "I am looking for algorithms"
Assistant: "Great! What type of resources would you like? Articles, books, journals, or any type of resource?"
User: "Articles please"
Assistant: "READY_TO_SEARCH"

Conversation 2 - Complete info provided:
User: "I need 5 articles about climate change impacts on agriculture"
Assistant: "READY_TO_SEARCH"

Conversation 3 - Missing resource type:
User: "Find research on neural networks"
Assistant: "What type of resources are you looking for? Articles, books, journals, or any type?"
User: "Any type is fine"
Assistant: "READY_TO_SEARCH"

Conversation 4 - Topic too broad:
User: "I need articles about AI"
Assistant: "AI is a very broad topic. Could you be more specific? For example, are you interested in AI ethics, machine learning, computer vision, natural language processing, or a particular application area?"
User: "Computer vision"
Assistant: "READY_TO_SEARCH"

DO NOT trigger search until you have:
1. Specific topic (not just broad field)
2. Resource type preference confirmed"""

    messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
    
    try:
        response = groq_client.chat(messages, system=system_prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating follow-up question: {e}")
        return "What research topic would you like to explore today?"


def extract_search_parameters(groq_client: GroqClient, conversation_history: List[Dict]) -> Dict[str, any]:
    """Extract search query, number of results, and resource type from conversation."""
    # Get the conversation text
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""Based on the following conversation, extract the search parameters in JSON format.

Conversation:
{conversation_text}

Extract:
1. "query": The main search terms (simple, no Boolean operators)
2. "limit": Number of results requested (default: 10 if not specified)
3. "resource_type": Type of resource to search for

Resource types:
- "article" - for scholarly/journal articles (when user says "articles" or "journal articles")
- "book" - for books or ebooks
- "journal" - for journal publications (when user says "journals" as the publication, NOT "journal articles")
- "thesis" - for dissertations and theses
- null - if not specified

IMPORTANT: 
- "journal articles" = "article" (articles published IN journals)
- "journals" = "journal" (the journal publication itself)

Examples:

User: "I need 5 articles about machine learning in healthcare"
{{"query": "machine learning healthcare", "limit": 5, "resource_type": "article"}}

User: "Find 10 books on climate change"
{{"query": "climate change", "limit": 10, "resource_type": "book"}}

User: "Show me research on diabetes"
{{"query": "diabetes", "limit": 10, "resource_type": null}}

User: "I want 3 journal articles about AI"
{{"query": "artificial intelligence", "limit": 3, "resource_type": "article"}}

User: "I need 5 journals about machine learning in healthcare"
{{"query": "machine learning healthcare", "limit": 5, "resource_type": "journal"}}

User: "Get me 7 scholarly articles on robotics"
{{"query": "robotics", "limit": 7, "resource_type": "article"}}

Respond with ONLY valid JSON, nothing else."""

    try:
        response = groq_client.chat(prompt)
        # Parse JSON response
        import json
        params = json.loads(response)
        logger.info(f"Extracted parameters: {params}")
        return params
    except Exception as e:
        logger.error(f"Error extracting search parameters: {e}")
        # Fallback to simple extraction
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        last_message = user_messages[-1] if user_messages else "research"
        
        return {
            "query": last_message,
            "limit": 10,
            "resource_type": None
        }


def extract_search_query(groq_client: GroqClient, conversation_history: List[Dict]) -> str:
    """Extract and format a search query from conversation history."""
    params = extract_search_parameters(groq_client, conversation_history)
    return params.get("query", "research")


def check_user_wants_search(user_input: str) -> bool:
    """Check if user explicitly wants to trigger a search."""
    search_keywords = [
        "search now", "find articles", "show me", "search for", 
        "look for", "get articles", "retrieve", "fetch"
    ]
    return any(keyword in user_input.lower() for keyword in search_keywords)
