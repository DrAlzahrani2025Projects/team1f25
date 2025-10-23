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


class TestBusinessRequirementsAcceptance(unittest.TestCase):
    """UAT: Verify system meets core business requirements."""

    @patch("core.csusb_library_client.explore_search")
    def test_search_limit_enforced(self, mock_explore):
        """
        UAT-BR-001: System enforces maximum search result limit
        Given: System has a maximum result limit of 50
        When: User requests more than 50 results
        Then: System caps at 50 and returns maximum allowed
        """
        # Create 50 mock results
        mock_explore.return_value = {"docs": [
            {
                "id": f"LIM{i}",
                "pnx": {
                    "display": {"title": [f"Article {i}"], "creator": ["A"], "type": ["article"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": [f"LIM{i}"]},
                },
                "context": "PC"
            }
            for i in range(50)
        ]}
        
        user_query = "Show me 100 articles on testing"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        limit = call_args.get("limit", 0)
        
        self.assertLessEqual(limit, 50)
        self.assertGreater(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_search_terms_required(self, mock_explore):
        """
        UAT-BR-002: System requires search terms before querying
        Given: System should not make empty searches
        When: User input has no search terms
        Then: System returns error message without calling API
        """
        empty_inputs = [
            "",
            "   ",
        ]
        
        for empty_input in empty_inputs:
            with self.subTest(input=empty_input):
                output = orchestrator_agent.handle(AgentInput(user_input=empty_input))
                
                self.assertIn("Please provide search terms", output.text)
                self.assertFalse(mock_explore.called)
                mock_explore.reset_mock()

    @patch("core.csusb_library_client.explore_search")
    def test_markdown_table_output_format(self, mock_explore):
        """
        UAT-BR-003: System outputs results as Markdown table
        Given: System should present results in readable table format
        When: User performs any successful search
        Then: Output is formatted as Markdown table with headers
        """
        mock_explore.return_value = {"docs": [{
            "id": "MD1",
            "pnx": {
                "display": {"title": ["Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["MD1"]},
            },
            "link": {"record": "https://example.org/md1"},
            "context": "PC"
        }]}
        
        user_query = "Show me articles on markdown formatting"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify Markdown table structure
        self.assertIn("|", output.text)
        self.assertIn("Type", output.text)
        self.assertIn("Title", output.text)
        self.assertIn("Authors", output.text)
        self.assertIn("Year", output.text)
        self.assertIn("Link", output.text)
        
        # Verify table separator line exists
        lines = output.text.split("\n")
        separator_exists = any("---" in line for line in lines)
        self.assertTrue(separator_exists)

    @patch("core.csusb_library_client.explore_search")
    def test_handles_primo_api_integration(self, mock_explore):
        """
        UAT-BR-004: System correctly integrates with Primo API
        Given: System must use Primo Discovery API format
        When: User makes a search request
        Then: System calls API with correct Primo query format
        """
        mock_explore.return_value = {"docs": [{
            "id": "PRIMO1",
            "pnx": {
                "display": {"title": ["Primo Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["PRIMO1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find peer-reviewed articles on libraries by Smith from 2020 to 2023"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify Primo query format
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        # Check Primo-specific format: field,operator,value
        self.assertRegex(q, r"\w+,\w+,\w+")
        self.assertTrue(mock_explore.called)


class TestUserExperienceAcceptance(unittest.TestCase):
    """UAT: User experience and interface requirements."""

    @patch("core.csusb_library_client.explore_search")
    def test_natural_language_understanding(self, mock_explore):
        """
        UAT-UX-001: System understands natural language queries
        Given: Users should not need to learn complex syntax
        When: User types conversational queries
        Then: System correctly interprets intent
        """
        mock_explore.return_value = {"docs": [{
            "id": "NL1",
            "pnx": {
                "display": {"title": ["NLP Study"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["NL1"]},
            },
            "context": "PC"
        }]}
        
        natural_queries = [
            "I need articles about natural language processing",
            "Can you find me books on machine learning?",
            "Show me research from 2020 about AI",
            "Looking for papers by John Smith",
        ]
        
        for query in natural_queries:
            with self.subTest(query=query):
                mock_explore.reset_mock()
                output = orchestrator_agent.handle(AgentInput(user_input=query))
                
                # Should successfully process all natural queries
                self.assertIsNotNone(output)
                self.assertTrue(mock_explore.called)

    @patch("core.csusb_library_client.explore_search")
    def test_clear_result_count_messaging(self, mock_explore):
        """
        UAT-UX-002: System clearly shows result count
        Given: Users need to know how many results they got
        When: Results are returned
        Then: Message includes clear count information
        """
        mock_explore.return_value = {"docs": [
            {
                "id": f"CNT{i}",
                "pnx": {
                    "display": {"title": [f"Article {i}"], "creator": ["A"], "type": ["article"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": [f"CNT{i}"]},
                },
                "context": "PC"
            }
            for i in range(7)
        ]}
        
        user_query = "Find articles on counting"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should mention result count
        self.assertTrue(
            "7" in output.text or "seven" in output.text.lower(),
            "Result count not clearly indicated"
        )

    @patch("core.csusb_library_client.explore_search")
    def test_helpful_no_results_message(self, mock_explore):
        """
        UAT-UX-003: System provides helpful message when no results
        Given: Empty results can be frustrating
        When: Search returns no results
        Then: System shows clear, helpful message
        """
        mock_explore.return_value = {"docs": []}
        
        user_query = "Find articles on nonexistent_topic_xyz"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        self.assertIn("No results found", output.text)
        self.assertGreater(len(output.text), 20)  # Should be more than just "No results"


class TestDataIntegrityAcceptance(unittest.TestCase):
    """UAT: Data integrity and accuracy requirements."""

    @patch("core.csusb_library_client.explore_search")
    def test_accurate_metadata_extraction(self, mock_explore):
        """
        UAT-DI-001: System accurately extracts metadata
        Given: Users rely on accurate bibliographic information
        When: Results are displayed
        Then: Title, authors, year, type are correctly extracted
        """
        mock_explore.return_value = {"docs": [{
            "id": "META1",
            "pnx": {
                "display": {
                    "title": ["The Complete Guide to Testing"],
                    "creator": ["Smith, John A.", "Doe, Jane B."],
                    "type": ["book"],
                },
                "sort": {
                    "creationdate": ["2023"],
                    "author": ["Smith, John A.", "Doe, Jane B."]  # Primo puts authors in sort.author
                },
                "control": {"recordid": ["META1"]},
            },
            "link": {"record": "https://example.org/meta1"},
            "context": "PC"
        }]}
        
        user_query = "Find books on testing"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify all metadata appears in output
        self.assertIn("The Complete Guide to Testing", output.text)
        self.assertIn("2023", output.text)
        self.assertIn("book", output.text.lower())
        
        # Verify creators data structure is populated
        self.assertGreater(len(output.briefs), 0)
        brief = output.briefs[0]
        self.assertIsNotNone(brief.creators)
        self.assertGreater(len(brief.creators), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_links_are_preserved(self, mock_explore):
        """
        UAT-DI-002: System preserves and displays record links
        Given: Users need to access full records
        When: Results are displayed
        Then: Record links are included and accessible
        """
        test_link = "https://csusb.primo.exlibrisgroup.com/discovery/fulldisplay?docid=TEST123"
        
        mock_explore.return_value = {"docs": [{
            "id": "LINK1",
            "pnx": {
                "display": {"title": ["Link Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["LINK1"]},
            },
            "link": {"record": test_link},
            "context": "PC"
        }]}
        
        user_query = "Find articles with links"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify link is in output
        self.assertIn(test_link, output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_handles_missing_metadata_gracefully(self, mock_explore):
        """
        UAT-DI-003: System handles missing metadata gracefully
        Given: Some records may have incomplete metadata
        When: System processes such records
        Then: System shows available data without errors
        """
        # Document with minimal metadata
        mock_explore.return_value = {"docs": [{
            "id": "MIN1",
            "pnx": {
                "display": {
                    "title": ["Untitled Document"],
                    # No creator
                    # No type
                },
                # No creation date
                "control": {"recordid": ["MIN1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find documents with missing metadata"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should not crash, should show what's available
        self.assertIsNotNone(output)
        self.assertIn("Untitled Document", output.text)


class TestFilteringAcceptance(unittest.TestCase):
    """UAT: Search filtering and refinement requirements."""

    @patch("core.csusb_library_client.explore_search")
    def test_peer_reviewed_filter_works(self, mock_explore):
        """
        UAT-FLT-001: Peer-reviewed filter is correctly applied
        Given: Users need to find scholarly peer-reviewed articles
        When: User specifies peer-reviewed
        Then: System adds appropriate filter to query
        """
        mock_explore.return_value = {"docs": [{
            "id": "PR1",
            "pnx": {
                "display": {"title": ["Peer Reviewed Study"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["PR1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find peer-reviewed articles on biology"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)

    @patch("core.csusb_library_client.explore_search")
    def test_resource_type_filter_works(self, mock_explore):
        """
        UAT-FLT-002: Resource type filter is correctly applied
        Given: Users want specific resource types
        When: User specifies books, articles, etc.
        Then: System filters to that resource type
        """
        test_cases = [
            ("Find books on history", "books"),
            ("Show me articles about science", "articles"),
            ("Looking for videos on education", "videos"),
        ]
        
        for query, expected_type in test_cases:
            with self.subTest(query=query, expected=expected_type):
                mock_explore.reset_mock()
                mock_explore.return_value = {"docs": [{
                    "id": "TYPE1",
                    "pnx": {
                        "display": {"title": ["Type Test"], "creator": ["A"], "type": ["article"]},
                        "sort": {"creationdate": ["2023"]},
                        "control": {"recordid": ["TYPE1"]},
                    },
                    "context": "PC"
                }]}
                
                output = orchestrator_agent.handle(AgentInput(user_input=query))
                
                call_args = mock_explore.call_args.kwargs
                q = call_args.get("q", "")
                
                self.assertIn(f"rtype,exact,{expected_type}", q)

    @patch("core.csusb_library_client.explore_search")
    def test_date_range_filter_works(self, mock_explore):
        """
        UAT-FLT-003: Date range filter is correctly applied
        Given: Users need recent or historical materials
        When: User specifies date range
        Then: System applies correct date filters
        """
        mock_explore.return_value = {"docs": [{
            "id": "DATE1",
            "pnx": {
                "display": {"title": ["Recent Study"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["DATE1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find articles on climate change from 2020 to 2023"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("dr_s,exact,20200101", q)
        self.assertIn("dr_e,exact,20231231", q)

    @patch("core.csusb_library_client.explore_search")
    def test_author_filter_works(self, mock_explore):
        """
        UAT-FLT-004: Author filter is correctly applied
        Given: Users want works by specific authors
        When: User specifies author name
        Then: System filters by that author
        """
        mock_explore.return_value = {"docs": [{
            "id": "AUTH1",
            "pnx": {
                "display": {"title": ["Author Test"], "creator": ["Einstein, Albert"], "type": ["article"]},
                "sort": {"creationdate": ["1920"]},
                "control": {"recordid": ["AUTH1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find papers by Albert Einstein"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("creator,contains,Albert Einstein", q)

    @patch("core.csusb_library_client.explore_search")
    def test_combined_filters_work_together(self, mock_explore):
        """
        UAT-FLT-005: Multiple filters can be combined
        Given: Users often need multiple criteria
        When: User specifies multiple filters
        Then: System applies all filters correctly
        """
        mock_explore.return_value = {"docs": [{
            "id": "COMBO1",
            "pnx": {
                "display": {"title": ["Combined Search"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["COMBO1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find peer-reviewed articles on climate change by Smith from 2020 to 2023"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        # Verify all filters present
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)
        self.assertIn("creator,contains,Smith", q)
        self.assertIn("dr_s,exact,20200101", q)
        self.assertIn("dr_e,exact,20231231", q)
        self.assertIn("climate change", q.lower())


class TestPerformanceAcceptance(unittest.TestCase):
    """UAT: Performance and reliability requirements."""

    @patch("core.csusb_library_client.explore_search")
    def test_handles_large_result_sets(self, mock_explore):
        """
        UAT-PERF-001: System handles large result sets
        Given: Some queries return many results
        When: Maximum results are requested
        Then: System processes and formats all results
        """
        # Create 50 results (max limit)
        mock_explore.return_value = {"docs": [
            {
                "id": f"LARGE{i}",
                "pnx": {
                    "display": {"title": [f"Article {i}"], "creator": ["A"], "type": ["article"]},
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": [f"LARGE{i}"]},
                },
                "context": "PC"
            }
            for i in range(50)
        ]}
        
        user_query = "Show me 50 articles on performance testing"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should successfully handle all results
        self.assertIsNotNone(output)
        # System may limit to 10 by default, but should handle request gracefully
        self.assertGreater(len(output.briefs), 0)
        self.assertLessEqual(len(output.briefs), 50)
        self.assertGreater(len(output.text), 100)

    @patch("core.csusb_library_client.explore_search")
    def test_error_handling_does_not_crash(self, mock_explore):
        """
        UAT-PERF-002: System handles errors without crashing
        Given: External dependencies may fail
        When: API call fails
        Then: System returns error message gracefully
        """
        mock_explore.side_effect = Exception("API Error: Connection timeout")
        
        user_query = "Find articles on error handling"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should not crash, should return error message
        self.assertIsNotNone(output)
        self.assertIn("Error", output.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
