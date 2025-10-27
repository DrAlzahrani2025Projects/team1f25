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
    
    @patch('core.clients.csusb_library_client.S')
    def test_search_with_peer_review_filter(self, mock_session):
        """Test that peer_reviewed_only adds correct facet filter."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"docs": [], "info": {"total": 0}}
        mock_session.get.return_value = mock_response
        
        # Call search with peer_reviewed_only=True
        self.client.search("test query", peer_reviewed_only=True)
        
        # Get the actual URL that would have been requested
        called_url = mock_session.get.call_args[1]['params']
        
        # Verify qInclude param contains peer-review facet
        assert 'qInclude' in called_url
        qinclude = called_url['qInclude']
        if isinstance(qinclude, list):
            assert "facet_tlevel,exact,peer_reviewed" in qinclude
        else:
            assert "facet_tlevel,exact,peer_reviewed" in qinclude
    
    @patch('core.clients.csusb_library_client.S')
    def test_search_with_multiple_filters(self, mock_session):
        """Test peer_reviewed_only with resource_type filter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"docs": [], "info": {"total": 0}}
        mock_session.get.return_value = mock_response
        
        # Call search with both filters
        self.client.search(
            "test query", 
            resource_type="article",
            peer_reviewed_only=True
        )
        
        # Verify both facets are included
        called_url = mock_session.get.call_args[1]['params']
        qinclude = called_url['qInclude']
        
        if isinstance(qinclude, list):
            assert any("facet_rtype,exact,articles" in q for q in qinclude)
            assert any("facet_tlevel,exact,peer_reviewed" in q for q in qinclude)
        else:
            assert "facet_rtype,exact,articles" in qinclude
            assert "facet_tlevel,exact,peer_reviewed" in qinclude


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