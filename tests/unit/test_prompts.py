"""
Unit tests for PromptManager.
Tests prompt generation without external dependencies.
"""
import pytest
from core.utils.prompts import PromptManager


class TestPromptManager:
    """Unit tests for PromptManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = PromptManager()
    
    def test_get_follow_up_prompt(self):
        """Test follow-up prompt retrieval."""
        prompt = self.manager.get_follow_up_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "research" in prompt.lower()
        assert "READY_TO_SEARCH" in prompt
    
    def test_get_parameter_extraction_prompt(self):
        """Test parameter extraction prompt with conversation."""
        conversation_text = "user: I need articles\nassistant: What topic?"
        prompt = self.manager.get_parameter_extraction_prompt(conversation_text)
        
        assert isinstance(prompt, str)
        assert conversation_text in prompt
        assert "query" in prompt.lower()
        assert "limit" in prompt.lower()
        assert "resource_type" in prompt.lower()
    
    def test_get_suggestion_prompt(self):
        """Test suggestion prompt generation."""
        query = "machine learning"
        prompt = self.manager.get_suggestion_prompt(query)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert "0 results" in prompt or "no results" in prompt.lower()
        assert "alternative" in prompt.lower() or "suggest" in prompt.lower()
    
    def test_follow_up_system_prompt_constant(self):
        """Test that system prompt constant exists."""
        assert hasattr(PromptManager, 'FOLLOW_UP_SYSTEM_PROMPT')
        assert len(PromptManager.FOLLOW_UP_SYSTEM_PROMPT) > 100
    
    def test_parameter_extraction_template_constant(self):
        """Test that parameter extraction template exists."""
        assert hasattr(PromptManager, 'PARAMETER_EXTRACTION_TEMPLATE')
        assert '{conversation_text}' in PromptManager.PARAMETER_EXTRACTION_TEMPLATE
    
    def test_suggestion_template_constant(self):
        """Test that suggestion template exists."""
        assert hasattr(PromptManager, 'SUGGESTION_TEMPLATE')
        assert '{query}' in PromptManager.SUGGESTION_TEMPLATE
