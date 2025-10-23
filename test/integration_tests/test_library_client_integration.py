import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.csusb_library_client import build_q, search_with_filters


class TestLibraryClientIntegration(unittest.TestCase):
    """Integration tests for CSUSB library client with mocked HTTP calls."""

    def _mock_primo_response(self, doc_count=3):
        """Generate a mock Primo API response."""
        docs = []
        for i in range(doc_count):
            docs.append({
                "id": f"DOC{i}",
                "pnx": {
                    "display": {"title": [f"Title {i}"], "creator": [f"Author {i}"], "type": ["article"]},
                    "sort": {"creationdate": [f"202{i}"]},
                    "control": {"recordid": [f"DOC{i}"]},
                },
                "context": "PC"
            })
        return {"docs": docs, "info": {"total": doc_count}}

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_basic(self, mock_explore):
        """Test basic search_with_filters functionality."""
        mock_explore.return_value = self._mock_primo_response(5)
        
        result = search_with_filters(
            query="machine learning",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=None,
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        self.assertIn("docs", result)
        self.assertEqual(len(result["docs"]), 5)
        mock_explore.assert_called_once()

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_peer_reviewed(self, mock_explore):
        """Test search with peer-reviewed filter."""
        mock_explore.return_value = self._mock_primo_response(3)
        
        result = search_with_filters(
            query="quantum physics",
            limit=10,
            lang_code="eng",
            peer_reviewed=True,
            rtypes=["articles"],
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        # Check that build_q was called with peer_reviewed=True
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        self.assertIn("facet_tlevel,exact,peer_reviewed", q_param)
        self.assertIn("rtype,exact,articles", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_multiple_types(self, mock_explore):
        """Test search with multiple resource types."""
        mock_explore.return_value = self._mock_primo_response(2)
        
        result = search_with_filters(
            query="climate change",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=["articles", "books"],
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        # Should be called twice (once per type)
        self.assertEqual(mock_explore.call_count, 2)
        self.assertIn("docs", result)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_with_authors(self, mock_explore):
        """Test search with author filter."""
        mock_explore.return_value = self._mock_primo_response(2)
        
        result = search_with_filters(
            query="neural networks",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=None,
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=["Andrew Ng", "Yann LeCun"]
        )
        
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        self.assertIn("creator,contains,Andrew Ng", q_param)
        self.assertIn("creator,contains,Yann LeCun", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_date_range(self, mock_explore):
        """Test search with date range filter."""
        mock_explore.return_value = self._mock_primo_response(3)
        
        result = search_with_filters(
            query="artificial intelligence",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=None,
            year_from=2015,
            year_to=2020,
            sort="date",
            authors=None
        )
        
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        # Date range should be in query as dr_s and dr_e
        self.assertIn("dr_s,exact,20150101", q_param)
        self.assertIn("dr_e,exact,20201231", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_date_swap(self, mock_explore):
        """Test that date range is swapped if year_to < year_from."""
        mock_explore.return_value = self._mock_primo_response(2)
        
        result = search_with_filters(
            query="test",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=None,
            year_from=2020,  # Later year
            year_to=2015,    # Earlier year (should swap)
            sort="rank",
            authors=None
        )
        
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        # Should be swapped: 2015 to 2020
        self.assertIn("dr_s,exact,20150101", q_param)
        self.assertIn("dr_e,exact,20201231", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_deduplication(self, mock_explore):
        """Test that duplicate documents are deduplicated across type searches."""
        # Return the same document twice (simulating overlap between types)
        duplicate_doc = {
            "id": "DUP1",
            "pnx": {
                "display": {"title": ["Duplicate"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["DUP1"]},
            },
            "context": "PC"
        }
        mock_explore.return_value = {"docs": [duplicate_doc]}
        
        result = search_with_filters(
            query="test",
            limit=10,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=["articles", "books"],  # Two types
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        # Should only have 1 document despite being called twice
        self.assertEqual(len(result["docs"]), 1)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_limit_respected(self, mock_explore):
        """Test that result limit is respected."""
        mock_explore.return_value = self._mock_primo_response(20)
        
        result = search_with_filters(
            query="test",
            limit=5,
            lang_code="eng",
            peer_reviewed=False,
            rtypes=None,
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        # Should stop at limit
        self.assertLessEqual(len(result["docs"]), 5)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_no_language(self, mock_explore):
        """Test search without language filter."""
        mock_explore.return_value = self._mock_primo_response(3)
        
        result = search_with_filters(
            query="test",
            limit=5,
            lang_code=None,  # No language filter
            peer_reviewed=False,
            rtypes=None,
            year_from=1900,
            year_to=2100,
            sort="rank",
            authors=None
        )
        
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        # Should not have language filter
        self.assertNotIn("lang,exact,", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_filters_all_parameters(self, mock_explore):
        """Test search with all parameters specified."""
        mock_explore.return_value = self._mock_primo_response(2)
        
        result = search_with_filters(
            query="comprehensive test",
            limit=3,
            lang_code="eng",
            peer_reviewed=True,
            rtypes=["articles"],
            year_from=2018,
            year_to=2023,
            sort="date",
            authors=["Smith, J.", "Doe, J."]
        )
        
        call_args = mock_explore.call_args
        q_param = call_args.kwargs.get("q")
        
        # Verify all filters are in the query
        self.assertIn("comprehensive test", q_param)
        self.assertIn("lang,exact,eng", q_param)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q_param)
        self.assertIn("rtype,exact,articles", q_param)
        self.assertIn("dr_s,exact,20180101", q_param)
        self.assertIn("dr_e,exact,20231231", q_param)
        self.assertIn("creator,contains,Smith, J.", q_param)
        self.assertIn("creator,contains,Doe, J.", q_param)
        
        # Verify sort parameter
        self.assertEqual(call_args.kwargs.get("sort"), "date")

    def test_build_q_structure(self):
        """Test that build_q produces proper query structure."""
        q = build_q(
            "test query",
            lang_code="eng",
            peer_reviewed=True,
            rtype="articles",
            authors=["Author One", "Author Two"],
            dr_s="20200101",
            dr_e="20201231"
        )
        
        # Verify structure with AND separators
        self.assertIn(",AND;", q)
        self.assertIn("any,contains,test query", q)
        self.assertIn("creator,contains,Author One", q)
        self.assertIn("creator,contains,Author Two", q)
        self.assertIn("dr_s,exact,20200101", q)
        self.assertIn("dr_e,exact,20201231", q)
        self.assertIn("lang,exact,eng", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)

    def test_build_q_minimal(self):
        """Test build_q with minimal parameters."""
        q = build_q(
            "simple query",
            lang_code=None,
            peer_reviewed=False,
            rtype=None,
            authors=None,
            dr_s=None,
            dr_e=None
        )
        
        # Should only have the query term
        self.assertIn("any,contains,simple query", q)
        self.assertNotIn("lang,exact,", q)
        self.assertNotIn("facet_tlevel", q)
        self.assertNotIn("rtype,exact,", q)
        self.assertNotIn("creator,contains,", q)
        self.assertNotIn("dr_s,exact,", q)


if __name__ == "__main__":
    unittest.main(verbosity=2)
