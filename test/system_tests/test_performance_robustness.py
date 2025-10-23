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


class TestSystemPerformance(unittest.TestCase):
    """System tests for performance characteristics and resource handling."""

    def _create_docs(self, count):
        """Create multiple test documents."""
        return {
            "docs": [
                {
                    "id": f"PERF{i}",
                    "pnx": {
                        "display": {"title": [f"Document {i}"], "creator": ["A"], "type": ["article"]},
                        "sort": {"creationdate": ["2023"]},
                        "control": {"recordid": [f"PERF{i}"]},
                    },
                    "context": "PC",
                }
                for i in range(count)
            ]
        }

    @patch("core.csusb_library_client.explore_search")
    def test_max_result_limit_enforcement(self, mock_explore):
        """Test that system enforces maximum result limits."""
        mock_explore.return_value = self._create_docs(100)
        
        # Request more than max
        output = orchestrator_agent.handle(AgentInput(user_input="Show top 200 articles on AI"))
        
        # Should be clamped to max (50)
        call_kwargs = mock_explore.call_args.kwargs
        self.assertLessEqual(call_kwargs.get("limit"), 50)

    @patch("core.csusb_library_client.explore_search")
    def test_min_result_limit_enforcement(self, mock_explore):
        """Test that system enforces minimum result limits."""
        mock_explore.return_value = self._create_docs(1)
        
        # Request less than min
        output = orchestrator_agent.handle(AgentInput(user_input="Show top 0 articles"))
        
        # Should either reject or clamp to 1
        if mock_explore.called:
            call_kwargs = mock_explore.call_args.kwargs
            self.assertGreaterEqual(call_kwargs.get("limit"), 1)

    @patch("core.csusb_library_client.explore_search")
    def test_handling_large_result_sets(self, mock_explore):
        """Test system behavior with large result sets."""
        # Return max results
        mock_explore.return_value = self._create_docs(50)
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show 50 articles on AI"))
        
        # Should handle requested results (up to the limit)
        self.assertGreater(len(output.briefs), 0)
        self.assertLessEqual(len(output.briefs), 50)
        
        # Output should still be well-formed
        self.assertIn("|", output.text)
        self.assertGreater(len(output.text), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_handling_single_result(self, mock_explore):
        """Test system behavior with single result."""
        mock_explore.return_value = self._create_docs(1)
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show 1 article"))
        
        self.assertEqual(len(output.briefs), 1)
        self.assertIn("Top 1 results", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_query_complexity_handling(self, mock_explore):
        """Test system handles complex queries without degradation."""
        mock_explore.return_value = self._create_docs(5)
        
        # Very complex query
        complex_query = (
            "Show me the top 10 peer-reviewed journal articles and book chapters "
            "by Einstein, Bohr, and Heisenberg about quantum mechanics and relativity theory "
            "published between 1920 and 1930 in English"
        )
        
        output = orchestrator_agent.handle(AgentInput(user_input=complex_query))
        
        # Should complete successfully
        self.assertIsNotNone(output)
        self.assertIsNotNone(output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_repeated_queries(self, mock_explore):
        """Test system handles repeated queries correctly."""
        mock_explore.return_value = self._create_docs(3)
        
        # Same query multiple times
        for _ in range(5):
            output = orchestrator_agent.handle(AgentInput(user_input="Show articles on AI"))
            self.assertIsNotNone(output)
            self.assertEqual(len(output.briefs), 3)

    @patch("core.csusb_library_client.explore_search")
    def test_varying_query_patterns(self, mock_explore):
        """Test system handles varying query patterns in sequence."""
        mock_explore.return_value = self._create_docs(2)
        
        queries = [
            "Show articles",
            "Find books by Smith",
            "List dissertations since 2020",
            "Get peer-reviewed papers",
            "Search for conference proceedings",
        ]
        
        for query in queries:
            output = orchestrator_agent.handle(AgentInput(user_input=query))
            self.assertIsNotNone(output)

    @patch("core.csusb_library_client.explore_search")
    def test_memory_efficiency_with_large_text(self, mock_explore):
        """Test system handles documents with large text fields."""
        large_doc = {
            "id": "LARGE1",
            "pnx": {
                "display": {
                    "title": ["A" * 1000],  # Very long title
                    "creator": ["Author " + str(i) for i in range(50)],  # Many authors
                    "type": ["article"],
                },
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["LARGE1"]},
            },
            "context": "PC",
        }
        mock_explore.return_value = {"docs": [large_doc]}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on testing"))
        
        # Should handle without error
        self.assertIsNotNone(output)
        self.assertEqual(len(output.briefs), 1)

    @patch("core.csusb_library_client.explore_search")
    def test_concurrent_filter_processing(self, mock_explore):
        """Test system processes multiple filters efficiently."""
        mock_explore.return_value = self._create_docs(5)
        
        # Query with many filters
        output = orchestrator_agent.handle(
            AgentInput(
                user_input=(
                    "Show peer-reviewed articles by multiple authors "
                    "from 2015 to 2023 about AI and ML"
                )
            )
        )
        
        # Should complete in reasonable time
        self.assertIsNotNone(output)
        
        # All filters should be applied
        call_kwargs = mock_explore.call_args.kwargs
        q = call_kwargs.get("q", "")
        self.assertGreater(len(q), 50)  # Complex query string


class TestSystemRobustness(unittest.TestCase):
    """System tests for robustness and error handling."""

    @patch("core.csusb_library_client.explore_search")
    def test_malformed_api_response_handling(self, mock_explore):
        """Test system handles malformed API responses."""
        malformed_responses = [
            {},  # Missing docs
            {"docs": None},  # Null docs
            {"docs": "invalid"},  # Wrong type
            {"docs": [{}]},  # Empty doc
            {"docs": [{"pnx": None}]},  # Null pnx
        ]
        
        for response in malformed_responses:
            with self.subTest(response=response):
                mock_explore.return_value = response
                
                output = orchestrator_agent.handle(AgentInput(user_input="Show articles"))
                
                # Should not crash
                self.assertIsNotNone(output)
                self.assertIsNotNone(output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_network_error_recovery(self, mock_explore):
        """Test system recovers from network errors."""
        mock_explore.side_effect = ConnectionError("Network unreachable")
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on networking"))
        
        # Should return error message
        self.assertIsNotNone(output)
        self.assertIn("Error", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_timeout_handling(self, mock_explore):
        """Test system handles timeout errors."""
        mock_explore.side_effect = TimeoutError("Request timeout")
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on performance"))
        
        # Should handle gracefully
        self.assertIsNotNone(output)
        self.assertIn("Error", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_invalid_user_input_handling(self, mock_explore):
        """Test system handles various invalid inputs."""
        invalid_inputs = [
            "",  # Empty
            "   ",  # Whitespace only
            "show",  # No search terms
            "top 5",  # No search terms
            "articles",  # No search terms
        ]
        
        for user_input in invalid_inputs:
            with self.subTest(input=user_input):
                output = orchestrator_agent.handle(AgentInput(user_input=user_input))
                
                # Should return appropriate message
                self.assertIsNotNone(output)
                self.assertIn("Please provide search terms", output.text)
                # Should not call API for invalid input
                self.assertFalse(mock_explore.called)
                mock_explore.reset_mock()

    @patch("core.csusb_library_client.explore_search")
    def test_special_character_escaping(self, mock_explore):
        """Test system properly handles special characters."""
        mock_explore.return_value = {"docs": []}
        
        special_queries = [
            "C++ programming",
            "A&B testing",
            "O'Reilly books",
            'Papers with "quotes"',
            "Research on <HTML> tags",
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=f"Show articles on {query}"))
                
                # Should handle without error
                self.assertIsNotNone(output)

    @patch("core.csusb_library_client.explore_search")
    def test_unicode_text_handling(self, mock_explore):
        """Test system handles unicode text correctly."""
        mock_explore.return_value = {"docs": []}
        
        unicode_queries = [
            "研究 on Chinese characters",
            "Études en français",
            "Исследование in Russian",
            "العربية research",
            "日本語 studies",
        ]
        
        for query in unicode_queries:
            with self.subTest(query=query):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=query))
                
                # Should process without error
                self.assertIsNotNone(output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
