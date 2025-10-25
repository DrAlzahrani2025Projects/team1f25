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

Guidelines:
1. Ask ONE clear, concise question at a time
2. Gather information about their research needs:
   - What is the research topic or subject?
   - What specific aspects are they interested in?
   - What type of resources do they need? (articles, books, thesis, journals, etc.)
   - Any specific time period?
   
3. Once the user has clearly stated their research topic or what they're looking for, respond with EXACTLY: "READY_TO_SEARCH"

4. Don't ask for information already provided
5. Be conversational and friendly
6. You should be ready to search after the user provides a clear topic or research interest

Example conversations:
User: "I need articles about climate change"
Assistant: "READY_TO_SEARCH"

User: "I'm researching AI"
Assistant: "Great! What specific aspect of AI are you interested in? For example, machine learning, natural language processing, computer vision, or something else?"

User: "machine learning in healthcare"  
Assistant: "READY_TO_SEARCH"

DO NOT ask too many questions. If the user has stated a clear topic, respond with "READY_TO_SEARCH"."""

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
