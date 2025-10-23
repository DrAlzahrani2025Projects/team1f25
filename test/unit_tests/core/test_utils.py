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


if __name__ == "__main__":
    unittest.main(verbosity=2)
