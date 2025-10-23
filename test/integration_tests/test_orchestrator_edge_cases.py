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


class TestOrchestratorEdgeCases(unittest.TestCase):
    """Integration tests for orchestrator edge cases and error scenarios."""

    def _empty_response(self):
        return {"docs": []}

    def _single_doc(self):
        return {
            "docs": [{
                "id": "SINGLE1",
                "pnx": {
                    "display": {"title": ["Single Result"], "creator": ["Author"], "type": ["article"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": ["SINGLE1"]},
                },
                "context": "PC"
            }]
        }

    @patch("core.csusb_library_client.explore_search")
    def test_handle_empty_search_results(self, mock_explore):
        """Test handling when search returns no results."""
        mock_explore.return_value = self._empty_response()
        
        out = orchestrator_agent.handle(AgentInput(user_input="Show articles on nonexistent topic xyz"))
        
        self.assertIn("No results found", out.text)
        self.assertEqual(len(out.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_handle_very_long_query(self, mock_explore):
        """Test handling of very long search queries."""
        mock_explore.return_value = self._single_doc()
        
        long_query = "Show articles about " + ("machine learning " * 50)
        out = orchestrator_agent.handle(AgentInput(user_input=long_query))
        
        # Should handle gracefully without crashing
        self.assertIsNotNone(out.text)
        mock_explore.assert_called_once()

    @patch("core.csusb_library_client.explore_search")
    def test_handle_special_characters_in_query(self, mock_explore):
        """Test handling of special characters in search queries."""
        mock_explore.return_value = self._single_doc()
        
        special_queries = [
            "Find articles on C++ programming",
            "Search for papers about A&B testing",
            "List books on O'Reilly publications",
            "Show articles with 'quotes' and \"double quotes\"",
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                out = orchestrator_agent.handle(AgentInput(user_input=query))
                self.assertIsNotNone(out.text)

    @patch("core.csusb_library_client.explore_search")
    def test_handle_unicode_characters(self, mock_explore):
        """Test handling of unicode characters in queries."""
        mock_explore.return_value = self._single_doc()
        
        out = orchestrator_agent.handle(AgentInput(user_input="Search for papers by José García on español"))
        
        self.assertIsNotNone(out.text)
        mock_explore.assert_called_once()

    @patch("core.csusb_library_client.explore_search")
    def test_handle_multiple_date_patterns(self, mock_explore):
        """Test various date pattern extractions."""
        captured = []
        
        def side_effect(*, q=None, **kwargs):
            captured.append(q)
            return self._single_doc()
        
        mock_explore.side_effect = side_effect
        
        test_cases = [
            ("Show articles on AI since 2020", "dr_s,exact,20200101"),
            ("Find papers on ML from 2015 to 2020", "dr_s,exact,20150101"),
            ("List books on physics between 2018 and 2022", "dr_s,exact,20180101"),
            ("Get articles on chemistry after 2019", "dr_s,exact,20200101"),  # after means next year
            ("Show papers on biology before 2021", "dr_e,exact,20201231"),  # before means previous year
        ]
        
        for user_input, expected_in_q in test_cases:
            with self.subTest(input=user_input):
                captured.clear()
                orchestrator_agent.handle(AgentInput(user_input=user_input))
                self.assertTrue(any(expected_in_q in q for q in captured if q), 
                              f"Expected '{expected_in_q}' in query for input '{user_input}'")

    @patch("core.csusb_library_client.explore_search")
    def test_handle_multiple_author_patterns(self, mock_explore):
        """Test various author pattern extractions."""
        captured = []
        
        def side_effect(*, q=None, **kwargs):
            captured.append(q)
            return self._single_doc()
        
        mock_explore.side_effect = side_effect
        
        test_cases = [
            ("Papers by Alan Turing", "creator,contains,Alan Turing"),
            ("author: Jane Doe on AI", "creator,contains,Jane Doe"),
            ("authors: Smith, Jones on quantum", "creator,contains,Smith"),
            ("Find works by Andrew Ng and Yann LeCun", "creator,contains,Andrew Ng"),
        ]
        
        for user_input, expected_in_q in test_cases:
            with self.subTest(input=user_input):
                captured.clear()
                orchestrator_agent.handle(AgentInput(user_input=user_input))
                self.assertTrue(any(expected_in_q in q for q in captured if q),
                              f"Expected '{expected_in_q}' in query for input '{user_input}'")

    @patch("core.csusb_library_client.explore_search")
    def test_handle_all_resource_types(self, mock_explore):
        """Test that all supported resource types are correctly parsed."""
        mock_explore.return_value = self._single_doc()
        
        type_mappings = [
            ("articles", "rtype,exact,articles"),
            ("books", "rtype,exact,books"),
            ("book chapters", "rtype,exact,book_chapters"),
            ("dissertations", "rtype,exact,dissertations"),
            ("conference proceedings", "rtype,exact,conference_proceedings"),
            ("videos", "rtype,exact,videos"),
            ("journals", "rtype,exact,journals"),
            ("datasets", "rtype,exact,datasets"),
            ("patents", "rtype,exact,patents"),
            ("reports", "rtype,exact,reports"),
            ("software", "rtype,exact,software"),
            ("websites", "rtype,exact,websites"),
        ]
        
        for type_term, expected_q in type_mappings:
            with self.subTest(type=type_term):
                mock_explore.reset_mock()
                out = orchestrator_agent.handle(
                    AgentInput(user_input=f"Show {type_term} about AI")
                )
                call_args = mock_explore.call_args
                if call_args:
                    q_param = call_args.kwargs.get("q", "")
                    self.assertIn(expected_q, q_param,
                                f"Expected '{expected_q}' for type '{type_term}'")

    @patch("core.csusb_library_client.explore_search")
    def test_handle_peer_reviewed_variations(self, mock_explore):
        """Test various peer-reviewed keyword patterns."""
        captured = []
        
        def side_effect(*, q=None, **kwargs):
            captured.append(q)
            return self._single_doc()
        
        mock_explore.side_effect = side_effect
        
        peer_reviewed_phrases = [
            "peer-reviewed articles",
            "peer reviewed papers",
            "peerreviewed research",
        ]
        
        for phrase in peer_reviewed_phrases:
            with self.subTest(phrase=phrase):
                captured.clear()
                out = orchestrator_agent.handle(
                    AgentInput(user_input=f"Show {phrase} on AI")
                )
                self.assertTrue(any("facet_tlevel,exact,peer_reviewed" in q for q in captured if q))

    @patch("core.csusb_library_client.explore_search")
    def test_handle_limit_variations(self, mock_explore):
        """Test various limit/top N patterns."""
        mock_explore.return_value = self._single_doc()
        
        test_cases = [
            ("Show top 5 articles", 5),
            ("List top 1 paper", 1),
            ("Find top 25 books", 25),
            ("Get top 100 results", 50),  # Should clamp to 50
        ]
        
        for user_input, expected_limit in test_cases:
            with self.subTest(input=user_input):
                mock_explore.reset_mock()
                orchestrator_agent.handle(AgentInput(user_input=user_input))
                call_args = mock_explore.call_args
                if call_args:
                    actual_limit = call_args.kwargs.get("limit")
                    self.assertEqual(actual_limit, expected_limit,
                                   f"Expected limit {expected_limit} for '{user_input}'")

    @patch("core.csusb_library_client.explore_search")
    def test_handle_combined_complex_query(self, mock_explore):
        """Test complex query with multiple filters combined."""
        captured = {}
        
        def side_effect(*, q=None, limit=10, sort="rank", **kwargs):
            captured["q"] = q
            captured["limit"] = limit
            captured["sort"] = sort
            return self._single_doc()
        
        mock_explore.side_effect = side_effect
        
        complex_query = (
            "Show top 15 peer-reviewed journal articles by Andrew Ng and Geoffrey Hinton "
            "about deep learning between 2015 and 2023"
        )
        
        out = orchestrator_agent.handle(AgentInput(user_input=complex_query))
        
        q = captured.get("q", "")
        # Verify all components are present
        self.assertIn("deep learning", q)
        self.assertIn("creator,contains,Andrew Ng", q)
        self.assertIn("creator,contains,Geoffrey Hinton", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)  # "journal articles" -> articles
        self.assertIn("dr_s,exact,20150101", q)
        self.assertIn("dr_e,exact,20231231", q)
        self.assertEqual(captured.get("limit"), 15)

    @patch("core.csusb_library_client.explore_search")
    def test_handle_no_terms_after_parsing(self, mock_explore):
        """Test when query has no actual search terms after parsing."""
        # These should return error messages without calling explore_search
        empty_queries = [
            "Show top 10",
            "List articles",
            "Find papers",
            "   ",  # Just whitespace
        ]
        
        for query in empty_queries:
            with self.subTest(query=query):
                out = orchestrator_agent.handle(AgentInput(user_input=query))
                self.assertIn("Please provide search terms", out.text)
                # Should not call explore_search
                self.assertFalse(mock_explore.called)
                mock_explore.reset_mock()

    @patch("core.csusb_library_client.explore_search")
    def test_handle_malformed_primo_response(self, mock_explore):
        """Test handling of malformed Primo API responses."""
        # Missing 'docs' key
        mock_explore.return_value = {}
        
        out = orchestrator_agent.handle(AgentInput(user_input="Show articles on test"))
        
        # Should handle gracefully
        self.assertIsNotNone(out.text)

    @patch("core.csusb_library_client.explore_search")
    def test_handle_exception_in_search(self, mock_explore):
        """Test error handling when search raises an exception."""
        mock_explore.side_effect = Exception("Network error")
        
        out = orchestrator_agent.handle(AgentInput(user_input="Show articles on test"))
        
        # Should catch exception and return error message
        self.assertIn("Error", out.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
