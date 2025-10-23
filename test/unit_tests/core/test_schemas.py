import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.schemas import AgentInput, SearchBrief, QAHit, AgentOutput


class TestSchemas(unittest.TestCase):
    def test_agent_input_basic(self):
        ai = AgentInput(user_input="test query")
        self.assertEqual(ai.user_input, "test query")

    def test_agent_input_empty(self):
        ai = AgentInput(user_input="")
        self.assertEqual(ai.user_input, "")

    def test_search_brief_minimal(self):
        sb = SearchBrief(record_id="TEST123")
        self.assertEqual(sb.record_id, "TEST123")
        self.assertEqual(sb.title, "")
        self.assertEqual(sb.creators, [])
        self.assertEqual(sb.creation_date, "")
        self.assertIsNone(sb.resource_type)
        self.assertEqual(sb.context, "PC")
        self.assertIsNone(sb.permalink)

    def test_search_brief_full(self):
        sb = SearchBrief(
            record_id="RID456",
            title="Test Article",
            creators=["Author One", "Author Two"],
            creation_date="2023",
            resource_type="article",
            context="L",
            permalink="https://example.org/rid456"
        )
        self.assertEqual(sb.record_id, "RID456")
        self.assertEqual(sb.title, "Test Article")
        self.assertEqual(len(sb.creators), 2)
        self.assertEqual(sb.creation_date, "2023")
        self.assertEqual(sb.resource_type, "article")
        self.assertEqual(sb.context, "L")
        self.assertEqual(sb.permalink, "https://example.org/rid456")

    def test_search_brief_defaults(self):
        sb = SearchBrief(record_id="ID1", title="Title Only")
        self.assertEqual(sb.creators, [])
        self.assertEqual(sb.creation_date, "")
        self.assertEqual(sb.context, "PC")

    def test_qa_hit_basic(self):
        qa = QAHit(text="Sample answer")
        self.assertEqual(qa.text, "Sample answer")
        self.assertEqual(qa.meta, {})

    def test_qa_hit_with_meta(self):
        meta_data = {"source": "doc1", "score": 0.95}
        qa = QAHit(text="Answer text", meta=meta_data)
        self.assertEqual(qa.text, "Answer text")
        self.assertEqual(qa.meta["source"], "doc1")
        self.assertEqual(qa.meta["score"], 0.95)

    def test_agent_output_minimal(self):
        ao = AgentOutput(text="Response text")
        self.assertEqual(ao.text, "Response text")
        self.assertEqual(ao.list_items, [])
        self.assertEqual(ao.hits, [])
        self.assertEqual(ao.briefs, [])
        self.assertFalse(ao.await_export)

    def test_agent_output_with_briefs(self):
        briefs = [
            SearchBrief(record_id="B1", title="Brief 1"),
            SearchBrief(record_id="B2", title="Brief 2")
        ]
        ao = AgentOutput(text="Results", briefs=briefs)
        self.assertEqual(len(ao.briefs), 2)
        self.assertEqual(ao.briefs[0].record_id, "B1")
        self.assertEqual(ao.briefs[1].title, "Brief 2")

    def test_agent_output_with_hits(self):
        hits = [
            QAHit(text="Hit 1", meta={"source": "s1"}),
            QAHit(text="Hit 2", meta={"source": "s2"})
        ]
        ao = AgentOutput(text="QA Results", hits=hits)
        self.assertEqual(len(ao.hits), 2)
        self.assertEqual(ao.hits[0].text, "Hit 1")

    def test_agent_output_full(self):
        briefs = [SearchBrief(record_id="ID1", title="T1")]
        hits = [QAHit(text="Answer")]
        list_items = ["Item 1", "Item 2"]
        ao = AgentOutput(
            text="Complete output",
            list_items=list_items,
            hits=hits,
            briefs=briefs,
            await_export=True
        )
        self.assertEqual(ao.text, "Complete output")
        self.assertEqual(len(ao.list_items), 2)
        self.assertEqual(len(ao.hits), 1)
        self.assertEqual(len(ao.briefs), 1)
        self.assertTrue(ao.await_export)

    def test_search_brief_multiple_creators(self):
        creators = ["Smith, J.", "Doe, J.", "Lee, B."]
        sb = SearchBrief(
            record_id="MC1",
            title="Multi-author work",
            creators=creators
        )
        self.assertEqual(len(sb.creators), 3)
        self.assertIn("Smith, J.", sb.creators)
        self.assertIn("Doe, J.", sb.creators)

    def test_search_brief_empty_creators(self):
        sb = SearchBrief(record_id="EC1", creators=[])
        self.assertEqual(sb.creators, [])

    def test_agent_output_empty_lists(self):
        ao = AgentOutput(text="Empty", list_items=[], hits=[], briefs=[])
        self.assertEqual(len(ao.list_items), 0)
        self.assertEqual(len(ao.hits), 0)
        self.assertEqual(len(ao.briefs), 0)

    def test_search_brief_resource_types(self):
        types = ["article", "book", "dissertation", "video", "dataset"]
        for rtype in types:
            sb = SearchBrief(record_id=f"RT_{rtype}", resource_type=rtype)
            self.assertEqual(sb.resource_type, rtype)

    def test_search_brief_contexts(self):
        contexts = ["PC", "L", "XYZ"]
        for ctx in contexts:
            sb = SearchBrief(record_id=f"CTX_{ctx}", context=ctx)
            self.assertEqual(sb.context, ctx)


if __name__ == "__main__":
    unittest.main(verbosity=2)
