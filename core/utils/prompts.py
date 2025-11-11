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

CRITICAL RESOURCE TYPE DISTINCTION:
- "peer reviewed journals" OR "journals" = journals (the journal publication itself)
- "peer reviewed articles" OR "journal articles" OR "articles" = articles (published within journals)
- When confirming back to the user, use their EXACT terminology:
  * If they said "journals", say "journals" NOT "journal articles"
  * If they said "articles", say "articles" NOT "journals"

IMPORTANT: Do NOT re-ask for information the user already provided!
- If user said "10 books", DO NOT ask "what type of resource" - they already said books
- If user said "5 articles", DO NOT ask how many - they already said 5
- ONLY ask for missing information (topic specificity, date range if relevant)

Ask ONE clear question at a time to gather missing information.

Only respond with "READY_TO_SEARCH" when you have at least:
- Clear research topic with specific focus
- Resource type preference (or user confirms "any type")

DO NOT ask for confirmation when you already have all required information!
If the user has provided topic, resource type, and optionally count/dates, respond ONLY with "READY_TO_SEARCH".

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
Conversation 4b - Resource type already specified:
User: "Give me 10 music books"
Assistant: "Music is a broad topic. What specific aspect are you interested in? For example, music theory, music history, music education, or a specific genre or era?"
User: "Music history"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 5 - Help:
User: "Explain about AI"
Assistant: "AI is the field of creating systems that perform tasks usually requiring human intelligence—like perception, learning, reasoning, and language—using data-driven algorithms and models."

(ACCEPT):
Conversation 6 - Help:
User: "Give me abstract of Forecasting the Effects of Global Warming on Biodiversity"
Assistant: Gives abstract of the specified scholarly article.

(ACCEPT):
Conversation 7 - Journals (not articles):
User: "I want research about academically at risk nursing students which are peer reviewed journals for last 3 years"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 8 - Articles from journals:
User: "I need peer reviewed articles about nursing education from the last 5 years"
Assistant: "READY_TO_SEARCH"

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
4. "date_from": (optional) Lower bound for publication date. Use STRING in YYYYMMDD format (e.g., "20220101" for Jan 1, 2022) or null.
5. "date_to": (optional) Upper bound for publication date. Use STRING in YYYYMMDD format (e.g., "20251231" for Dec 31, 2025) or null.

Resource types:
- "article" - for scholarly/journal articles (when user says "articles" or "journal articles" or "peer reviewed articles")
- "book" - for books or ebooks
- "journal" - for journal publications (when user says "journals" or "peer reviewed journals" as the PUBLICATION TITLE, NOT articles)
- "thesis" - for dissertations and theses
- null - if not specified

CRITICAL DISTINCTION - PAY CLOSE ATTENTION:
- If user says "journals" OR "peer reviewed journals" OR "research journals" = resource_type: "journal"
- If user says "articles" OR "peer reviewed articles" OR "journal articles" = resource_type: "article"
- If user says "thesis" OR "theses" OR "dissertation" OR "dissertations" = resource_type: "thesis"
- If user says "books" OR "ebooks" = resource_type: "book"

RULES FOR DETERMINING RESOURCE TYPE:
1. Look for the EXACT NOUN the user used: "articles", "journals", "books", "thesis", "dissertation"
2. "peer reviewed" is an ADJECTIVE - it modifies the noun but doesn't change the resource type
3. Examples of proper extraction:
   - "peer reviewed JOURNALS" → resource_type: "journal"
   - "peer reviewed ARTICLES" → resource_type: "article"
   - "peer reviewed THESIS" → resource_type: "thesis"
   - "research JOURNALS" → resource_type: "journal"
   - "scholarly ARTICLES" → resource_type: "article"
   - "doctoral DISSERTATION" → resource_type: "thesis"

DATE CALCULATION (assume today is November 10, 2025 = "20251110"):
- "last 3 years" = "20221110" to "20251110" (exactly 3 years ago from today)
- "last 5 years" = "20201110" to "20251110" (exactly 5 years ago from today)
- "since 2019" = "20190101" to "20251110" (Jan 1 of specified year to today)
- "from 2018 to 2020" = "20180101" to "20201231" (full year ranges)
- Always return dates as STRINGS in YYYYMMDD format
- For "last N years/months", calculate from TODAY's date, not just the year
- For "since YYYY", use January 1st of that year
- For explicit year ranges, use January 1st to December 31st
- For end dates when not specified, use TODAY's date

Examples - ARTICLES vs JOURNALS:

User: "I need 5 articles about machine learning in healthcare"
{{"query": "machine learning healthcare", "limit": 5, "resource_type": "article"}}

User: "I need 5 journals about machine learning in healthcare"
{{"query": "machine learning healthcare", "limit": 5, "resource_type": "journal"}}

User: "Get me 7 scholarly articles on robotics"
{{"query": "robotics", "limit": 7, "resource_type": "article"}}

User: "I want 3 journal articles about AI"
Note: "journal articles" means ARTICLES (published in journals)
{{"query": "artificial intelligence", "limit": 3, "resource_type": "article"}}

User: "Find peer reviewed journals on nursing education"
Note: "peer reviewed journals" means JOURNALS (the publication itself)
{{"query": "nursing education", "limit": 10, "resource_type": "journal"}}

User: "I want peer reviewed articles from medical journals"
Note: "peer reviewed articles" means ARTICLES (even though from journals)
{{"query": "medical", "limit": 10, "resource_type": "article"}}

User: "I want research journals about academically at risk nursing students which are peer reviewed for last 3 years"
Note: "research journals" means JOURNALS, "peer reviewed" is just an adjective. "last 3 years" from today (20251110) = 3 years ago
{{"query": "academically at risk nursing students", "limit": 10, "resource_type": "journal", "date_from": "20221110", "date_to": "20251110"}}

User: "Find peer reviewed articles about nursing students from last 5 years"
Note: "peer reviewed articles" means ARTICLES. "last 5 years" from today (20251110) = 5 years ago
{{"query": "nursing students", "limit": 10, "resource_type": "article", "date_from": "20201110", "date_to": "20251110"}}

Examples - THESIS/DISSERTATIONS:

User: "I want thesis about academically at risk nursing students which are peer reviewed for last 3 years"
Note: "thesis" is the resource type, "peer reviewed" is just an adjective. "last 3 years" from today (20251110) = 3 years ago
{{"query": "academically at risk nursing students", "limit": 10, "resource_type": "thesis", "date_from": "20221110", "date_to": "20251110"}}

User: "Find 5 dissertations on machine learning"
{{"query": "machine learning", "limit": 5, "resource_type": "thesis"}}

User: "I need doctoral dissertations about climate change"
Note: "doctoral dissertations" means THESIS
{{"query": "climate change", "limit": 10, "resource_type": "thesis"}}

User: "Show me theses on nursing education"
Note: "theses" (plural of thesis) means THESIS
{{"query": "nursing education", "limit": 10, "resource_type": "thesis"}}

Examples - BOOKS:

User: "Find 10 books on climate change"
{{"query": "climate change", "limit": 10, "resource_type": "book"}}

User: "I need ebooks about artificial intelligence"
{{"query": "artificial intelligence", "limit": 10, "resource_type": "book"}}

Other examples:

User: "Show me research on diabetes"
{{"query": "diabetes", "limit": 10, "resource_type": null}}

User: "Find articles on diabetes from the last 5 years"
Note: "last 5 years" from today (20251110) = 5 years ago
{{"query": "diabetes", "limit": 10, "resource_type": "article", "date_from": "20201110", "date_to": "20251110"}}

Respond with ONLY valid JSON, nothing else."""
    
    # Additional examples showing date formats the LLM should recognize. These
    # are not exhaustive but help the model learn preferred shapes for dates.
    DATE_EXTRACTION_EXAMPLES = """
Examples of date formats you may return for date_from/date_to:
- "last 5 years" (from today 20251110) → "20201110" to "20251110"
- "last 3 years" (from today 20251110) → "20221110" to "20251110"
- "since 2019" → "20190101" to "20251110" (today's date)
- "from 2015 to 2018" → "20150101" to "20181231"
- "in 2020" → "20200101" to "20201231"
- Always use YYYYMMDD format as strings
- Calculate "last N years" from TODAY's exact date, not just year
- Use null when a bound is not specified
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
