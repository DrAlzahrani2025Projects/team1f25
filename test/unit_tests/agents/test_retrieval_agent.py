import os
import sys
import unittest
from unittest.mock import patch

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import retrieval_agent
from core.schemas import SearchBreif


class TestRetrievalAgentUnit(unittest.TestCase):
    def setUp(self):
        self.doc_no_search_rtype = {
            "id": "RID1",
            "pnx": {
                "display": {
                    "title": ["Sample"],
                    "creator": ["Doe, Jane"],
                    "type": ["book"],
                },
                "sort": {"creationdate": ["2022"]},
                "control": {"recordid": ["RID1"]},
            },
            "link": {"record": "https://example.org/rid1"},
            "context": "PC",
        }
        self.doc_with_search_rtype = {
            "id": "RID2",
            "pnx": {
                "display": {
                    "title": ["Sample2"],
                    "creator": ["Smith, John"],
                    "type": ["article"],
                },
                "sort": {"creationdate": ["2021"]},
                "search": {"rtype": ["journal"]},
                "control": {"recordid": ["RID2"]},
            },
            "link": {"record": "https://example.org/rid2"},
            "context": "PC",
        }

    def test_brief_from_doc_type_fallback(self):
        brief = retrieval_agent._brief_from_doc(self.doc_no_search_rtype)
        self.assertEqual(brief.resource_type, "book")

    def test_brief_from_doc_type_prefer_search(self):
        brief = retrieval_agent._brief_from_doc(self.doc_with_search_rtype)
        self.assertEqual(brief.resource_type, "journal")

    def test_brief_from_doc_year_normalization(self):
        # creationdate comes as YYYYMMDD; expect extraction of YYYY only
        doc = {
            "id": "RID4",
            "pnx": {
                "display": {"title": ["T"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["20240101"]},
                "control": {"recordid": ["RID4"]},
            },
            "link": {"record": "https://example.org/rid4"},
            "context": "PC",
        }
        brief = retrieval_agent._brief_from_doc(doc)
        self.assertEqual(brief.creation_date, "2024")

    def test_brief_from_doc_type_default_when_missing(self):
        doc = {
            "id": "RID3",
            "pnx": {
                "display": {"title": ["T"], "creator": ["A"]},
                "sort": {"creationdate": ["2019"]},
                "control": {"recordid": ["RID3"]},
            },
            "link": {"record": "https://example.org/rid3"},
            "context": "PC",
        }
        brief = retrieval_agent._brief_from_doc(doc)
        # default chosen in retrieval agent when no rtype present
        self.assertEqual(brief.resource_type, "article")

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_passes_rtypes_none_when_no_type(self, mock_search):
        mock_search.return_value = {"docs": [self.doc_no_search_rtype]}
        _ = retrieval_agent.search("ai", n=1)
        mock_search.assert_called_once()
        kwargs = mock_search.call_args.kwargs
        self.assertIn("rtypes", kwargs)
        self.assertIsNone(kwargs["rtypes"])  # explicit None when no type

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_passes_rtypes_list_when_type_given(self, mock_search):
        mock_search.return_value = {"docs": [self.doc_with_search_rtype]}
        _ = retrieval_agent.search("ml", n=2, search_type="journal")
        kwargs = mock_search.call_args.kwargs
        self.assertEqual(kwargs["rtypes"], ["journal"])  # list form passed through

    @patch("agents.retrieval_agent.search")
    def test_onesearch_alias(self, mock_search):
        mock_search.return_value = []
        _ = retrieval_agent.onesearch("quantum", n=3, peer_reviewed=True, sort="date", year_from=2000, year_to=2020, search_type="article")
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        self.assertEqual(kwargs["query"], "quantum")
        self.assertEqual(kwargs["n"], 3)
        self.assertTrue(kwargs["peer_reviewed"]) 
        self.assertEqual(kwargs["sort"], "date")
        self.assertEqual(kwargs["year_from"], 2000)
        self.assertEqual(kwargs["year_to"], 2020)
        self.assertEqual(kwargs["search_type"], "article")


if __name__ == "__main__":
    unittest.main(verbosity=2)
