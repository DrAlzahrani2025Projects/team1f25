"""
Unit tests for peer-review filtering functionality.
Tests CSUSBLibraryClient, ResultFormatter, and ConversationAnalyzer.
"""
import pytest
from unittest.mock import patch, MagicMock
from core.clients.csusb_library_client import CSUSBLibraryClient
from core.services.result_formatter import ResultFormatter
from core.services.conversation_analyzer import ConversationAnalyzer


class TestCSUSBLibraryClientPeerReview:
    """Test CSUSBLibraryClient peer-review filter handling."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = CSUSBLibraryClient()
    
    def test_search_with_peer_review_filter(self):
        """Test that peer_reviewed_only adds correct facet filter."""
        # Mock the session's get method directly on the client instance
        with patch.object(self.client.session, 'get') as mock_get:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"docs": [], "info": {"total": 0}}
            mock_response.url = "http://test.com"
            mock_get.return_value = mock_response
            
            # Call search with peer_reviewed_only=True
            self.client.search("test query", peer_reviewed_only=True)
            
            # Verify that get was called
            assert mock_get.called
            
            # Get the call arguments
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            
            # Verify qInclude param contains peer-review facet
            assert 'qInclude' in params, f"qInclude not found in params: {params}"
            qinclude = params['qInclude']
            assert "facet_tlevel,exact,peer_reviewed" in qinclude
    
    def test_search_with_multiple_filters(self):
        """Test peer_reviewed_only with resource_type filter."""
        # Mock the session's get method directly on the client instance
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"docs": [], "info": {"total": 0}}
            mock_response.url = "http://test.com"
            mock_get.return_value = mock_response
            
            # Call search with both filters
            self.client.search(
                "test query", 
                resource_type="article",
                peer_reviewed_only=True
            )
            
            # Verify that get was called
            assert mock_get.called
            
            # Get call arguments
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            
            # Verify both facets are included
            assert 'qInclude' in params, f"qInclude not found in params: {params}"
            qinclude = params['qInclude']
            
            # Both filters should be in the qInclude parameter
            assert "facet_rtype,exact,articles" in qinclude, f"Article filter not found in: {qinclude}"
            assert "facet_tlevel,exact,peer_reviewed" in qinclude, f"Peer review filter not found in: {qinclude}"


class TestResultFormatterPeerReview:
    """Test ResultFormatter peer-review status extraction."""
    
    def test_parse_peer_reviewed_document(self):
        """Test parsing document with peer-review status."""
        doc = {
            "pnx": {
                "display": {
                    "title": ["Test Title"],
                    "creator": ["Test Author"],
                    "type": ["article"],
                },
                "facets": {
                    "tlevel": ["peer_reviewed"]
                },
                "control": {
                    "recordid": ["test123"]
                }
            }
        }
        
        result = ResultFormatter.parse_document(doc)
        assert result["peer_reviewed"] == "Yes"
    
    def test_parse_non_peer_reviewed_document(self):
        """Test parsing document without peer-review status."""
        doc = {
            "pnx": {
                "display": {
                    "title": ["Test Title"],
                    "creator": ["Test Author"],
                    "type": ["article"],
                },
                "facets": {
                    "tlevel": ["online_resources"]
                },
                "control": {
                    "recordid": ["test123"]
                }
            }
        }
        
        result = ResultFormatter.parse_document(doc)
        assert result["peer_reviewed"] == "No"
    
    def test_parse_document_missing_facets(self):
        """Test parsing document with missing facets section."""
        doc = {
            "pnx": {
                "display": {
                    "title": ["Test Title"],
                    "creator": ["Test Author"],
                    "type": ["article"],
                },
                "control": {
                    "recordid": ["test123"]
                }
            }
        }
        
        result = ResultFormatter.parse_document(doc)
        assert result["peer_reviewed"] == "No"


class TestConversationAnalyzerPeerReview:
    """Test ConversationAnalyzer peer-review detection."""
    
    def test_fallback_extraction_peer_review_keywords(self):
        """Test heuristic detection of peer-review intent."""
        analyzer = ConversationAnalyzer(None, None)  # LLM not needed for fallback
        
        test_messages = [
            (["I need peer-reviewed articles on AI"], True),
            (["Find scholarly research on medicine"], True),
            (["Get me refereed publications"], True),
            (["Show me credible academic sources"], True),
            (["Find articles about robots"], False),
            (["Get me some books"], False),
        ]
        
        for messages, expected in test_messages:
            conversation = [{"role": "user", "content": msg} for msg in messages]
            params = analyzer._fallback_extraction(conversation)
            assert params["peer_reviewed_only"] == expected, f"Failed for: {messages[0]}"