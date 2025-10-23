import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import utils


class TestUtils(unittest.TestCase):
    def test_extract_top_n_default_and_limits(self):
        self.assertEqual(utils.extract_top_n("show top 5 results"), 5)
        self.assertEqual(utils.extract_top_n("list top 0 items", default=10), 1)  # min clamp
        self.assertEqual(utils.extract_top_n("top 500 please", default=10), 50)  # max clamp
        self.assertEqual(utils.extract_top_n("no number here", default=7), 7)

    def test_strip_to_search_terms(self):
        self.assertEqual(utils.strip_to_search_terms("Show top 10 articles about AI"), "AI")
        self.assertEqual(utils.strip_to_search_terms("Find papers on quantum computing"), "quantum computing")
        self.assertEqual(utils.strip_to_search_terms("retrieve literature on biology"), "biology")
        self.assertEqual(utils.strip_to_search_terms("list references on deep learning"), "deep learning")

    def test_strip_to_search_type_core(self):
        self.assertEqual(utils.strip_to_search_type("journal articles"), "articles")  # articles wins in phrase
        self.assertEqual(utils.strip_to_search_type("book chapters on history"), "book_chapters")
        self.assertEqual(utils.strip_to_search_type("thesis about NLP"), "dissertations")
        self.assertEqual(utils.strip_to_search_type("sheet music Beethoven"), "scores")
        self.assertEqual(utils.strip_to_search_type("maps of Europe"), "maps")
        self.assertEqual(utils.strip_to_search_type("patents on batteries"), "patents")
        self.assertEqual(utils.strip_to_search_type("software for statistics"), "software")
        self.assertEqual(utils.strip_to_search_type("government documents climate"), "government_documents")
        self.assertEqual(utils.strip_to_search_type("movie about physics"), "videos")
        self.assertEqual(utils.strip_to_search_type("encyclopedia entries on birds"), "reference_entries")
        self.assertEqual(utils.strip_to_search_type("web pages on chemistry"), "websites")
        self.assertEqual(utils.strip_to_search_type("review of methods"), "reviews")

    def test_fulldisplay_link(self):
        url = utils.fulldisplay_link("RID123", context="PC")
        self.assertIn("discovery/fulldisplay", url)
        self.assertIn("vid=", url)
        self.assertIn("docid=RID123", url)
        self.assertIn("context=PC", url)

    def test_strip_to_authors_colon_and_by(self):
        self.assertEqual(utils.strip_to_authors("author: Turing, Alan"), ["Turing, Alan"])
        self.assertEqual(utils.strip_to_authors("authors: Andrew Ng, Yann LeCun"), ["Andrew Ng", "Yann LeCun"])
        self.assertEqual(utils.strip_to_authors("papers by Jane Doe and John Smith on AI"), ["Jane Doe", "John Smith"])

    def test_parse_date_range_variants(self):
        y = utils.parse_date_range("since 2019")
        self.assertEqual(y, (2019, 2100))
        y = utils.parse_date_range("from 2015 to 2021")
        self.assertEqual(y, (2015, 2021))
        y = utils.parse_date_range("between 2021 and 2015")
        self.assertEqual(y, (2015, 2021))
        y = utils.parse_date_range("after 2010")
        self.assertEqual(y, (2011, 2100))
        y = utils.parse_date_range("before 2000")
        self.assertEqual(y, (1900, 1999))
        # Use CURRENT_YEAR override for deterministic testing
        os.environ["CURRENT_YEAR_OVERRIDE"] = "2025"
        from importlib import reload
        reload(utils)
        y = utils.parse_date_range("last 5 years")
        self.assertEqual(y, (2021, 2025))
        # Clean override
        os.environ.pop("CURRENT_YEAR_OVERRIDE", None)
        reload(utils)

    def test_parse_peer_review_flag(self):
        self.assertTrue(utils.parse_peer_review_flag("peer-reviewed articles"))
        self.assertTrue(utils.parse_peer_review_flag("peer reviewed articles"))
        self.assertFalse(utils.parse_peer_review_flag("not peer reviewed"))
        self.assertFalse(utils.parse_peer_review_flag("regular articles"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
