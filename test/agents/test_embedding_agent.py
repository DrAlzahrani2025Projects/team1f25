# test/agents/test_embedding_agent.py
import unittest
from unittest.mock import patch, MagicMock
from core.embedding_model import Embedder
from agents import embedding_agent
import json

class TestEmbeddingAgent(unittest.TestCase):
    def setUp(self):
        # sample record with PNX-like structure and brief
        self.record = {
            "id": "rec1",
            "pnx": {
                "display": {"title": ["The Title"], "creator": ["Alice", "Bob"]},
                "addata": {"abstract": ["An abstract."]},
                "search": {"subject": ["Topic A", "Topic B"]},
                "sort": {"creationdate": ["2020"]},
                "display_extra": {}
            },
            "brief": {
                "record_id": "rec1",
                "title": "The Title",
                "creators": ["Alice", "Bob"],
                "creation_date": "2020",
                "resource_type": "article",
                "context": "test",
                "source": "primo"
            },
            "links": {"record": "http://example.com/rec1"}
        }

    def test_record_to_text(self):
        text = embedding_agent._record_to_text(self.record)
        # should contain title, creators, year, abstract and subjects
        self.assertIn("The Title", text)
        self.assertIn("Alice", text)
        self.assertIn("2020", text)
        self.assertIn("An abstract.", text)
        self.assertIn("Topic A", text)

    def test_brief_meta(self):
        meta = embedding_agent._brief_meta(self.record)
        self.assertEqual(meta["record_id"], "rec1")
        self.assertEqual(meta["title"], "The Title")
        self.assertEqual(meta["permalink"], "http://example.com/rec1")
        self.assertEqual(meta["creators"], ["Alice", "Bob"])

    def test_chunks(self):
        # generate text of 1000 words "w0 w1 ..." to ensure chunking
        words = [f"w{i}" for i in range(1000)]
        text = " ".join(words)
        chunks = embedding_agent._chunks(text, size=200, overlap=50)
        # step = 150, so expect ceil((1000 - 200) / 150) + 1 = 6 or 7
        self.assertTrue(len(chunks) >= 5)
        # ensure no chunk is longer than size (words joined)
        for ch in chunks:
            self.assertLessEqual(len(ch.split()), 200)

    @patch("agents.embedding_agent.get_collection")
    @patch("agents.embedding_agent.upsert")
    @patch("agents.embedding_agent.get_existing_ids")
    @patch("agents.embedding_agent.Embedder")
    def test_upsert_records(self, mock_embedder_cls, mock_get_existing, mock_upsert, mock_get_coll):
        # prepare embedder mock
        mock_embedder = MagicMock()
        # return two-dim vectors for each doc
        mock_embedder.embed.return_value = [[0.1, 0.2]]
        mock_embedder_cls.return_value = mock_embedder

        # collection and existing ids
        mock_get_coll.return_value = MagicMock()
        mock_get_existing.return_value = []

        # upsert returns number of added items
        def upsert_side(coll, ids, docs, metas, emb):
            return len(ids)
        mock_upsert.side_effect = upsert_side

        # record with text split into multiple chunks
        rec = self.record.copy()
        # make content that will split into 3 chunks of ~5 words
        rec_text = "one two three four five six seven eight nine ten"
        # patch _record_to_text to return this small text so _chunks produces splits
        with patch("agents.embedding_agent._record_to_text", return_value=rec_text):
            # use small chunk size to force multiple chunks
            result = embedding_agent.upsert_records([rec], batch=128)

        # verify upsert was called and returned counts
        self.assertIn("added", result)
        self.assertIn("skipped_empty", result)
        self.assertGreaterEqual(result["added"], 1)

    @patch("agents.embedding_agent.os.path.exists")
    @patch("agents.embedding_agent.upsert_records")
    def test_index_jsonl(self, mock_upsert_records, mock_exists):
        # simulate file exists
        mock_exists.return_value = True
        sample = json.dumps(self.record)
        # patch open to return our single-line JSONL content
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value = [sample + "\n"]
        with patch("builtins.open", mock_open):
            mock_upsert_records.return_value = {"added": 1, "skipped_empty": 0}
            res = embedding_agent.index_jsonl("/fake/path.jsonl", batch=128)
        self.assertEqual(res, {"added": 1, "skipped_empty": 0})


if __name__ == '__main__':
    unittest.main(verbosity=2)


