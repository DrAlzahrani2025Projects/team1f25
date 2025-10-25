"""
Integration tests for CSUSB Library Client.
Tests actual API communication (requires network connection).
"""
import pytest
from core.clients.csusb_library_client import CSUSBLibraryClient, explore_search


class TestCSUSBLibraryClientIntegration:
    """Integration tests for CSUSB Library API."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = CSUSBLibraryClient()
    
    @pytest.mark.integration
    def test_search_basic_query(self):
        """Test basic search query."""
        results = self.client.search("machine learning", limit=5)
        
        assert results is not None
        assert "docs" in results
        assert "info" in results
        assert len(results["docs"]) > 0
    
    @pytest.mark.integration
    def test_search_with_article_filter(self):
        """Test search with article resource type filter."""
        results = self.client.search(
            "machine learning healthcare",
            limit=5,
            resource_type="article"
        )
        
        assert results is not None
        docs = results.get("docs", [])
        assert len(docs) > 0
        
        # Verify docs contain article types
        for doc in docs[:3]:  # Check first 3
            doc_type = doc.get("pnx", {}).get("display", {}).get("type", [""])[0]
            assert "article" in doc_type.lower() or "review" in doc_type.lower()
    
    @pytest.mark.integration
    def test_search_with_book_filter(self):
        """Test search with book resource type filter."""
        results = self.client.search(
            "machine learning",
            limit=5,
            resource_type="book"
        )
        
        assert results is not None
        docs = results.get("docs", [])
        assert len(docs) > 0
    
    @pytest.mark.integration
    def test_search_returns_proper_structure(self):
        """Test that search returns expected data structure."""
        results = self.client.search("climate change", limit=3)
        
        assert "docs" in results
        assert "info" in results
        assert "total" in results["info"]
        
        if len(results["docs"]) > 0:
            doc = results["docs"][0]
            assert "pnx" in doc
            assert "display" in doc["pnx"]
    
    @pytest.mark.integration
    def test_legacy_explore_search_function(self):
        """Test backward compatibility with legacy function."""
        results = explore_search("artificial intelligence", limit=3)
        
        assert results is not None
        assert "docs" in results
        assert len(results["docs"]) > 0
    
    @pytest.mark.integration
    def test_search_with_offset(self):
        """Test search with offset parameter."""
        results = self.client.search("education", limit=5, offset=5)
        
        assert results is not None
        assert "docs" in results
    
    @pytest.mark.integration
    def test_search_empty_results_handling(self):
        """Test handling of queries with no results."""
        # Use a very specific query unlikely to return results
        results = self.client.search("xyzabc123nonexistentquery", limit=5)
        
        assert results is not None
        assert "docs" in results
        # May return 0 or few results
