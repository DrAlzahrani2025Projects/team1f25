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


def extract_search_query(groq_client: GroqClient, conversation_history: List[Dict]) -> str:
    """Extract and format a search query from conversation history."""
    # Get the conversation text
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""Based on the following conversation with a user looking for academic resources, extract the key search terms and create a precise search query for a library database.

Conversation:
{conversation_text}

Generate a search query that:
1. Includes the main topic and keywords mentioned by the user
2. Keep it simple - avoid complex Boolean operators unless specifically requested
3. Use natural language that works well with academic search
4. Focuses on the actual research topic, not procedural questions

Examples:
- If user wants "machine learning in healthcare", return: machine learning healthcare
- If user wants "climate change articles from 2020", return: climate change
- If user wants "artificial intelligence OR neural networks", return: artificial intelligence neural networks
- If user wants "diabetes treatment", return: diabetes treatment

IMPORTANT: Keep the query simple and natural. Avoid AND/OR operators unless the user specifically requested them.

Respond with ONLY the search query, nothing else. Do not include quotes or explanations."""

    try:
        query = groq_client.chat(prompt)
        return query.strip()
    except Exception as e:
        logger.error(f"Error extracting search query: {e}")
        # Fallback: extract from last user message
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        if user_messages:
            return user_messages[-1]
        return "research"


def check_user_wants_search(user_input: str) -> bool:
    """Check if user explicitly wants to trigger a search."""
    search_keywords = [
        "search now", "find articles", "show me", "search for", 
        "look for", "get articles", "retrieve", "fetch"
    ]
    return any(keyword in user_input.lower() for keyword in search_keywords)
