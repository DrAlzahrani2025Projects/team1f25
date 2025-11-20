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
        # LLM should extract limit, but may use default
        assert params.get("limit") in [5, 10]  # Either extracted or default
        assert params.get("resource_type") == "article"
        
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
        
        # LLM should extract limit, but may use default
        assert params.get("limit") in [3, 10]  # Either extracted or default
        assert params.get("resource_type") == "book"
        
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
        # First message
        conversation = [
            {"role": "user", "content": "I want to research machine learning"}
        ]
        
        # Get follow-up question
        response = self.analyzer.get_follow_up_response(conversation)
        
        assert response is not None
        assert len(response) > 0
        
        # Check if ready to search or needs more info
        if "READY_TO_SEARCH" not in response:
            # Add follow-up
            conversation.append({"role": "assistant", "content": response})
            conversation.append({"role": "user", "content": "I want articles"})
            
            response = self.analyzer.get_follow_up_response(conversation)
        
        # Eventually should be ready or continue conversation
        assert response is not None
    
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
            ("Show me 2 journals about medicine", "article")  # journals now map to article
        ]
        
        for user_request, expected_type in test_cases:
            conversation = [{"role": "user", "content": user_request}]
            params = self.analyzer.extract_search_parameters(conversation)
            
            assert params.get("resource_type") == expected_type
            
            # Verify search works
            results = self.search_service.search(
                params["query"],
                limit=params["limit"],
                resource_type=params["resource_type"]
            )
            
            assert results is not None
