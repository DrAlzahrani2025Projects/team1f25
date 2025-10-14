# test/agents/test_retrieval_agent.py
import unittest
from unittest.mock import patch, MagicMock
from agents import retrieval_agent
from core.schemas import ArticleBrief

class TestRetrievalAgent(unittest.TestCase):

    def setUp(self):
        self.sample_doc = {
            "id": "123",
            "pnx": {
                "control": {"recordid": ["123"]},
                "display": {"creator": ["John Doe"], "title": ["Sample Title"]},
                "sort": {"creationdate": ["2020"]}
            },
            "link": {"record": "http://example.com/123"},
            "context": "PC"
        }
        self.sample_brief = ArticleBrief(
            record_id="123",
            title="Sample Title",
            creators=["John Doe"],
            creation_date="2020",
            resource_type="article",
            context="PC",
            permalink="http://example.com/123"
        )

    def test_brief_from_doc(self):
        brief = retrieval_agent._brief_from_doc(self.sample_doc)
        self.assertEqual(brief.record_id, "123")
        self.assertEqual(brief.title, "Sample Title")
        self.assertEqual(brief.creators, ["John Doe"])
        self.assertEqual(brief.creation_date, "2020")
        self.assertEqual(brief.permalink, "http://example.com/123")

    @patch('agents.retrieval_agent.search_with_filters')
    def test_search_articles(self, mock_search):
        mock_search.return_value = {"docs": [self.sample_doc]}
        results = retrieval_agent.search_articles("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Sample Title")

    @patch('core.csusb_library_client.fetch_full_with_fallback')
    def test_fetch_pnx_for_briefs(self, mock_fetch):
        mock_fetch.return_value = {
            "pnx": {"test": "data"},
            "link": {"record": "http://example.com/123"},
        }
        briefs = [self.sample_brief]
        records = retrieval_agent.fetch_pnx_for_briefs(briefs)
        self.assertEqual(records[0]["id"], "123")
        self.assertIn("pnx", records[0])
        self.assertIn("links", records[0])

    @patch('agents.retrieval_agent.append_records', return_value=1)
    def test_export_briefs_with_pnx(self, mock_append):
        briefs = [self.sample_brief]
        result = retrieval_agent.export_briefs_with_pnx(briefs)
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
