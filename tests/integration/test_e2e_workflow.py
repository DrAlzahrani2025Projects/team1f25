"""
End-to-end integration tests for complete workflows.
Tests the entire flow from user input to search results.
"""
import pytest
import os
from core.clients.groq_client import GroqClient
from core.services.conversation_analyzer import ConversationAnalyzer
from core.services.search_service import SearchService
from core.clients.csusb_library_client import CSUSBLibraryClient
from core.utils.prompts import PromptManager


class TestEndToEndWorkflow:
    """E2E integration tests for complete user workflows."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")
        
        self.llm_client = GroqClient()
        self.library_client = CSUSBLibraryClient()
        self.prompt_manager = PromptManager()
        self.analyzer = ConversationAnalyzer(self.llm_client, self.prompt_manager)
        self.search_service = SearchService(self.library_client)
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_complete_article_search_workflow(self):
        """Test complete workflow: user request -> parameter extraction -> search."""
        # Step 1: User makes request
        conversation = [
            {"role": "user", "content": "I need 5 articles about machine learning in healthcare"}
        ]
        
        # Step 2: Extract parameters
        params = self.analyzer.extract_search_parameters(conversation)
        
        assert "query" in params
        assert params.get("limit") == 5
        assert params.get("resource_type") == "article"
        assert "peer_reviewed" in params
        assert params.get("peer_reviewed") in ["true", "false"]
        
        # Step 3: Perform search
        results = self.search_service.search(
            params["query"],
            limit=params["limit"],
            resource_type=params["resource_type"]
        )
        
        assert results is not None
        assert len(results.get("docs", [])) > 0
        
        # Step 4: Verify results are articles
        for doc in results["docs"][:3]:
            doc_type = doc.get("pnx", {}).get("display", {}).get("type", [""])[0]
            assert "article" in doc_type.lower() or "review" in doc_type.lower()
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_complete_book_search_workflow(self):
        """Test complete workflow for book search."""
        conversation = [
            {"role": "user", "content": "Find 3 books on artificial intelligence"}
        ]
        
        # Extract parameters
        params = self.analyzer.extract_search_parameters(conversation)
        
        assert params.get("limit") == 3
        assert params.get("resource_type") == "book"
        assert "peer_reviewed" in params
        
        # Perform search
        results = self.search_service.search(
            params["query"],
            limit=params["limit"],
            resource_type=params["resource_type"]
        )
        
        assert results is not None
        assert len(results.get("docs", [])) > 0
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_conversation_flow_with_follow_up(self):
        """Test multi-turn conversation flow."""
        # First message - broad topic
        conversation = [
            {"role": "user", "content": "I want to research machine learning"}
        ]
        
        # Get follow-up question
        response = self.analyzer.get_follow_up_response(conversation)
        
        assert response is not None
        assert len(response) > 0
        
        # Should NOT be ready yet (needs more info)
        assert "READY_TO_SEARCH" not in response
        
        # Add assistant response and user's specific aspect
        conversation.append({"role": "assistant", "content": response})
        conversation.append({"role": "user", "content": "I am looking for algorithms"})
        
        response = self.analyzer.get_follow_up_response(conversation)
        
        # Should ask for resource type
        assert response is not None
        assert "READY_TO_SEARCH" not in response
        
        # Add resource type preference
        conversation.append({"role": "assistant", "content": response})
        conversation.append({"role": "user", "content": "Articles please"})
        
        response = self.analyzer.get_follow_up_response(conversation)
        
        # Should ask for peer review preference
        assert response is not None
        
        # If not ready, add peer review preference
        if "READY_TO_SEARCH" not in response:
            conversation.append({"role": "assistant", "content": response})
            conversation.append({"role": "user", "content": "Yes, peer reviewed only"})
            
            response = self.analyzer.get_follow_up_response(conversation)
        
        # Now should be ready
        assert "READY_TO_SEARCH" in response
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_trigger_search_detection(self):
        """Test explicit search trigger detection."""
        user_input = "search now for climate change"
        
        assert self.analyzer.should_trigger_search(user_input) == True
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_different_resource_types_workflow(self):
        """Test workflow with different resource type requests."""
        test_cases = [
            ("I need 5 articles about AI", "article"),
            ("Find 3 books on robotics", "book"),
            ("Show me 2 journals about medicine", "journal"),
            ("I want 3 journal articles about AI", "article"),  # journal articles = article
            ("Get me 7 scholarly articles on robotics", "article"),
            ("Find theses on quantum computing", "dissertations")
        ]
        
        for user_request, expected_type in test_cases:
            conversation = [{"role": "user", "content": user_request}]
            params = self.analyzer.extract_search_parameters(conversation)
            
            assert params.get("resource_type") == expected_type, \
                f"Failed for '{user_request}': expected {expected_type}, got {params.get('resource_type')}"
            
            # Verify search works
            results = self.search_service.search(
                params["query"],
                limit=params.get("limit", 10),
                resource_type=params["resource_type"]
            )
            
            assert results is not None
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_peer_reviewed_parameter_extraction(self):
        """Test extraction of peer_reviewed parameter."""
        test_cases = [
            ("Find peer reviewed articles on AI", "true"),
            ("I need articles about climate change with peer review only", "true"),
            ("Get me 5 articles on robotics", "false"),  # No peer review mentioned
            ("Find theses on quantum computing with peer review only", "true")
        ]
        
        for user_request, expected_peer_reviewed in test_cases:
            conversation = [{"role": "user", "content": user_request}]
            params = self.analyzer.extract_search_parameters(conversation)
            
            assert "peer_reviewed" in params, f"Missing peer_reviewed for '{user_request}'"
            assert params.get("peer_reviewed") == expected_peer_reviewed, \
                f"Failed for '{user_request}': expected {expected_peer_reviewed}, got {params.get('peer_reviewed')}"
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_journal_vs_journal_article_distinction(self):
        """Test distinction between 'journals' and 'journal articles'."""
        # "journal articles" should map to "article"
        conversation1 = [{"role": "user", "content": "I want 3 journal articles about AI"}]
        params1 = self.analyzer.extract_search_parameters(conversation1)
        assert params1.get("resource_type") == "article", \
            "Journal articles should map to 'article' resource type"
        
        # "journals" should map to "journal"
        conversation2 = [{"role": "user", "content": "I need 5 journals about machine learning"}]
        params2 = self.analyzer.extract_search_parameters(conversation2)
        assert params2.get("resource_type") == "journal", \
            "Journals should map to 'journal' resource type"
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_dissertations_thesis_search(self):
        """Test searching for dissertations and theses."""
        conversation = [
            {"role": "user", "content": "Find theses on quantum computing"}
        ]
        
        params = self.analyzer.extract_search_parameters(conversation)
        
        assert params.get("resource_type") == "dissertations"
        
        # Perform search
        results = self.search_service.search(
            params["query"],
            limit=params.get("limit", 10),
            resource_type=params["resource_type"]
        )
        
        assert results is not None
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_default_limit_when_not_specified(self):
        """Test that limit defaults to 10 when not specified."""
        conversation = [
            {"role": "user", "content": "Show me research on diabetes"}
        ]
        
        params = self.analyzer.extract_search_parameters(conversation)
        
        # Should default to 10 if not specified
        assert params.get("limit") == 10
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_null_resource_type_when_not_specified(self):
        """Test that resource_type is null when not specified."""
        conversation = [
            {"role": "user", "content": "Search for machine learning research"}
        ]
        
        params = self.analyzer.extract_search_parameters(conversation)
        
        # Should be null or None when not specified
        assert params.get("resource_type") in [None, "null", ""]
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_off_topic_query_redirect(self):
        """Test that off-topic queries are redirected to research assistance."""
        off_topic_queries = [
            "What's the weather today?",
            "Tell me a joke",
            "How are you doing?"
        ]
        
        redirect_message = "scholarly research assistant"
        
        for query in off_topic_queries:
            conversation = [{"role": "user", "content": query}]
            response = self.analyzer.get_follow_up_response(conversation)
            
            assert response is not None
            # Should redirect to research assistance
            assert redirect_message.lower() in response.lower() or \
                   "research topic" in response.lower(), \
                   f"Failed to redirect off-topic query: '{query}'"
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_simple_query_extraction(self):
        """Test that queries are simplified without Boolean operators."""
        conversation = [
            {"role": "user", "content": "I need articles about machine learning in healthcare"}
        ]
        
        params = self.analyzer.extract_search_parameters(conversation)
        query = params.get("query", "")
        
        # Should be simple terms, no complex Boolean operators
        assert "AND" not in query.upper()
        assert "OR" not in query.upper()
        assert "machine learning" in query.lower() or "healthcare" in query.lower()
