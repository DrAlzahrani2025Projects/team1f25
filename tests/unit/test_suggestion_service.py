"""
Unit tests for SuggestionService.
Uses mocks to test without external LLM API calls.
"""
import pytest
from unittest.mock import Mock
from core.services.suggestion_service import SuggestionService
from core.interfaces import ILLMClient, IPromptProvider


class TestSuggestionService:
    """Unit tests for SuggestionService class."""
    
    def setup_method(self):
        """Setup test fixtures with mocks."""
        self.mock_llm = Mock(spec=ILLMClient)
        self.mock_prompts = Mock(spec=IPromptProvider)
        self.mock_prompts.get_suggestion_prompt.return_value = "Suggest alternatives"
        
        self.service = SuggestionService(self.mock_llm, self.mock_prompts)
    
    def test_generate_suggestions_success(self):
        """Test successful suggestion generation."""
        expected_suggestions = "- Try broader terms\n- Use synonyms"
        self.mock_llm.chat.return_value = expected_suggestions
        
        result = self.service.generate_suggestions("narrow query")
        
        assert result == expected_suggestions
        self.mock_llm.chat.assert_called_once()
    
    def test_generate_suggestions_error_fallback(self):
        """Test fallback when suggestion generation fails."""
        self.mock_llm.chat.side_effect = Exception("API Error")
        
        result = self.service.generate_suggestions("test query")
        
        assert "broader search terms" in result.lower()
        assert result.startswith("-")
    
    def test_default_suggestions_constant(self):
        """Test that default suggestions are defined."""
        assert len(SuggestionService.DEFAULT_SUGGESTIONS) > 0
        assert all(isinstance(s, str) for s in SuggestionService.DEFAULT_SUGGESTIONS)
    
    def test_format_fallback_suggestions(self):
        """Test formatting of fallback suggestions."""
        result = self.service._format_fallback_suggestions()
        
        assert result.count("-") == len(SuggestionService.DEFAULT_SUGGESTIONS)
        for suggestion in SuggestionService.DEFAULT_SUGGESTIONS:
            assert suggestion in result
