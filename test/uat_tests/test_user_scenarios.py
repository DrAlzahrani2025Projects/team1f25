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


class TestStudentResearchScenarios(unittest.TestCase):
    """UAT: Student research scenarios - typical undergraduate/graduate student use cases."""

    def _create_realistic_response(self, topic, count=5):
        """Create realistic academic search results."""
        docs = []
        for i in range(count):
            docs.append({
                "id": f"DOC{i}",
                "pnx": {
                    "display": {
                        "title": [f"Research on {topic}: A Comprehensive Study"],
                        "creator": ["Smith, John A.", "Doe, Jane B."],
                        "type": ["article"],
                    },
                    "sort": {"creationdate": [f"202{i}"]},
                    "search": {"rtype": ["article"]},
                    "control": {"recordid": [f"DOC{i}"]},
                },
                "link": {"record": f"https://example.org/doc{i}"},
                "context": "PC",
            })
        return {"docs": docs}

    @patch("core.csusb_library_client.explore_search")
    def test_undergraduate_finds_articles_for_essay(self, mock_explore):
        """
        UAT-001: Undergraduate student searches for articles for an essay
        Given: A student needs 5-10 articles on climate change for an essay
        When: They search using natural language
        Then: System returns relevant articles in an easy-to-read format
        """
        mock_explore.return_value = self._create_realistic_response("climate change", 10)
        
        # Natural language query a student would type
        user_query = "Find me 10 articles about climate change for my essay"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify student gets results
        self.assertIsNotNone(output)
        self.assertGreater(len(output.briefs), 0)
        self.assertIn("Top", output.text)
        self.assertIn("climate change", output.text.lower())
        
        # Verify output is readable (has table structure)
        self.assertIn("|", output.text)
        self.assertIn("Title", output.text)
        self.assertIn("Link", output.text)

    @patch("core.csusb_library_client.explore_search")
    def test_graduate_student_finds_recent_research(self, mock_explore):
        """
        UAT-002: Graduate student searches for recent peer-reviewed research
        Given: A grad student needs recent (last 3 years) peer-reviewed papers
        When: They specify peer-reviewed and date range
        Then: System filters appropriately and returns recent scholarly articles
        """
        mock_explore.return_value = self._create_realistic_response("machine learning", 5)
        
        user_query = "Show me peer-reviewed articles on machine learning from 2022 to 2025"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Verify filters were applied
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("dr_s,exact,20220101", q)
        self.assertIn("dr_e,exact,20251231", q)
        self.assertGreater(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_student_searches_by_specific_author(self, mock_explore):
        """
        UAT-003: Student searches for works by a specific author
        Given: Student knows a key researcher in their field
        When: They search by author name
        Then: System filters to that author's works
        """
        mock_explore.return_value = self._create_realistic_response("quantum physics", 3)
        
        user_query = "Find papers by Richard Feynman about quantum physics"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("creator,contains,Richard Feynman", q)
        self.assertIn("quantum physics", q.lower())

    @patch("core.csusb_library_client.explore_search")
    def test_student_finds_books_for_background_reading(self, mock_explore):
        """
        UAT-004: Student looks for books for background reading
        Given: Student needs books for literature review
        When: They specify they want books
        Then: System returns books instead of articles
        """
        mock_explore.return_value = self._create_realistic_response("psychology", 5)
        
        user_query = "Show me books about cognitive psychology"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("rtype,exact,books", q)
        self.assertGreater(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_student_starts_new_topic_broad_search(self, mock_explore):
        """
        UAT-005: Student starts research on new topic with broad search
        Given: Student is new to a topic
        When: They do a simple, broad search
        Then: System returns diverse, introductory results
        """
        mock_explore.return_value = self._create_realistic_response("artificial intelligence", 10)
        
        user_query = "artificial intelligence research"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        self.assertGreater(len(output.briefs), 0)
        self.assertIn("artificial intelligence", output.text.lower())


class TestFacultyResearchScenarios(unittest.TestCase):
    """UAT: Faculty research scenarios - professor and researcher use cases."""

    def _create_scholarly_response(self, count=10):
        docs = []
        for i in range(count):
            docs.append({
                "id": f"SCHOLAR{i}",
                "pnx": {
                    "display": {
                        "title": [f"Advanced Research Study {i}"],
                        "creator": [f"Researcher {i}, Dr."],
                        "type": ["article"],
                    },
                    "sort": {"creationdate": ["2023"]},
                    "search": {"rtype": ["journal"]},
                    "control": {"recordid": [f"SCHOLAR{i}"]},
                },
                "link": {"record": f"https://example.org/scholar{i}"},
                "context": "PC",
            })
        return {"docs": docs}

    @patch("core.csusb_library_client.explore_search")
    def test_faculty_literature_review_comprehensive_search(self, mock_explore):
        """
        UAT-101: Faculty performs comprehensive literature review
        Given: Professor needs extensive literature for grant proposal
        When: They request maximum results with specific criteria
        Then: System returns comprehensive results up to the limit
        """
        mock_explore.return_value = self._create_scholarly_response(50)
        
        user_query = "Show me top 50 peer-reviewed journal articles on neural networks since 2020"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        limit = call_args.get("limit")
        
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)
        self.assertIn("dr_s,exact,20200101", q)
        self.assertLessEqual(limit, 50)  # Respects max limit

    @patch("core.csusb_library_client.explore_search")
    def test_faculty_tracks_colleague_publications(self, mock_explore):
        """
        UAT-102: Faculty tracks colleague's recent publications
        Given: Professor wants to follow a colleague's work
        When: They search by author and recent years
        Then: System shows that author's recent works
        """
        mock_explore.return_value = self._create_scholarly_response(5)
        
        user_query = "Find articles by Dr. Sarah Johnson since 2023"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("creator,contains,Dr. Sarah Johnson", q)
        self.assertIn("dr_s,exact,20230101", q)

    @patch("core.csusb_library_client.explore_search")
    def test_faculty_finds_conference_proceedings(self, mock_explore):
        """
        UAT-103: Faculty searches for conference proceedings
        Given: Professor needs conference papers from specific venues
        When: They specify conference proceedings
        Then: System filters to show conference papers
        """
        mock_explore.return_value = self._create_scholarly_response(8)
        
        user_query = "Show me conference proceedings on computer vision"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("rtype,exact,conference_proceedings", q)


class TestLibrarianAssistanceScenarios(unittest.TestCase):
    """UAT: Librarian helping patrons - reference desk scenarios."""

    @patch("core.csusb_library_client.explore_search")
    def test_librarian_helps_student_with_no_results(self, mock_explore):
        """
        UAT-201: Librarian helps when student gets no results
        Given: Student's search returns nothing
        When: Librarian sees the "no results" message
        Then: System clearly indicates no results found
        """
        mock_explore.return_value = {"docs": []}
        
        user_query = "Find articles on xyz123nonexistent999topic"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        self.assertIn("No results found", output.text)
        self.assertEqual(len(output.briefs), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_librarian_demonstrates_date_filtering(self, mock_explore):
        """
        UAT-202: Librarian demonstrates date range filtering
        Given: Librarian teaching a student about date filters
        When: They demonstrate "between" date syntax
        Then: System correctly applies the date range
        """
        mock_explore.return_value = {"docs": [{
            "id": "DEMO1",
            "pnx": {
                "display": {"title": ["Demo"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2020"]},
                "control": {"recordid": ["DEMO1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find articles on climate between 2018 and 2022"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("dr_s,exact,20180101", q)
        self.assertIn("dr_e,exact,20221231", q)

    @patch("core.csusb_library_client.explore_search")
    def test_librarian_shows_multiple_authors_search(self, mock_explore):
        """
        UAT-203: Librarian demonstrates searching multiple authors
        Given: Librarian teaching advanced search
        When: They show how to search multiple authors
        Then: System includes all authors in the query
        """
        mock_explore.return_value = {"docs": [{
            "id": "MULTI1",
            "pnx": {
                "display": {"title": ["Collaboration"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["MULTI1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Show papers by Einstein and Bohr on physics"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        self.assertIn("creator,contains,Einstein", q)
        self.assertIn("creator,contains,Bohr", q)


class TestAccessibilityAndUsabilityScenarios(unittest.TestCase):
    """UAT: Accessibility and usability scenarios - diverse user needs."""

    @patch("core.csusb_library_client.explore_search")
    def test_user_with_simple_query_gets_clear_results(self, mock_explore):
        """
        UAT-301: Non-technical user with simple query
        Given: User not familiar with academic databases
        When: They type a simple, conversational query
        Then: System understands and returns results
        """
        mock_explore.return_value = {"docs": [{
            "id": "SIMPLE1",
            "pnx": {
                "display": {"title": ["Dogs Research"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["SIMPLE1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "I need information about dogs"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should work despite informal language
        self.assertGreater(len(output.briefs), 0)
        self.assertIn("dogs", output.text.lower())

    @patch("core.csusb_library_client.explore_search")
    def test_output_format_is_readable(self, mock_explore):
        """
        UAT-302: Output format is clear and readable
        Given: Any user performs a search
        When: Results are returned
        Then: Output is well-formatted with clear structure
        """
        mock_explore.return_value = {"docs": [
            {
                "id": f"FMT{i}",
                "pnx": {
                    "display": {
                        "title": [f"Article {i}"],
                        "creator": [f"Author {i}"],
                        "type": ["article"]
                    },
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": [f"FMT{i}"]},
                },
                "link": {"record": f"https://example.org/fmt{i}"},
                "context": "PC"
            }
            for i in range(3)
        ]}
        
        user_query = "Show me 3 articles on testing"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Check for table headers
        self.assertIn("Type", output.text)
        self.assertIn("Title", output.text)
        self.assertIn("Authors", output.text)
        self.assertIn("Year", output.text)
        self.assertIn("Link", output.text)
        
        # Check for table structure
        lines = output.text.split("\n")
        table_lines = [l for l in lines if l.strip().startswith("|")]
        self.assertGreaterEqual(len(table_lines), 5)  # Header + separator + 3 data rows

    @patch("core.csusb_library_client.explore_search")
    def test_links_are_clickable_and_formatted(self, mock_explore):
        """
        UAT-303: Links in output are properly formatted as clickable
        Given: User receives search results
        When: They view the output
        Then: Links are formatted as clickable Markdown links
        """
        mock_explore.return_value = {"docs": [{
            "id": "LINK1",
            "pnx": {
                "display": {"title": ["Test"], "creator": ["A"], "type": ["article"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["LINK1"]},
            },
            "link": {"record": "https://example.org/link1"},
            "context": "PC"
        }]}
        
        user_query = "Show me articles on links"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Check for Markdown link format
        import re
        markdown_links = re.findall(r'\[https?://[^\]]+\]\(https?://[^\)]+\)', output.text)
        self.assertGreater(len(markdown_links), 0)


class TestErrorRecoveryScenarios(unittest.TestCase):
    """UAT: Error recovery and help - handling user mistakes gracefully."""

    @patch("core.csusb_library_client.explore_search")
    def test_user_forgets_search_terms(self, mock_explore):
        """
        UAT-401: User forgets to include actual search terms
        Given: User types command words but no topic
        When: System processes the request
        Then: System provides helpful error message
        """
        # These should not call the API (truly empty)
        empty_queries = [
            "",
            "   ",
        ]
        
        for query in empty_queries:
            with self.subTest(query=query):
                output = orchestrator_agent.handle(AgentInput(user_input=query))
                
                self.assertIn("Please provide search terms", output.text)
                self.assertFalse(mock_explore.called)
                mock_explore.reset_mock()

    @patch("core.csusb_library_client.explore_search")
    def test_system_handles_special_characters(self, mock_explore):
        """
        UAT-402: User includes special characters in search
        Given: User searches for programming languages or technical terms
        When: Query includes special characters
        Then: System handles them gracefully
        """
        mock_explore.return_value = {"docs": [{
            "id": "SPEC1",
            "pnx": {
                "display": {"title": ["C++ Programming"], "creator": ["A"], "type": ["book"]},
                "sort": {"creationdate": ["2023"]},
                "control": {"recordid": ["SPEC1"]},
            },
            "context": "PC"
        }]}
        
        user_query = "Find books about C++ programming"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should handle without error
        self.assertIsNotNone(output)
        self.assertGreater(len(output.text), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_system_recovers_from_api_errors(self, mock_explore):
        """
        UAT-403: System gracefully handles API errors
        Given: Backend API has an issue
        When: User performs a search
        Then: System shows user-friendly error message
        """
        mock_explore.side_effect = Exception("Database connection failed")
        
        user_query = "Show me articles on databases"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        # Should not crash, should show error
        self.assertIsNotNone(output)
        self.assertIn("Error", output.text)


class TestRealWorldWorkflowScenarios(unittest.TestCase):
    """UAT: Real-world research workflows - complex multi-step scenarios."""

    @patch("core.csusb_library_client.explore_search")
    def test_senior_thesis_research_workflow(self, mock_explore):
        """
        UAT-501: Student working on senior thesis
        Given: Senior student doing comprehensive research
        When: They perform multiple related searches
        Then: Each search builds on previous findings
        """
        mock_explore.return_value = {"docs": [
            {
                "id": f"THESIS{i}",
                "pnx": {
                    "display": {
                        "title": [f"Research Article {i}"],
                        "creator": ["Scholar, Dr."],
                        "type": ["article"]
                    },
                    "sort": {"creationdate": ["2023"]},
                    "control": {"recordid": [f"THESIS{i}"]},
                },
                "link": {"record": f"https://example.org/thesis{i}"},
                "context": "PC"
            }
            for i in range(3)
        ]}
        
        # Workflow: Broad → Narrow → Specific author
        searches = [
            "Find articles on renewable energy",
            "Show me peer-reviewed articles on solar power from 2020 to 2025",
            "Papers by Dr. Maria Santos on photovoltaic cells",
        ]
        
        for search in searches:
            mock_explore.reset_mock()
            output = orchestrator_agent.handle(AgentInput(user_input=search))
            
            self.assertIsNotNone(output)
            self.assertGreater(len(output.text), 0)

    @patch("core.csusb_library_client.explore_search")
    def test_grant_proposal_research_workflow(self, mock_explore):
        """
        UAT-502: Faculty preparing grant proposal
        Given: Professor needs comprehensive recent literature
        When: They search for recent peer-reviewed research
        Then: System provides extensive, quality results
        """
        mock_explore.return_value = {"docs": [
            {
                "id": f"GRANT{i}",
                "pnx": {
                    "display": {
                        "title": [f"Advanced Study {i}"],
                        "creator": ["Researcher, Prof."],
                        "type": ["article"]
                    },
                    "sort": {"creationdate": ["2024"]},
                    "search": {"rtype": ["journal"]},
                    "control": {"recordid": [f"GRANT{i}"]},
                },
                "link": {"record": f"https://example.org/grant{i}"},
                "context": "PC"
            }
            for i in range(20)
        ]}
        
        user_query = "Show me top 20 peer-reviewed journal articles on nanotechnology since 2022"
        
        output = orchestrator_agent.handle(AgentInput(user_input=user_query))
        
        call_args = mock_explore.call_args.kwargs
        q = call_args.get("q", "")
        
        # Verify comprehensive filters
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)
        self.assertIn("dr_s,exact,20220101", q)
        self.assertGreater(len(output.briefs), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
