# test/agents/test_rag_agent.py
import unittest
from unittest.mock import patch, MagicMock
from agents import rag_agent


class TestRagAgent(unittest.TestCase):
    def setUp(self) -> None:
        # Clear cached singletons so patched constructors are used during tests
        rag_agent._get_embedder.cache_clear()
        rag_agent._get_collection_cached.cache_clear()
        rag_agent._get_qroq_client.cache_clear()

    def test_build_context_formats_hits(self):
        hits = [
            {
                "id": "id1",
                "text": "  Some text for doc1.  ",
                "meta": {"title": "Doc One", "link": "https://example/one"},
                "score": 0.5,
            },
            {
                "id": "id2",
                "text": "\nSecond document text.\n",
                "meta": {"source": "SourceTwo"},
                "score": 0.3,
            },
            {
                "id": "doc3",
                # text missing -> should default to empty string
                "meta": {},
            },
        ]

        context_str, normalized = rag_agent._build_context(hits)

        # Check formatted headers and trimmed texts
        self.assertIn("[1] Doc One — https://example/one", context_str)
        self.assertIn("Some text for doc1.", context_str)
        self.assertIn("[2] SourceTwo", context_str)
        self.assertIn("Second document text.", context_str)
        self.assertIn("[3] doc3", context_str)

        # Normalized hits shape and content
        self.assertEqual(len(normalized), 3)
        for item in normalized:
            self.assertIn("id", item)
            self.assertIn("text", item)
            self.assertIn("meta", item)
            self.assertIn("score", item)

        self.assertEqual(normalized[0]["text"], "Some text for doc1.")
        self.assertEqual(normalized[1]["text"], "Second document text.")
        self.assertEqual(normalized[2]["text"], "")

    def test_rag_answer_calls_dependencies(self):
        question = "What is the test?"

        # Prepare mock instances and return values
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed.return_value = [[0.1, 0.2, 0.3]]

        fake_collection = object()

        fake_hits = [
            {"id": "a", "text": "First", "meta": {"title": "A"}, "score": 0.1},
            {"id": "b", "text": "Second", "meta": {"title": "B"}, "score": 0.2},
        ]

        mock_qroq_instance = MagicMock()
        mock_qroq_instance.chat.return_value = "This is a mocked answer."

        with patch("agents.rag_agent.Embedder") as MockEmbedder, patch(
            "agents.rag_agent.get_collection"
        ) as mock_get_collection, patch("agents.rag_agent.query") as mock_query, patch(
            "agents.rag_agent.QroqClient"
        ) as MockQroq:

            MockEmbedder.return_value = mock_embedder_instance
            mock_get_collection.return_value = fake_collection
            mock_query.return_value = fake_hits
            MockQroq.return_value = mock_qroq_instance

            # Ensure cached getters will construct from the patched classes/functions
            rag_agent._get_embedder.cache_clear()
            rag_agent._get_collection_cached.cache_clear()
            rag_agent._get_qroq_client.cache_clear()

            res = rag_agent.rag_answer(question=question, top_k=2)

            # Embedder called with the question
            mock_embedder_instance.embed.assert_called_once_with([question])

            # get_collection and query were used
            mock_get_collection.assert_called_once()
            mock_query.assert_called_once()
            called_args, called_kwargs = mock_query.call_args
            self.assertIs(called_args[0], fake_collection)
            self.assertEqual(called_args[1], [0.1, 0.2, 0.3])
            self.assertEqual(called_kwargs.get("top_k"), 2)

            # Qroq chat was called and response propagated
            MockQroq.return_value.chat.assert_called_once()
            self.assertEqual(res["answer"], "This is a mocked answer.")
            self.assertEqual(len(res["hits"]), 2)
            self.assertEqual(res["hits"][0]["id"], "a")
            self.assertEqual(res["hits"][1]["id"], "b")

    def test_build_context_handles_alternate_link_fields(self):
        hits = [
            {
                "id": "f1",
                "text": "Text one",
                "meta": {"file": "FileName", "source_url": "https://s.example"},
            },
            {"id": "f2", "text": "", "meta": {"url": "https://u.example"}},
        ]

        context_str, normalized = rag_agent._build_context(hits)

        # Both items should produce headers and include the provided links
        self.assertIn("[1] FileName — https://s.example", context_str)
        self.assertIn("[2] f2 — https://u.example", context_str)
        self.assertEqual(len(normalized), 2)

    def test_build_context_empty_hits_returns_empty(self):
        context_str, normalized = rag_agent._build_context([])
        self.assertEqual(context_str, "")
        self.assertEqual(normalized, [])

    def test_rag_answer_with_no_hits_still_calls_qroq(self):
        question = "No hits question"

        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed.return_value = [[0.9, 0.8]]

        fake_collection = object()
        mock_qroq_instance = MagicMock()
        mock_qroq_instance.chat.return_value = "Answer with no hits"

        with patch("agents.rag_agent.Embedder") as MockEmbedder, patch(
            "agents.rag_agent.get_collection"
        ) as mock_get_collection, patch("agents.rag_agent.query") as mock_query, patch(
            "agents.rag_agent.QroqClient"
        ) as MockQroq:

            MockEmbedder.return_value = mock_embedder_instance
            mock_get_collection.return_value = fake_collection
            mock_query.return_value = []
            MockQroq.return_value = mock_qroq_instance

            rag_agent._get_embedder.cache_clear()
            rag_agent._get_collection_cached.cache_clear()
            rag_agent._get_qroq_client.cache_clear()

            res = rag_agent.rag_answer(question=question, top_k=1)

            mock_embedder_instance.embed.assert_called_once_with([question])
            mock_get_collection.assert_called_once()
            mock_query.assert_called_once()
            MockQroq.return_value.chat.assert_called_once()
            self.assertEqual(res["answer"], "Answer with no hits")
            self.assertEqual(res["hits"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)