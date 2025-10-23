import os
import sys
import unittest
from unittest.mock import patch

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import retrieval_agent
from core.schemas import SearchBrief


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

    # Additional test cases for _as_str_first
    def test_as_str_first_edge_cases(self):
        self.assertEqual(retrieval_agent._as_str_first(None), "")
        self.assertEqual(retrieval_agent._as_str_first("test"), "test")
        self.assertEqual(retrieval_agent._as_str_first([]), "")
        self.assertEqual(retrieval_agent._as_str_first([[]]), "")
        self.assertEqual(retrieval_agent._as_str_first(["value"]), "value")
        self.assertEqual(retrieval_agent._as_str_first([["nested"]]), "nested")
        self.assertEqual(retrieval_agent._as_str_first([[["deeply nested"]]]), "deeply nested")
        self.assertEqual(retrieval_agent._as_str_first(123), "123")
        self.assertEqual(retrieval_agent._as_str_first([456]), "456")

    # Additional test cases for _brief_from_doc
    def test_brief_from_doc_minimal_doc(self):
        minimal_doc = {
            "id": "MIN1",
            "pnx": {},
            "link": {},
            "context": "PC"
        }
        brief = retrieval_agent._brief_from_doc(minimal_doc)
        self.assertEqual(brief.record_id, "MIN1")
        self.assertEqual(brief.title, "Untitled")
        self.assertEqual(brief.creators, [])
        self.assertEqual(brief.resource_type, "article")  # default

    def test_brief_from_doc_missing_fields(self):
        doc = {
            "id": "TEST1",
            "pnx": {
                "display": {},
                "sort": {},
                "control": {}
            }
        }
        brief = retrieval_agent._brief_from_doc(doc)
        self.assertEqual(brief.record_id, "TEST1")
        self.assertEqual(brief.title, "Untitled")
        self.assertEqual(brief.creation_date, "")

    def test_brief_from_doc_complex_date_formats(self):
        # Test various date formats
        doc1 = {
            "id": "D1",
            "pnx": {
                "display": {"title": ["T"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["20200315"]},
                "control": {"recordid": ["D1"]},
            },
            "context": "PC"
        }
        brief1 = retrieval_agent._brief_from_doc(doc1)
        self.assertEqual(brief1.creation_date, "2020")

        doc2 = {
            "id": "D2",
            "pnx": {
                "display": {"title": ["T"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["1999"]},
                "control": {"recordid": ["D2"]},
            },
            "context": "PC"
        }
        brief2 = retrieval_agent._brief_from_doc(doc2)
        self.assertEqual(brief2.creation_date, "1999")

    def test_brief_from_doc_multiple_creators(self):
        doc = {
            "id": "MC1",
            "pnx": {
                "display": {"title": ["Multi Author Paper"], "type": ["article"]},
                "sort": {"author": ["Smith, John", "Doe, Jane", "Lee, Bob"], "creationdate": ["2021"]},
                "control": {"recordid": ["MC1"]},
            },
            "context": "L"
        }
        brief = retrieval_agent._brief_from_doc(doc)
        self.assertEqual(len(brief.creators), 3)
        self.assertIn("Smith, John", brief.creators)
        self.assertIn("Doe, Jane", brief.creators)

    def test_brief_from_doc_context_variations(self):
        doc = {
            "id": "CTX1",
            "pnx": {
                "display": {"title": ["T"], "creator": ["A"], "type": ["book"]},
                "sort": {"creationdate": ["2018"]},
                "control": {"recordid": ["CTX1"]},
            },
            "context": "L"
        }
        brief = retrieval_agent._brief_from_doc(doc)
        self.assertEqual(brief.context, "L")
        self.assertIn("context=L", brief.permalink)

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_default_params(self, mock_search):
        mock_search.return_value = {"docs": []}
        _ = retrieval_agent.search("test")
        kwargs = mock_search.call_args.kwargs
        self.assertEqual(kwargs["query"], "test")
        self.assertEqual(kwargs["limit"], 10)
        self.assertFalse(kwargs["peer_reviewed"])
        self.assertEqual(kwargs["sort"], "rank")

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_with_authors_param(self, mock_search):
        mock_search.return_value = {"docs": []}
        _ = retrieval_agent.search("AI", authors=["Turing", "Lovelace"])
        kwargs = mock_search.call_args.kwargs
        self.assertEqual(kwargs["authors"], ["Turing", "Lovelace"])

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_empty_response(self, mock_search):
        mock_search.return_value = {}
        briefs = retrieval_agent.search("empty query")
        self.assertEqual(len(briefs), 0)

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_multiple_docs(self, mock_search):
        mock_docs = [
            {
                "id": f"DOC{i}",
                "pnx": {
                    "display": {"title": [f"Title {i}"], "creator": ["Author"], "type": ["article"]},
                    "sort": {"creationdate": ["2020"]},
                    "control": {"recordid": [f"DOC{i}"]},
                },
                "context": "PC"
            }
            for i in range(5)
        ]
        mock_search.return_value = {"docs": mock_docs}
        briefs = retrieval_agent.search("test", n=5)
        self.assertEqual(len(briefs), 5)
        for i, brief in enumerate(briefs):
            self.assertEqual(brief.record_id, f"DOC{i}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
