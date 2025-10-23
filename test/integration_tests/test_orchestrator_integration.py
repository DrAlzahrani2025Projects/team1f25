import os
import sys
import unittest
from unittest.mock import patch

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import orchestrator_agent
from core.schemas import AgentInput


class TestOrchestratorIntegration(unittest.TestCase):
    def _sample_docs(self):
        return [
            {
                "id": "01CALS_USB_alma9911111111111111",
                "pnx": {
                    "display": {
                        "title": ["First Sample Title"],
                        "creator": ["Alpha, Ann"],
                        # display.type differs from search.rtype to test preference order
                        "type": ["book"],
                    },
                    "sort": {"creationdate": ["2021"]},
                    "search": {"rtype": ["journal"]},
                    "control": {"recordid": ["01CALS_USB_alma9911111111111111"]},
                },
                "link": {"record": "https://example.org/permalink/01CALS_USB_alma9911111111111111"},
                "context": "PC",
            },
            {
                "id": "01CALS_USB_alma9922222222222222",
                "pnx": {
                    "display": {
                        "title": ["Second Sample Title"],
                        "creator": ["Beta, Bob"],
                        "type": ["article"],
                    },
                    "sort": {"creationdate": ["2020"]},
                    "search": {},
                    "control": {"recordid": ["01CALS_USB_alma9922222222222222"]},
                },
                "link": {"record": "https://example.org/permalink/01CALS_USB_alma9922222222222222"},
                "context": "PC",
            },
        ]

    @patch("core.csusb_library_client.explore_search")
    def test_handle_returns_formatted_list_and_briefs(self, mock_explore):
        # Always return two docs regardless of q/params
        mock_explore.return_value = {"docs": self._sample_docs()}

        input_text = "List top 2 articles on climate change"
        out = orchestrator_agent.handle(AgentInput(user_input=input_text))

        self.assertTrue(out.text.startswith("Top 2 results for"))
        self.assertIn("climate change", out.text)
        self.assertEqual(len(out.briefs), 2)
        # Titles should appear in the formatted text
        self.assertIn("First Sample Title", out.text)
        self.assertIn("Second Sample Title", out.text)
        # Resource type is carried through in briefs
        self.assertEqual(out.briefs[0].resource_type, "journal")  # from search.rtype
        self.assertEqual(out.briefs[1].resource_type, "article")  # from display.type

    @patch("core.csusb_library_client.explore_search")
    def test_type_filter_embedded_in_q(self, mock_explore):
        captured = {}

        def side_effect(*, q=None, limit=10, offset=0, query=None, sort="rank"):
            captured["q"] = q
            captured["limit"] = limit
            captured["sort"] = sort
            return {"docs": self._sample_docs()[:1]}  # one doc is enough

        mock_explore.side_effect = side_effect

        input_text = "Show top 1 journal articles about AI"
        out = orchestrator_agent.handle(AgentInput(user_input=input_text))

        self.assertTrue(out.text.startswith("Top 1 results for"))
        # Verify rtype facet was embedded by the pipeline into the q string
        # For phrase "journal articles", the pipeline selects 'articles' (Primo facet)
        self.assertIn("rtype,exact,articles", captured.get("q", ""))
        # Also ensure language facet appears (added by our search)
        self.assertIn("lang,exact,eng", captured.get("q", ""))

    @patch("core.csusb_library_client.explore_search")
    def test_authors_date_peerreview_in_q_and_params(self, mock_explore):
        captured = {}

        def side_effect(*, q=None, limit=10, offset=0, query=None, sort="rank"):
            captured["q"], captured["limit"] = q, limit
            return {"docs": self._sample_docs()[:1]}

        mock_explore.side_effect = side_effect

        input_text = "Show top 3 peer-reviewed articles by Andrew Ng and Yann LeCun between 2018 and 2020"
        out = orchestrator_agent.handle(AgentInput(user_input=input_text))
        self.assertTrue(out.text.startswith("Top 1 results for") or out.text.startswith("Top 3 results for"))
        # creators included via build_q
        self.assertIn("creator,contains,Andrew Ng", captured.get("q", ""))
        self.assertIn("creator,contains,Yann LeCun", captured.get("q", ""))
        # ensure no stray years are included as creators
        self.assertNotIn("creator,contains,2018", captured.get("q", ""))
        self.assertNotIn("creator,contains,2020", captured.get("q", ""))
        # peer reviewed facet
        self.assertIn("facet_tlevel,exact,peer_reviewed", captured.get("q", ""))
        # date range now in query clauses instead of URL params
        self.assertIn("dr_s,exact,20180101", captured.get("q", ""))
        self.assertIn("dr_e,exact,20201231", captured.get("q", ""))

    @patch("core.csusb_library_client.explore_search")
    def test_book_chapter_type_and_limit_clamp(self, mock_explore):
        captured = {}

        def side_effect(*, q=None, limit=10, offset=0, query=None, sort="rank"):
            captured["q"] = q
            captured["limit"] = limit
            captured["sort"] = sort
            return {"docs": self._sample_docs()[:1]}

        mock_explore.side_effect = side_effect

        # Ask for top 0 to ensure clamp to 1; also target book chapters parsing
        input_text = "List top 0 book chapters on AI"
        out = orchestrator_agent.handle(AgentInput(user_input=input_text))

        self.assertTrue(out.text.startswith("Top 1 results for"))
        self.assertEqual(captured.get("limit"), 1)
        self.assertIn("rtype,exact,book_chapters", captured.get("q", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
