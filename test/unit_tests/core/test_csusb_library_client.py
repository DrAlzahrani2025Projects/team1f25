import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.csusb_library_client import build_q


class TestPrimoQueryBuilder(unittest.TestCase):
    def test_build_q_basic(self):
        q = build_q("climate change", lang_code="eng", peer_reviewed=False, rtype=None)
        self.assertIn("any,contains,climate change", q)
        self.assertIn("lang,exact,eng", q)
        self.assertNotIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertNotIn("rtype,exact,", q)

    def test_build_q_with_peer_reviewed_and_type(self):
        q = build_q("ai", lang_code=None, peer_reviewed=True, rtype="articles")
        self.assertIn("any,contains,ai", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,articles", q)

    def test_build_q_with_authors(self):
        q = build_q("ml", lang_code=None, peer_reviewed=False, rtype=None, authors=["Jane Doe", "Alan Turing"]) 
        # Ensure both creator clauses are present
        self.assertIn("creator,contains,Jane Doe", q)
        self.assertIn("creator,contains,Alan Turing", q)
        # AND separators join parts
        self.assertIn(",AND;", q)

    def test_build_q_with_date_range(self):
        q = build_q("quantum", lang_code="eng", peer_reviewed=False, rtype="articles", dr_s="20180101", dr_e="20201231")
        self.assertIn("any,contains,quantum", q)
        self.assertIn("dr_s,exact,20180101", q)
        self.assertIn("dr_e,exact,20201231", q)
        self.assertIn("rtype,exact,articles", q)


if __name__ == "__main__":
    unittest.main(verbosity=2)
