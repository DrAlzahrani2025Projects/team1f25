"""
Centralized prompt management for AI interactions.
Follows SRP (Single Responsibility) and DRY (Don't Repeat Yourself) principles.
"""
from core.interfaces import IPromptProvider


class PromptManager(IPromptProvider):
    """Manages all AI prompts in one place to avoid duplication."""
    
    # System prompts as class constants for easy maintenance
    FOLLOW_UP_SYSTEM_PROMPT = """You are a professional scholarly research assistant for an academic library. Your ONLY purpose is to help users find scholarly resources (articles, books, journals, theses).

STRICT RULES:
- ONLY discuss academic research topics and scholarly resources
- Do NOT engage in casual conversation or off-topic discussions

IMPORTANT: Gather ALL required information before searching:
1. Research topic (what subject?)
2. Specific aspect or focus area (what specifically?)
3. Resource type (articles, books, journals, thesis, or any type?)
4. Number of results (how many? default to 10 if not specified)

Ask ONE clear question at a time to gather missing information.

Only respond with "READY_TO_SEARCH" when you have at least:
- Clear research topic with specific focus
- Resource type preference (or user confirms "any type")

Required information checklist:
✓ Topic + specific aspect (e.g., "machine learning algorithms")
✓ Resource type (articles/books/journals/thesis) OR user says "any type"

If user asks non-research questions, respond with:
"I'm a scholarly research assistant designed to help you find academic resources. What research topic would you like to explore?"

Example conversations:

(ACCEPT):
Conversation 1 - Need more info:
User: "I want to research about machine learning"
Assistant: "Machine learning is a broad field. What specific aspect are you interested in? For example, algorithms, applications, deep learning, or something else?"
User: "I am looking for algorithms"
Assistant: "Great! What type of resources would you like? Articles, books, journals, or any type of resource?"
User: "Articles please"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 2 - Complete info provided:
User: "I need 5 articles about climate change impacts on agriculture"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 3 - Missing resource type:
User: "Find research on neural networks"
Assistant: "What type of resources are you looking for? Articles, books, journals, or any type?"
User: "Any type"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 4 - Topic too broad:
User: "I need articles about AI"
Assistant: "AI is a very broad topic. Could you be more specific? For example, are you interested in AI ethics, machine learning, computer vision, natural language processing, or a particular application area?"
User: "Computer vision"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 5 - Help:
User: "Explain about AI"
Assistant: "AI is the field of creating systems that perform tasks usually requiring human intelligence—like perception, learning, reasoning, and language—using data-driven algorithms and models."

(ACCEPT):
Conversation 6 - Help:
User: "Give me abstract of Forecasting the Effects of Global Warming on Biodiversity"
Assistant: Gives abstract of the specified scholarly article.

DO NOT trigger search until you have:
1. Specific topic (not just broad field)
2. Resource type preference confirmed

(REDIRECT):
Conversation 1 - Off-topic query:
User: "What's the weather today?"
Assistant: "I'm a scholarly research assistant designed to help you find academic resources. What research topic would you like to explore?"

(REDIRECT):
Conversation 2 - Off-topic query:
User: "Tell me a joke"
Assistant: "I'm a scholarly research assistant designed to help you find academic resources. What research topic would you like to explore?"

(REDIRECT):
Conversation 3 - Off-topic query:
User: "How are you doing?"
Assistant: "I'm a scholarly research assistant designed to help you find academic resources. What research topic would you like to explore?"

IMPORTANT: Stay strictly within the scope of scholarly research assistance. Redirect any off-topic queries."""

    PARAMETER_EXTRACTION_TEMPLATE = """Based on the following conversation, extract the search parameters in JSON format.

Conversation:
{conversation_text}

Extract:
1. "query": The main search terms (simple, no Boolean operators)
2. "limit": Number of results requested (default: 10 if not specified)
3. "resource_type": Type of resource to search for
4. "date_from": (optional) Lower bound for publication date. Use YYYY or YYYYMMDD or null.
5. "date_to": (optional) Upper bound for publication date. Use YYYY or YYYYMMDD or null.

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
    
    # Additional examples showing date formats the LLM should recognize. These
    # are not exhaustive but help the model learn preferred shapes for dates.
    DATE_EXTRACTION_EXAMPLES = """
Examples of date formats you may return for date_from/date_to:
- Year only: 2018
- Year range: 2015 to 2018
- Full date: 2020-03-15 or March 15, 2020
- Month and year: March 2020
- Relative: since 2019, last 3 years, last month, last 6 months
- Quarter: Q1 2018 (interpret as Jan-Mar 2018)

When returning dates, prefer integers in YYYY or YYYYMMDD format. Use null
when a bound is not specified.
"""
    

    SUGGESTION_TEMPLATE = """The user searched for "{query}" in an academic library database but got 0 results.

Suggest 2-3 alternative, broader search terms that might work better. Keep suggestions short and relevant.

Format your response as a simple list:
- suggestion 1
- suggestion 2
- suggestion 3

Example:
If user searched: "ott churn causes"
Suggest:
- customer churn
- subscriber retention
- streaming service analytics"""

    def get_follow_up_prompt(self) -> str:
        """Get the system prompt for follow-up questions."""
        return self.FOLLOW_UP_SYSTEM_PROMPT
    
    def get_parameter_extraction_prompt(self, conversation_text: str) -> str:
        """Get the prompt for extracting search parameters."""
        return self.PARAMETER_EXTRACTION_TEMPLATE.format(conversation_text=conversation_text)
    
    def get_suggestion_prompt(self, query: str) -> str:
        """Get the prompt for generating search suggestions."""
        return self.SUGGESTION_TEMPLATE.format(query=query)
