import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import orchestrator_agent
from core.schemas import AgentInput


class TestDataFlowThroughSystem(unittest.TestCase):
    """System tests verifying data flow through all system layers."""

    def _create_test_doc(self, doc_id="DOC1", title="Test Title", year="2023"):
        """Create a minimal test document."""
        return {
            "id": doc_id,
            "pnx": {
                "display": {
                    "title": [title],
                    "creator": ["Test Author"],
                    "type": ["article"],
                },
                "sort": {"creationdate": [year]},
                "search": {"rtype": ["journal"]},
                "control": {"recordid": [doc_id]},
            },
            "link": {"record": f"https://example.org/{doc_id.lower()}"},
            "context": "PC",
        }

    @patch("core.csusb_library_client.explore_search")
    def test_user_input_to_api_call_flow(self, mock_explore):
        """Test data flow from user input to API call construction."""
        mock_explore.return_value = {"docs": [self._create_test_doc()]}
        
        user_input = "Show top 5 peer-reviewed articles by Einstein about relativity since 2020"
        
        # Trace the flow through the system
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # Verify API was called
        self.assertTrue(mock_explore.called)
        
        # Extract and verify the query construction
        call_kwargs = mock_explore.call_args.kwargs
        q = call_kwargs.get("q", "")
        limit = call_kwargs.get("limit")
        
        # Verify user input was properly parsed and transformed
        self.assertIn("relativity", q.lower())
        self.assertIn("creator,contains,Einstein", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)
        self.assertIn("dr_s,exact,20200101", q)
        self.assertEqual(limit, 5)

    @patch("core.csusb_library_client.explore_search")
    def test_api_response_to_user_output_flow(self, mock_explore):
        """Test data flow from API response to formatted user output."""
        # Create API response
        test_doc = self._create_test_doc(
            doc_id="FLOW123",
            title="Data Flow in Distributed Systems",
            year="20220815"
        )
        mock_explore.return_value = {"docs": [test_doc]}
        
        # Process through system
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on data flow"))
        
        # Verify data transformation at each layer
        # 1. API response -> SearchBrief objects
        self.assertEqual(len(output.briefs), 1)
        brief = output.briefs[0]
        self.assertEqual(brief.record_id, "FLOW123")
        self.assertEqual(brief.title, "Data Flow in Distributed Systems")
        self.assertEqual(brief.creation_date, "2022")  # Year normalized
        self.assertEqual(brief.resource_type, "journal")  # From search.rtype
        
        # 2. SearchBrief objects -> Formatted text output
        self.assertIn("Data Flow in Distributed Systems", output.text)
        self.assertIn("2022", output.text)
        self.assertIn("journal", output.text.lower())
        self.assertIn("https://example.org/flow123", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_query_parameters_propagation(self, mock_explore):
        """Test that query parameters propagate correctly through all layers."""
        mock_explore.return_value = {"docs": [self._create_test_doc()]}
        
        # Test with multiple parameters
        test_params = {
            "query_terms": "neural networks",
            "author": "Andrew Ng",
            "type": "books",
            "year_from": 2018,
            "year_to": 2023,
            "peer_reviewed": True,
            "limit": 7,
        }
        
        user_input = (
            f"Show top {test_params['limit']} peer-reviewed {test_params['type']} "
            f"by {test_params['author']} about {test_params['query_terms']} "
            f"between {test_params['year_from']} and {test_params['year_to']}"
        )
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # Verify all parameters made it through
        call_kwargs = mock_explore.call_args.kwargs
        q = call_kwargs.get("q", "")
        
        self.assertIn(test_params['query_terms'], q.lower())
        self.assertIn(f"creator,contains,{test_params['author']}", q)
        self.assertIn(f"rtype,exact,{test_params['type']}", q)
        self.assertIn(f"dr_s,exact,{test_params['year_from']}0101", q)
        self.assertIn(f"dr_e,exact,{test_params['year_to']}1231", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertEqual(call_kwargs.get("limit"), test_params['limit'])

    @patch("core.csusb_library_client.explore_search")
    def test_multiple_documents_flow(self, mock_explore):
        """Test data flow with multiple documents."""
        docs = [
            self._create_test_doc(f"DOC{i}", f"Title {i}", f"202{i}")
            for i in range(5)
        ]
        mock_explore.return_value = {"docs": docs}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show 5 articles"))
        
        # Verify all documents flowed through
        self.assertEqual(len(output.briefs), 5)
        
        # Verify each document in output
        for i in range(5):
            self.assertIn(f"Title {i}", output.text)
            self.assertIn(f"202{i}", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_error_propagation_flow(self, mock_explore):
        """Test that errors propagate correctly through the system."""
        # Simulate API error
        mock_explore.side_effect = Exception("API connection failed")
        
        # Error should be caught and returned to user
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on AI"))
        
        # Should get error message, not crash
        self.assertIsNotNone(output.text)
        self.assertIn("Error", output.text)
        self.assertEqual(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_empty_result_flow(self, mock_explore):
        """Test data flow when no results are found."""
        mock_explore.return_value = {"docs": []}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show xyz articles"))
        
        # Should complete flow with appropriate message
        self.assertIsNotNone(output.text)
        self.assertIn("No results found", output.text)
        self.assertEqual(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_default_values_flow(self, mock_explore):
        """Test that default values are correctly applied throughout the flow."""
        mock_explore.return_value = {"docs": [self._create_test_doc()]}
        
        # Minimal query - should use defaults
        output = orchestrator_agent.handle(AgentInput(user_input="Show articles on AI"))
        
        call_kwargs = mock_explore.call_args.kwargs
        q = call_kwargs.get("q", "")
        
        # Default language should be applied
        self.assertIn("lang,exact,eng", q)
        
        # Default limit (10) should be used
        limit = call_kwargs.get("limit")
        self.assertEqual(limit, 10)
        
        # Default sort should be rank
        sort = call_kwargs.get("sort")
        self.assertEqual(sort, "rank")

    @patch("core.csusb_library_client.explore_search")
    def test_metadata_preservation_flow(self, mock_explore):
        """Test that document metadata is preserved through the flow."""
        test_doc = {
            "id": "META123",
            "pnx": {
                "display": {
                    "title": ["Metadata Preservation Test"],
                    "creator": ["Smith, J.", "Doe, J."],
                    "type": ["book"],
                    "publisher": ["Academic Press"],
                },
                "sort": {
                    "creationdate": ["20230515"],
                    "author": ["Smith, John", "Doe, Jane"],
                },
                "search": {
                    "rtype": ["book"],
                    "creatorcontrib": ["Smith, John", "Doe, Jane"],
                },
                "control": {"recordid": ["META123"]},
            },
            "link": {"record": "https://example.org/meta123"},
            "context": "L",
        }
        mock_explore.return_value = {"docs": [test_doc]}
        
        output = orchestrator_agent.handle(AgentInput(user_input="Show books"))
        
        # Verify all metadata preserved
        brief = output.briefs[0]
        self.assertEqual(brief.record_id, "META123")
        self.assertEqual(brief.title, "Metadata Preservation Test")
        self.assertEqual(len(brief.creators), 2)
        self.assertIn("Smith, John", brief.creators)
        self.assertIn("Doe, Jane", brief.creators)
        self.assertEqual(brief.creation_date, "2023")
        self.assertEqual(brief.resource_type, "book")
        self.assertEqual(brief.context, "L")
        self.assertIn("meta123", brief.permalink)

    @patch("core.csusb_library_client.explore_search")
    def test_filter_combination_flow(self, mock_explore):
        """Test that multiple filters combine correctly through the flow."""
        mock_explore.return_value = {"docs": [self._create_test_doc()]}
        
        # Complex query with all filter types
        user_input = (
            "Show top 3 peer-reviewed journal articles "
            "by Jane Doe and John Smith "
            "about quantum computing "
            "from 2019 to 2023"
        )
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_input))
        
        # All filters should be combined in the query
        call_kwargs = mock_explore.call_args.kwargs
        q = call_kwargs.get("q", "")
        
        # Verify all filters present and properly combined with AND
        self.assertIn(",AND;", q)
        self.assertIn("quantum computing", q.lower())
        self.assertIn("creator,contains,Jane Doe", q)
        self.assertIn("creator,contains,John Smith", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)
        self.assertIn("dr_s,exact,20190101", q)
        self.assertIn("dr_e,exact,20231231", q)


if __name__ == "__main__":
    unittest.main(verbosity=2)
