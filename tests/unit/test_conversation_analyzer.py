"""
Unit tests for ConversationAnalyzer service.
Uses mocks to test without external LLM API calls.
"""
import pytest
from unittest.mock import Mock, MagicMock
from core.services.conversation_analyzer import ConversationAnalyzer
from core.interfaces import ILLMClient, IPromptProvider


class TestConversationAnalyzer:
    """Unit tests for ConversationAnalyzer class."""
    
    def setup_method(self):
        """Setup test fixtures with mocks."""
        # Create mock LLM client
        self.mock_llm = Mock(spec=ILLMClient)
        
        # Create mock prompt provider
        self.mock_prompts = Mock(spec=IPromptProvider)
        self.mock_prompts.get_follow_up_prompt.return_value = "System prompt"
        self.mock_prompts.get_parameter_extraction_prompt.return_value = "Extract params"
        
        # Create analyzer with mocks
        self.analyzer = ConversationAnalyzer(self.mock_llm, self.mock_prompts)
    
    def test_should_trigger_search_explicit_keywords(self):
        """Test explicit search trigger detection."""
        assert self.analyzer.should_trigger_search("search now") == True
        assert self.analyzer.should_trigger_search("find articles") == True
        assert self.analyzer.should_trigger_search("show me results") == True
        assert self.analyzer.should_trigger_search("look for papers") == True
    
    def test_should_trigger_search_no_keywords(self):
        """Test when no trigger keywords present."""
        assert self.analyzer.should_trigger_search("I need help") == False
        assert self.analyzer.should_trigger_search("What is AI?") == False
    
    def test_get_follow_up_response_success(self):
        """Test successful follow-up response generation."""
        self.mock_llm.chat.return_value = "What topic are you interested in?"
        
        conversation = [{"role": "user", "content": "I need help"}]
        response = self.analyzer.get_follow_up_response(conversation)
        
        assert response == "What topic are you interested in?"
        self.mock_llm.chat.assert_called_once()
    
    def test_get_follow_up_response_error_handling(self):
        """Test error handling in follow-up response."""
        self.mock_llm.chat.side_effect = Exception("API Error")
        
        conversation = [{"role": "user", "content": "test"}]
        response = self.analyzer.get_follow_up_response(conversation)
        
        assert "research topic" in response.lower()
    
    def test_extract_search_parameters_success(self):
        """Test successful parameter extraction."""
        mock_json = '{"query": "machine learning", "limit": 5, "resource_type": "article"}'
        self.mock_llm.chat.return_value = mock_json
        
        conversation = [{"role": "user", "content": "I need 5 articles on ML"}]
        params = self.analyzer.extract_search_parameters(conversation)
        
        assert params["query"] == "machine learning"
        assert params["limit"] == 5
        assert params["resource_type"] == "article"
    
    def test_extract_search_parameters_fallback(self):
        """Test fallback when extraction fails."""
        self.mock_llm.chat.side_effect = Exception("Parse error")
        
        conversation = [{"role": "user", "content": "test query"}]
        params = self.analyzer.extract_search_parameters(conversation)
        
        assert params["query"] == "test query"
        assert params["limit"] == 10
        assert params["resource_type"] is None
    
    def test_fallback_extraction(self):
        """Test private fallback extraction method."""
        conversation = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "last message"}
        ]
        
        params = self.analyzer._fallback_extraction(conversation)
        
        assert params["query"] == "last message"
        assert params["limit"] == 10
        assert params["resource_type"] is None
    
    def test_search_trigger_keywords_constant(self):
        """Test that search trigger keywords are defined."""
        assert len(ConversationAnalyzer.SEARCH_TRIGGER_KEYWORDS) > 0
        assert "search now" in ConversationAnalyzer.SEARCH_TRIGGER_KEYWORDS

    def test_extract_dates_from_llm_json(self):
        """If LLM returns date_from/date_to in JSON, they are preserved."""
        mock_json = '{"query": "machine learning", "limit": 5, "resource_type": "article", "date_from": 2015, "date_to": 2018}'
        self.mock_llm.chat.return_value = mock_json

        conversation = [{"role": "user", "content": "I need articles from 2015 to 2018 about ML"}]
        params = self.analyzer.extract_search_parameters(conversation)

        assert params.get("date_from") == 2015
        assert params.get("date_to") == 2018

    def test_heuristic_date_extraction_since_and_last(self):
        """Heuristic extraction should catch 'since' and 'last N years' patterns."""
        # Simulate LLM failure
        self.mock_llm.chat.side_effect = Exception("API down")

        conversation = [{"role": "user", "content": "Show me papers since 2019"}]
        params = self.analyzer.extract_search_parameters(conversation)
        assert params.get("date_from") == 2019

        conversation2 = [{"role": "user", "content": "Recent work from the last 3 years"}]
        params2 = self.analyzer.extract_search_parameters(conversation2)
        from datetime import datetime
        now = datetime.utcnow().year
        assert params2.get("date_from") == now - 3 + 1
        assert params2.get("date_to") == now

    def test_month_and_quarter_parsing(self):
        """Test month name parsing and quarter parsing heuristics."""
        self.mock_llm.chat.side_effect = Exception("API down")

        conversation = [{"role": "user", "content": "Show papers from March 2020"}]
        params = self.analyzer.extract_search_parameters(conversation)
        assert params.get("date_from") == 20200301

        conversation2 = [{"role": "user", "content": "I need studies from Q2 2019"}]
        params2 = self.analyzer.extract_search_parameters(conversation2)
        assert params2.get("date_from") == 20190401
        assert params2.get("date_to") == 20190631

    def test_last_n_months(self):
        """Test 'last N months' and 'last month' heuristics."""
        self.mock_llm.chat.side_effect = Exception("API down")
        from datetime import datetime
        now = datetime.utcnow()

        conversation = [{"role": "user", "content": "Find papers from the last 3 months"}]
        params = self.analyzer.extract_search_parameters(conversation)
        assert params.get("date_to") == int(now.strftime("%Y%m%d"))
        assert params.get("date_from") is not None

        conversation2 = [{"role": "user", "content": "Find papers from last month"}]
        params2 = self.analyzer.extract_search_parameters(conversation2)
        assert params2.get("date_from") is not None
        assert params2.get("date_to") == int(now.strftime("%Y%m%d"))
