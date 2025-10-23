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

    # Additional test cases for build_q
    def test_build_q_empty_query(self):
        q = build_q("", lang_code=None, peer_reviewed=False, rtype=None)
        self.assertIn("any,contains,", q)
        # Should still have basic structure

    def test_build_q_all_parameters(self):
        q = build_q(
            "machine learning", 
            lang_code="eng", 
            peer_reviewed=True, 
            rtype="books",
            authors=["Andrew Ng", "Yann LeCun"],
            dr_s="20150101",
            dr_e="20231231"
        )
        self.assertIn("any,contains,machine learning", q)
        self.assertIn("creator,contains,Andrew Ng", q)
        self.assertIn("creator,contains,Yann LeCun", q)
        self.assertIn("dr_s,exact,20150101", q)
        self.assertIn("dr_e,exact,20231231", q)
        self.assertIn("lang,exact,eng", q)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertIn("rtype,exact,books", q)

    def test_build_q_single_author(self):
        q = build_q("AI", lang_code=None, peer_reviewed=False, rtype=None, authors=["Einstein"])
        self.assertIn("creator,contains,Einstein", q)
        self.assertIn("any,contains,AI", q)

    def test_build_q_no_lang_no_peer_no_type(self):
        q = build_q("physics", lang_code=None, peer_reviewed=False, rtype=None)
        self.assertIn("any,contains,physics", q)
        self.assertNotIn("lang,exact,", q)
        self.assertNotIn("facet_tlevel", q)
        self.assertNotIn("rtype,exact,", q)

    def test_build_q_only_peer_reviewed(self):
        q = build_q("chemistry", lang_code=None, peer_reviewed=True, rtype=None)
        self.assertIn("facet_tlevel,exact,peer_reviewed", q)
        self.assertNotIn("rtype,exact,", q)

    def test_build_q_only_type(self):
        q = build_q("biology", lang_code=None, peer_reviewed=False, rtype="dissertations")
        self.assertIn("rtype,exact,dissertations", q)
        self.assertNotIn("facet_tlevel", q)

    def test_build_q_multiple_authors_no_dates(self):
        q = build_q("quantum mechanics", lang_code="eng", peer_reviewed=False, rtype=None, 
                   authors=["Feynman", "Dirac", "Heisenberg"])
        self.assertIn("creator,contains,Feynman", q)
        self.assertIn("creator,contains,Dirac", q)
        self.assertIn("creator,contains,Heisenberg", q)

    def test_build_q_empty_author_list(self):
        q = build_q("test", lang_code=None, peer_reviewed=False, rtype=None, authors=[])
        self.assertIn("any,contains,test", q)
        self.assertNotIn("creator,contains,", q)

    def test_build_q_whitespace_author(self):
        q = build_q("test", lang_code=None, peer_reviewed=False, rtype=None, authors=["  ", "Valid Name"])
        # Empty/whitespace author should be skipped
        self.assertIn("creator,contains,Valid Name", q)
        # The whitespace-only author should not create an empty creator clause


if __name__ == "__main__":
    unittest.main(verbosity=2)
