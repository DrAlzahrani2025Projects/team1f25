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
5. Do you want it to be peer reviewed only? (yes/no)

Ask ONE clear question at a time to gather missing information.

Only respond with "READY_TO_SEARCH" when you have at least:
- Clear research topic with specific focus
- Resource type preference (or user confirms "any type")
- Peer reviewed preference (yes/no)

Required information checklist:
✓ Topic + specific aspect (e.g., "machine learning algorithms")
✓ Resource type (articles/books/journals/thesis) OR user says "any type"
✓ Peer reviewed preference (yes/no)
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
Assistant: "Do you want the articles to be peer reviewed only? (yes/no)"
User: "Yes"
Assistant: "READY_TO_SEARCH"

(ACCEPT):
Conversation 2 - Help:
User: "Explain about AI"
Assistant: "AI is the field of creating systems that perform tasks usually requiring human intelligence—like perception, learning, reasoning, and language—using data-driven algorithms and models."

(ACCEPT):
Conversation 3 - Help:
User: "Give me abstract of Forecasting the Effects of Global Warming on Biodiversity"
Assistant: Gives abstract of the specified scholarly article.

DO NOT trigger search until you have:
1. Specific topic (not just broad field)
2. Resource type preference confirmed
3. Peer reviewed preference confirmed

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

EXTRACTION RULES:
1. "query": Extract ONLY the main research topic/search terms. REMOVE all resource types, peer-review keywords, and date references.
   Examples of what to REMOVE: "articles", "peer reviewed", "peer-reviewed", "from 2025", "since 2020", "between 2015 and 2020"
   
2. "limit": Number of results requested. Default to 10 if not specified.

3. "resource_type": Type of resource (article/book/journal/dissertations). Set to null if not specified.
   - "article" = journal articles, scholarly articles
   - "book" = books, ebooks  
   - "journal" = journal publications
   - "dissertations" = dissertations, theses

4. "date_from": Lower bound for publication year. Extract ONLY the EARLIEST year mentioned.
   - "from 2025" → 2025
   - "since 2018" → 2018
   - "2015-2023" → 2015
   - "between 2010 and 2018" → 2010
   - Not mentioned → null

5. "date_to": Upper bound for publication year. Extract ONLY the LATEST year mentioned.
   - "from 2025" → null (open-ended)
   - "until 2023" → 2023
   - "2015-2023" → 2023
   - "between 2010 and 2018" → 2018
   - Not mentioned → null

6. "peer_reviewed_only": Boolean. true if "peer reviewed", "peer-reviewed", "scholarly", "academic", "refereed" mentioned. false otherwise.

CRITICAL EXAMPLES FOR DATES:

User: "I need articles on viruses from 2025"
QUERY PART: "viruses"
DATE PART: "from 2025"
→ {{"query": "viruses", "resource_type": "article", "date_from": 2025, "date_to": null, "peer_reviewed_only": false}}

User: "peer reviewed articles on diabetes 2020-2024"
QUERY PART: "diabetes"
DATE PART: "2020-2024"
→ {{"query": "diabetes", "resource_type": "article", "date_from": 2020, "date_to": 2024, "peer_reviewed_only": true}}

User: "give me research papers since 2018"
QUERY PART: "research papers" → CLEAN TO: "papers"
DATE PART: "since 2018"
→ {{"query": "papers", "resource_type": null, "date_from": 2018, "date_to": null, "peer_reviewed_only": false}}

EXAMPLES:

User: "I need 5 articles about machine learning in healthcare"
{{"query": "machine learning healthcare", "limit": 5, "resource_type": "article", "date_from": null, "date_to": null, "peer_reviewed_only": false}}

User: "Find 10 books on climate change"
{{"query": "climate change", "limit": 10, "resource_type": "book", "date_from": null, "date_to": null, "peer_reviewed_only": false}}

User: "Show me research on diabetes from 2020"
{{"query": "diabetes", "limit": 10, "resource_type": null, "date_from": 2020, "date_to": null, "peer_reviewed_only": false}}

User: "I want peer reviewed articles about AI since 2018"
{{"query": "artificial intelligence", "limit": 10, "resource_type": "article", "date_from": 2018, "date_to": null, "peer_reviewed_only": true}}

User: "Give me any peer reviewed articles on viruses from 2025"
{{"query": "viruses", "limit": 10, "resource_type": "article", "date_from": 2025, "date_to": null, "peer_reviewed_only": true}}

User: "I need scholarly research on robotics between 2020 and 2024"
{{"query": "robotics", "limit": 10, "resource_type": null, "date_from": 2020, "date_to": 2024, "peer_reviewed_only": true}}

User: "Find peer-reviewed journal articles about climate from 2015-2023"
{{"query": "climate", "limit": 10, "resource_type": "article", "date_from": 2015, "date_to": 2023, "peer_reviewed_only": true}}

User: "Get me 7 scholarly articles on robotics since 2018"
{{"query": "robotics", "limit": 7, "resource_type": "article", "date_from": 2018, "date_to": null, "peer_reviewed_only": true}}

User: "Find theses on quantum computing with peer review only from 2015 to 2022"
{{"query": "quantum computing", "limit": 10, "resource_type": "dissertations", "date_from": 2015, "date_to": 2022, "peer_reviewed_only": true}}

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
