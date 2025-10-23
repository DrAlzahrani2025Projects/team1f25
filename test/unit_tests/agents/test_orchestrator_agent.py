import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import orchestrator_agent
from core.schemas import AgentInput


class TestOrchestratorAgent(unittest.TestCase):
    def test_handle_empty_terms(self):
        out = orchestrator_agent.handle(AgentInput(user_input="Show top 5"))
        self.assertIn("Please provide search terms", out.text)
        self.assertEqual(out.briefs, [])

    # Additional test cases for orchestrator_agent
    def test_handle_empty_input(self):
        out = orchestrator_agent.handle(AgentInput(user_input=""))
        self.assertIn("Please provide search terms", out.text)

    def test_handle_whitespace_only(self):
        out = orchestrator_agent.handle(AgentInput(user_input="   "))
        self.assertIn("Please provide search terms", out.text)

    def test_handle_just_commands(self):
        out = orchestrator_agent.handle(AgentInput(user_input="show list find retrieve"))
        self.assertIn("Please provide search terms", out.text)

    def test_format_list_empty(self):
        result = orchestrator_agent._format_list([], "test")
        self.assertIn("Top 0 results", result)
        self.assertIn("test", result)

    def test_format_list_single_result(self):
        from core.schemas import SearchBrief
        brief = SearchBrief(
            record_id="TEST1",
            title="Test Title",
            creators=["Author One"],
            creation_date="2020",
            resource_type="article",
            context="PC",
            permalink="https://example.org/test1"
        )
        result = orchestrator_agent._format_list([brief], "machine learning")
        self.assertIn("Top 1 results", result)
        self.assertIn("machine learning", result)
        self.assertIn("Test Title", result)
        self.assertIn("Author One", result)
        self.assertIn("2020", result)
        self.assertIn("article", result)
        self.assertIn("[https://example.org/test1]", result)

    def test_format_list_multiple_results(self):
        from core.schemas import SearchBrief
        briefs = [
            SearchBrief(
                record_id=f"ID{i}",
                title=f"Title {i}",
                creators=[f"Author {i}"],
                creation_date=str(2020 + i),
                resource_type="article",
                context="PC",
                permalink=f"https://example.org/id{i}"
            )
            for i in range(3)
        ]
        result = orchestrator_agent._format_list(briefs, "AI")
        self.assertIn("Top 3 results", result)
        self.assertIn("Title 0", result)
        self.assertIn("Title 1", result)
        self.assertIn("Title 2", result)

    def test_format_list_missing_fields(self):
        from core.schemas import SearchBrief
        brief = SearchBrief(
            record_id="MIN1",
            title="",
            creators=[],
            creation_date="",
            resource_type=None,
            context="PC",
            permalink=""
        )
        result = orchestrator_agent._format_list([brief], "query")
        self.assertIn("Untitled", result)
        self.assertIn("—", result)  # em dash for missing fields

    def test_format_list_multiple_authors(self):
        from core.schemas import SearchBrief
        brief = SearchBrief(
            record_id="MA1",
            title="Multi-author Paper",
            creators=["Smith, John", "Doe, Jane", "Lee, Bob"],
            creation_date="2021",
            resource_type="article",
            context="PC",
            permalink="https://example.org/ma1"
        )
        result = orchestrator_agent._format_list([brief], "research")
        self.assertIn("Smith, John, Doe, Jane, Lee, Bob", result)

    def test_format_list_markdown_table_structure(self):
        from core.schemas import SearchBrief
        brief = SearchBrief(
            record_id="TBL1",
            title="Table Test",
            creators=["Author"],
            creation_date="2022",
            resource_type="book",
            context="PC",
            permalink="https://example.org/tbl1"
        )
        result = orchestrator_agent._format_list([brief], "test")
        # Check for markdown table structure
        self.assertIn("|", result)
        self.assertIn("Type", result)
        self.assertIn("Title", result)
        self.assertIn("Authors", result)
        self.assertIn("Year", result)
        self.assertIn("Link", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
