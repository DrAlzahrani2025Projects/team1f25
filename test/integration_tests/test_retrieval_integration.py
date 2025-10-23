import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import retrieval_agent
from core.schemas import SearchBrief


class TestRetrievalIntegration(unittest.TestCase):
    """Integration tests for retrieval_agent with mocked Primo API."""

    def _mock_primo_docs(self, count=3):
        """Generate mock Primo API response documents."""
        docs = []
        for i in range(count):
            docs.append({
                "id": f"RID{i}",
                "pnx": {
                    "display": {
                        "title": [f"Test Article {i}"],
                        "creator": [f"Author{i}, First"],
                        "type": ["article"],
                    },
                    "sort": {
                        "creationdate": [f"202{i}"],
                        "author": [f"Author{i}, First", f"Coauthor{i}, Second"],
                    },
                    "search": {"rtype": ["journal"]},
                    "control": {"recordid": [f"RID{i}"]},
                },
                "link": {"record": f"https://example.org/rid{i}"},
                "context": "PC",
            })
        return docs

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_returns_briefs(self, mock_search):
        """Test that search returns properly formatted SearchBrief objects."""
        mock_search.return_value = {"docs": self._mock_primo_docs(5)}
        
        results = retrieval_agent.search("machine learning", n=5)
        
        self.assertEqual(len(results), 5)
        self.assertIsInstance(results[0], SearchBrief)
        self.assertEqual(results[0].title, "Test Article 0")
        self.assertEqual(results[0].resource_type, "journal")

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_all_parameters(self, mock_search):
        """Test search with all optional parameters populated."""
        mock_search.return_value = {"docs": self._mock_primo_docs(2)}
        
        results = retrieval_agent.search(
            query="quantum physics",
            n=2,
            peer_reviewed=True,
            sort="date",
            year_from=2015,
            year_to=2020,
            search_type="articles",
            authors=["Einstein", "Bohr"]
        )
        
        # Verify search_with_filters was called with correct params
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        self.assertEqual(call_kwargs["query"], "quantum physics")
        self.assertEqual(call_kwargs["limit"], 2)
        self.assertTrue(call_kwargs["peer_reviewed"])
        self.assertEqual(call_kwargs["sort"], "date")
        self.assertEqual(call_kwargs["year_from"], 2015)
        self.assertEqual(call_kwargs["year_to"], 2020)
        self.assertEqual(call_kwargs["rtypes"], ["articles"])
        self.assertEqual(call_kwargs["authors"], ["Einstein", "Bohr"])
        
        # Verify results
        self.assertEqual(len(results), 2)

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_no_results(self, mock_search):
        """Test search handles empty results gracefully."""
        mock_search.return_value = {"docs": []}
        
        results = retrieval_agent.search("nonexistent topic xyz", n=10)
        
        self.assertEqual(len(results), 0)
        self.assertIsInstance(results, list)

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_malformed_docs(self, mock_search):
        """Test search handles malformed documents."""
        # Document with missing fields
        malformed_docs = [
            {
                "id": "MAL1",
                "pnx": {
                    "display": {},  # Empty display
                    "sort": {},
                    "control": {},
                },
                "context": "PC"
            }
        ]
        mock_search.return_value = {"docs": malformed_docs}
        
        results = retrieval_agent.search("test", n=1)
        
        self.assertEqual(len(results), 1)
        # Should have default values
        self.assertEqual(results[0].title, "Untitled")
        self.assertEqual(results[0].creators, [])
        self.assertEqual(results[0].resource_type, "article")

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_year_normalization(self, mock_search):
        """Test that years are normalized from YYYYMMDD to YYYY."""
        docs = [{
            "id": "YR1",
            "pnx": {
                "display": {"title": ["Year Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["20231015"]},  # YYYYMMDD format
                "control": {"recordid": ["YR1"]},
            },
            "context": "PC"
        }]
        mock_search.return_value = {"docs": docs}
        
        results = retrieval_agent.search("test", n=1)
        
        self.assertEqual(results[0].creation_date, "2023")  # Should be normalized

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_prefers_search_rtype_over_display_type(self, mock_search):
        """Test that search.rtype is preferred over display.type."""
        docs = [{
            "id": "RT1",
            "pnx": {
                "display": {"title": ["Type Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "search": {"rtype": ["book"]},  # Should win
                "control": {"recordid": ["RT1"]},
            },
            "context": "PC"
        }]
        mock_search.return_value = {"docs": docs}
        
        results = retrieval_agent.search("test", n=1)
        
        self.assertEqual(results[0].resource_type, "book")

    @patch("agents.retrieval_agent.search_with_filters")
    def test_onesearch_alias_compatibility(self, mock_search):
        """Test that onesearch is a proper alias for search."""
        mock_search.return_value = {"docs": self._mock_primo_docs(3)}
        
        results = retrieval_agent.onesearch(
            "test query",
            n=3,
            peer_reviewed=True,
            sort="date",
            year_from=2000,
            year_to=2023,
            search_type="books",
            authors=["Smith"]
        )
        
        # Verify it calls search_with_filters correctly
        self.assertEqual(len(results), 3)
        call_kwargs = mock_search.call_args.kwargs
        self.assertEqual(call_kwargs["query"], "test query")
        self.assertEqual(call_kwargs["limit"], 3)
        self.assertTrue(call_kwargs["peer_reviewed"])
        self.assertEqual(call_kwargs["rtypes"], ["books"])
        self.assertEqual(call_kwargs["authors"], ["Smith"])

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_multiple_creators(self, mock_search):
        """Test that multiple creators are properly extracted."""
        docs = [{
            "id": "MC1",
            "pnx": {
                "display": {"title": ["Multi-author"], "type": ["article"]},
                "sort": {
                    "creationdate": ["2023"],
                    "author": ["Smith, John", "Doe, Jane", "Lee, Bob"]
                },
                "control": {"recordid": ["MC1"]},
            },
            "context": "PC"
        }]
        mock_search.return_value = {"docs": docs}
        
        results = retrieval_agent.search("test", n=1)
        
        self.assertEqual(len(results[0].creators), 3)
        self.assertIn("Smith, John", results[0].creators)
        self.assertIn("Doe, Jane", results[0].creators)
        self.assertIn("Lee, Bob", results[0].creators)

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_different_contexts(self, mock_search):
        """Test that different context values are preserved."""
        docs = [
            {
                "id": "CTX1",
                "pnx": {
                    "display": {"title": ["Context L"], "creator": ["A"], "type": ["book"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": ["CTX1"]},
                },
                "context": "L"  # Different context
            },
            {
                "id": "CTX2",
                "pnx": {
                    "display": {"title": ["Context PC"], "creator": ["B"], "type": ["article"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": ["CTX2"]},
                },
                "context": "PC"
            }
        ]
        mock_search.return_value = {"docs": docs}
        
        results = retrieval_agent.search("test", n=2)
        
        self.assertEqual(results[0].context, "L")
        self.assertEqual(results[1].context, "PC")
        self.assertIn("context=L", results[0].permalink)
        self.assertIn("context=PC", results[1].permalink)


if __name__ == "__main__":
    unittest.main(verbosity=2)
