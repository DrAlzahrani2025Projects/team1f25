"""
Integration tests for search service with real library API.
Tests the complete search flow with actual external calls.
"""
import pytest
from core.services.search_service import SearchService, perform_library_search
from core.clients.csusb_library_client import CSUSBLibraryClient
from core.services.result_formatter import ResultFormatter


class TestSearchServiceIntegration:
    """Integration tests for SearchService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = CSUSBLibraryClient()
        self.formatter = ResultFormatter()
        self.service = SearchService(self.client, self.formatter)
    
    @pytest.mark.integration
    def test_search_basic(self):
        """Test basic search through service."""
        results = self.service.search("machine learning", limit=5)
        
        assert results is not None
        assert len(results.get("docs", [])) > 0
    
    @pytest.mark.integration
    def test_search_with_article_filter(self):
        """Test search with article type filter."""
        results = self.service.search(
            "healthcare",
            limit=5,
            resource_type="article"
        )
        
        assert results is not None
        docs = results.get("docs", [])
        assert len(docs) > 0
    
    @pytest.mark.integration
    def test_search_with_book_filter(self):
        """Test search with book type filter."""
        results = self.service.search(
            "artificial intelligence",
            limit=5,
            resource_type="book"
        )
        
        assert results is not None
        docs = results.get("docs", [])
        assert len(docs) > 0
    
    @pytest.mark.integration
    def test_parse_results(self):
        """Test result parsing through service."""
        results = self.service.search("climate change", limit=3)
        parsed = self.service.parse_results(results)
        
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        
        # Check parsed structure
        if len(parsed) > 0:
            item = parsed[0]
            assert "title" in item
            assert "author" in item
            assert "date" in item
            assert "type" in item
    
    @pytest.mark.integration
    def test_legacy_perform_library_search(self):
        """Test backward compatibility with legacy function."""
        results = perform_library_search("education", limit=5)
        
        assert results is not None
        assert "docs" in results
    
    @pytest.mark.integration
    def test_different_resource_types(self):
        """Test searching for different resource types."""
        query = "machine learning"
        
        # Test articles
        articles = self.service.search(query, limit=3, resource_type="article")
        assert len(articles.get("docs", [])) > 0
        
        # Test books
        books = self.service.search(query, limit=3, resource_type="book")
        assert len(books.get("docs", [])) > 0
    
    @pytest.mark.integration
    def test_search_with_various_limits(self):
        """Test search with different limit values."""
        query = "computer science"
        
        for limit in [1, 5, 10]:
            results = self.service.search(query, limit=limit)
            docs = results.get("docs", [])
            assert len(docs) > 0
            assert len(docs) <= limit
