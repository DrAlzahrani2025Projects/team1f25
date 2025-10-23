import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import orchestrator_agent
from core.schemas import AgentInput, AgentOutput


class TestEndToEndSearchWorkflow(unittest.TestCase):
    """System tests for complete end-to-end search workflows."""

    def _create_realistic_primo_response(self, query_terms="AI", count=5):
        """Create a realistic Primo API response with multiple documents."""
        docs = []
        topics = ["machine learning", "deep learning", "neural networks", "computer vision", "NLP"]
        authors = [
            ["Ng, Andrew", "Bengio, Yoshua"],
            ["LeCun, Yann", "Hinton, Geoffrey"],
            ["Schmidhuber, Jürgen"],
            ["Goodfellow, Ian", "Bengio, Yoshua", "Courville, Aaron"],
            ["Sutskever, Ilya", "Vinyals, Oriol"]
        ]
        years = ["2023", "2022", "2021", "2020", "2019"]
        types = ["article", "journal", "book", "conference_proceeding", "dissertation"]
        
        for i in range(min(count, 5)):
            doc = {
                "id": f"01CALS_USB_alma99{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}",
                "pnx": {
                    "display": {
                        "title": [f"{topics[i].title()} Research: Applications and Theory"],
                        "creator": authors[i],
                        "type": [types[i]],
                        "publisher": ["Academic Press"],
                        "subject": [query_terms, topics[i], "artificial intelligence"],
                    },
                    "sort": {
                        "creationdate": [f"{years[i]}0315"],
                        "author": authors[i],
                    },
                    "search": {
                        "rtype": [types[i]],
                        "creatorcontrib": authors[i],
                    },
                    "control": {
                        "recordid": [f"01CALS_USB_alma99{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}"],
                    },
                },
                "link": {
                    "record": f"https://csu-sb.primo.exlibrisgroup.com/permalink/01CALS_USB/example{i+1}"
                },
                "context": "PC",
            }
            docs.append(doc)
        
        return {"docs": docs, "info": {"total": count}}

    @patch("core.csusb_library_client.explore_search")
    def test_simple_search_workflow(self, mock_explore):
        """Test a simple search request from user input to formatted output."""
        mock_explore.return_value = self._create_realistic_primo_response("machine learning", 3)
        
        # User makes a simple search request
        user_input = "Show me top 3 articles on machine learning"
        
        # Process through the system
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # Verify output structure
        self.assertIsInstance(output, AgentOutput)
        self.assertIsNotNone(output.text)
        self.assertGreater(len(output.text), 0)
        
        # Verify results were returned
        self.assertEqual(len(output.briefs), 3)
        
        # Verify formatted output contains key elements
        self.assertIn("Top 3 results", output.text)
        self.assertIn("machine learning", output.text.lower())
        self.assertIn("|", output.text)  # Markdown table
        
        # Verify each brief has required fields
        for brief in output.briefs:
            self.assertIsNotNone(brief.record_id)
            self.assertIsNotNone(brief.title)
            self.assertIsNotNone(brief.permalink)

    @patch("core.csusb_library_client.explore_search")
    def test_complex_filtered_search_workflow(self, mock_explore):
        """Test a complex search with multiple filters."""
        mock_explore.return_value = self._create_realistic_primo_response("quantum computing", 5)
        
        # User makes a complex request with multiple filters
        user_input = (
            "Find top 5 peer-reviewed journal articles by Andrew Ng "
            "about deep learning between 2018 and 2023"
        )
        
        # Process through the system
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # Verify the request was processed
        self.assertIsInstance(output, AgentOutput)
        self.assertGreater(len(output.briefs), 0)
        
        # Verify the API was called with correct filters
        mock_explore.assert_called_once()
        call_args = mock_explore.call_args.kwargs
        q_param = call_args.get("q", "")
        
        # Verify all filters were applied
        self.assertIn("deep learning", q_param.lower())
        self.assertIn("creator,contains,Andrew Ng", q_param)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q_param)
        self.assertIn("rtype,exact,articles", q_param)
        self.assertIn("dr_s,exact,20180101", q_param)
        self.assertIn("dr_e,exact,20231231", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_search_with_no_results_workflow(self, mock_explore):
        """Test workflow when search returns no results."""
        mock_explore.return_value = {"docs": []}
        
        user_input = "Show articles about xyz123nonexistent456topic"
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # Should return appropriate message
        self.assertIn("No results found", output.text)
        self.assertEqual(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_author_search_workflow(self, mock_explore):
        """Test search workflow specifically for author queries."""
        mock_explore.return_value = self._create_realistic_primo_response("AI", 4)
        
        test_cases = [
            "Papers by Alan Turing on computing",
            "author: Jane Doe research",
            "authors: Smith, Jones, and Lee collaboration",
        ]
        
        for user_input in test_cases:
            with self.subTest(query=user_input):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=user_input))
                
                # Should successfully process
                self.assertIsInstance(output, AgentOutput)
                
                # Should have called API with creator filter
                if mock_explore.called:
                    call_args = mock_explore.call_args.kwargs
                    q_param = call_args.get("q", "")
                    self.assertIn("creator,contains,", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_resource_type_search_workflow(self, mock_explore):
        """Test search workflow for different resource types."""
        mock_explore.return_value = self._create_realistic_primo_response("test", 2)
        
        type_queries = [
            ("Show me books about history", "books"),
            ("Find dissertations on physics", "dissertations"),
            ("List conference proceedings on AI", "conference_proceedings"),
            ("Get datasets for analysis", "datasets"),
            ("Show software tools", "software"),
        ]
        
        for user_input, expected_type in type_queries:
            with self.subTest(query=user_input, type=expected_type):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=user_input))
                
                # Should successfully process
                self.assertIsInstance(output, AgentOutput)
                
                # Verify type filter was applied
                if mock_explore.called:
                    call_args = mock_explore.call_args.kwargs
                    q_param = call_args.get("q", "")
                    self.assertIn(f"rtype,exact,{expected_type}", q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_date_range_search_workflow(self, mock_explore):
        """Test search workflow with various date range queries."""
        mock_explore.return_value = self._create_realistic_primo_response("climate", 3)
        
        date_queries = [
            ("Articles on climate since 2020", "20200101"),
            ("Papers from 2015 to 2020 about energy", "20150101"),
            ("Research after 2018 on sustainability", "20190101"),
        ]
        
        for user_input, expected_date in date_queries:
            with self.subTest(query=user_input):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=user_input))
                
                self.assertIsInstance(output, AgentOutput)
                
                if mock_explore.called:
                    call_args = mock_explore.call_args.kwargs
                    q_param = call_args.get("q", "")
                    self.assertIn(expected_date, q_param)

    @patch("core.csusb_library_client.explore_search")
    def test_markdown_table_output_format(self, mock_explore):
        """Test that output is properly formatted as a Markdown table."""
        mock_explore.return_value = self._create_realistic_primo_response("test", 3)
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show 3 articles on AI"))
        
        # Check for Markdown table structure
        self.assertIn("|", output.text)
        self.assertIn("Type", output.text)
        self.assertIn("Title", output.text)
        self.assertIn("Authors", output.text)
        self.assertIn("Year", output.text)
        self.assertIn("Link", output.text)
        
        # Check for table rows
        lines = output.text.split("\n")
        table_lines = [l for l in lines if l.startswith("|")]
        self.assertGreaterEqual(len(table_lines), 4)  # Header + separator + data rows

    @patch("core.csusb_library_client.explore_search")
    def test_limit_clamping_workflow(self, mock_explore):
        """Test that result limits are properly clamped."""
        mock_explore.return_value = self._create_realistic_primo_response("test", 1)
        
        # Test upper limit clamping
        output = orchestrator_agent.handle(AgentInput(user_input="Show top 100 articles on AI"))
        
        call_args = mock_explore.call_args.kwargs
        limit = call_args.get("limit")
        self.assertLessEqual(limit, 50)  # Max limit is 50
        
        # Test lower limit clamping
        mock_explore.reset_mock()
        output = orchestrator_agent.handle(AgentInput(user_input="List top 0 papers"))
        
        # Should either return error or clamp to 1
        if mock_explore.called:
            call_args = mock_explore.call_args.kwargs
            limit = call_args.get("limit")
            self.assertGreaterEqual(limit, 1)

    @patch("core.csusb_library_client.explore_search")
    def test_error_recovery_workflow(self, mock_explore):
        """Test that system gracefully handles errors."""
        # Simulate network error
        mock_explore.side_effect = Exception("Network timeout")
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on test"))
        
        # Should not crash, should return error message
        self.assertIsInstance(output, AgentOutput)
        self.assertIn("Error", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_year_normalization_in_output(self, mock_explore):
        """Test that years are properly normalized in output."""
        docs = [{
            "id": "TEST1",
            "pnx": {
                "display": {"title": ["Test"], "creator": ["Author"], "type": ["article"]},
                "sort": {"creationdate": ["20231015"]},  # Full date
                "control": {"recordid": ["TEST1"]},
            },
            "context": "PC"
        }]
        mock_explore.return_value = {"docs": docs}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show test articles"))
        
        # Year should be normalized to YYYY only
        self.assertIn("2023", output.text)
        self.assertNotIn("20231015", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_multiple_authors_display(self, mock_explore):
        """Test that multiple authors are properly displayed."""
        docs = [{
            "id": "MA1",
            "pnx": {
                "display": {"title": ["Collaboration"], "type": ["article"]},
                "sort": {
                    "creationdate": ["2023"],
                    "author": ["Smith, John", "Doe, Jane", "Lee, Bob"]
                },
                "control": {"recordid": ["MA1"]},
            },
            "context": "PC"
        }]
        mock_explore.return_value = {"docs": docs}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on collaboration"))
        
        # All authors should appear in output
        self.assertIn("Smith, John", output.text)
        self.assertIn("Doe, Jane", output.text)
        self.assertIn("Lee, Bob", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_clickable_links_in_output(self, mock_explore):
        """Test that output contains properly formatted clickable links."""
        mock_explore.return_value = self._create_realistic_primo_response("test", 2)
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show 2 articles"))
        
        # Check for Markdown link format
        self.assertRegex(output.text, r'\[https?://[^\]]+\]\(https?://[^\)]+\)')

    @patch("core.csusb_library_client.explore_search")
    def test_concurrent_different_queries(self, mock_explore):
        """Test handling multiple different queries in sequence."""
        queries = [
            "Show articles on AI",
            "Find books by Turing",
            "List dissertations since 2020",
            "Get peer-reviewed papers on quantum",
        ]
        
        for query in queries:
            with self.subTest(query=query):
                mock_explore.reset_mock()
                mock_explore.return_value = self._create_realistic_primo_response("test", 2)
                
                output = orchestrator_agent.handle(AgentInput(user_input=query))
                
                self.assertIsInstance(output, AgentOutput)
                self.assertIsNotNone(output.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
