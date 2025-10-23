import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.csusb_library_client import explore_search, build_q

RUN_LIVE = os.getenv("PRIMO_LIVE_TESTS") == "1"


@unittest.skipUnless(RUN_LIVE, "Set PRIMO_LIVE_TESTS=1 to run live Primo tests")
class TestPrimoLive(unittest.TestCase):
    def test_live_simple_query(self):
        q = build_q("machine learning", lang_code="eng", peer_reviewed=False, rtype="articles")
        data = explore_search(q=q, limit=3, sort="rank")
        self.assertIn("docs", data)
        self.assertIsInstance(data["docs"], list)
        self.assertLessEqual(len(data["docs"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
