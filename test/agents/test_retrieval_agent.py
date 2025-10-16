# test/agents/test_retrieval_agent.py
import unittest
from unittest.mock import patch
from agents import retrieval_agent
from core.schemas import ArticleBrief


class TestRetrievalAgent(unittest.TestCase):
    def setUp(self):
        self.sample_doc = {
            "id": "01CALS_USB_alma9912345678901234",
            "pnx": {
                "display": {
                    "title": ["Sample Article Title"],
                    "creator": ["Doe, Jane", "Smith, John"],
                },
                "sort": {
                    "creationdate": ["2021"]
                },
                "control": {
                    "recordid": ["01CALS_USB_alma9912345678901234"]
                }
            },
            "link": {
                "record": "https://example.org/permalink/01CALS_USB_alma9912345678901234"
            },
            "context": "PC",
        }

        self.sample_brief = ArticleBrief(
            record_id="01CALS_USB_alma9912345678901234",
            title="Sample Article Title",
            creators=["Doe, Jane", "Smith, John"],
            creation_date="2021",
            resource_type="article",
            context="PC",
            permalink="https://example.org/permalink/01CALS_USB_alma9912345678901234",
        )

    def test_brief_from_doc(self):
        brief = retrieval_agent._brief_from_doc(self.sample_doc)
        self.assertIsInstance(brief, ArticleBrief)
        self.assertEqual(brief.record_id, self.sample_brief.record_id)
        self.assertEqual(brief.title, self.sample_brief.title)
        self.assertEqual(brief.creators, self.sample_brief.creators)
        self.assertEqual(brief.creation_date, self.sample_brief.creation_date)
        self.assertEqual(brief.resource_type, "article")
        self.assertEqual(brief.context, "PC")
        self.assertTrue(brief.permalink and brief.permalink.startswith("http"))

    @patch("agents.retrieval_agent.search_with_filters")
    def test_search_articles(self, mock_search):
        mock_search.return_value = {"docs": [self.sample_doc]}
        results = retrieval_agent.search_articles("climate change", n=1)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ArticleBrief)
        self.assertEqual(results[0].record_id, self.sample_brief.record_id)
        # ensure the search was called with expected filters
        mock_search.assert_called_once()
        kwargs = mock_search.call_args.kwargs
        self.assertEqual(kwargs["query"], "climate change")
        self.assertEqual(kwargs["limit"], 1)
        self.assertIn("rtypes", kwargs)

    @patch("agents.retrieval_agent.fetch_full_with_fallback")
    def test_fetch_pnx_for_briefs(self, mock_fetch):
        mock_fetch.return_value = {
            "pnx": {"display": {"title": ["Sample Article Title"]}},
            "link": {"record": self.sample_brief.permalink},
        }
        records = retrieval_agent.fetch_pnx_for_briefs([self.sample_brief])
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["id"], self.sample_brief.record_id)
        self.assertIn("brief", rec)
        self.assertIn("pnx", rec)
        self.assertIn("links", rec)
        self.assertIsInstance(rec["brief"], dict)
        mock_fetch.assert_called_once_with(self.sample_brief.record_id, context_hint="PC")

    @patch("agents.retrieval_agent.append_records")
    @patch("agents.retrieval_agent.fetch_pnx_for_briefs")
    def test_export_briefs_with_pnx(self, mock_fetch_pnx, mock_append):
        fake_records = [
            {"id": self.sample_brief.record_id, "brief": self.sample_brief.model_dump(), "pnx": {}, "links": {}, "raw": {}
            }
        ]
        mock_fetch_pnx.return_value = fake_records
        mock_append.return_value = 1

        wrote = retrieval_agent.export_briefs_with_pnx([self.sample_brief])
        self.assertEqual(wrote, 1)
        mock_fetch_pnx.assert_called_once()
        mock_append.assert_called_once_with(fake_records)


if __name__ == '__main__':
    unittest.main(verbosity=2)
