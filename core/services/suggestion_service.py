"""
Search suggestion service for generating alternative search terms.
Follows SRP - Single Responsibility: Generate search suggestions.
"""
from core.interfaces import ILLMClient, IPromptProvider
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class SuggestionService:
    """Generates search suggestions when no results are found."""
    
    # Fallback suggestions if AI fails
    DEFAULT_SUGGESTIONS = [
        "Try using broader search terms",
        "Check spelling and try synonyms",
        "Remove specific filters and search again"
    ]
    
    def __init__(self, llm_client: ILLMClient, prompt_provider: IPromptProvider):
        """Initialize with dependencies (Dependency Injection)."""
        self.llm_client = llm_client
        self.prompt_provider = prompt_provider
    
    def generate_suggestions(self, original_query: str) -> str:
        """Generate alternative search suggestions using AI."""
        try:
            prompt = self.prompt_provider.get_suggestion_prompt(original_query)
            suggestions = self.llm_client.chat(prompt)
            return suggestions.strip()
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._format_fallback_suggestions()
    
    def _format_fallback_suggestions(self) -> str:
        """Format fallback suggestions as a list."""
        return "\n".join([f"- {suggestion}" for suggestion in self.DEFAULT_SUGGESTIONS])
