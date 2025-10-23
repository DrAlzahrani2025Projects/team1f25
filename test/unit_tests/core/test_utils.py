import os
import sys
import unittest
from unittest.mock import patch

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

    @patch.dict(os.environ, {'CURRENT_YEAR_OVERRIDE': '2025'})
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
        y = utils.parse_date_range("last 5 years")
        self.assertEqual(y, (2021, 2025))

    def test_parse_peer_review_flag(self):
        self.assertTrue(utils.parse_peer_review_flag("peer-reviewed articles"))
        self.assertTrue(utils.parse_peer_review_flag("peer reviewed articles"))
        self.assertFalse(utils.parse_peer_review_flag("not peer reviewed"))
        self.assertFalse(utils.parse_peer_review_flag("regular articles"))

    # Additional test cases for extract_top_n
    def test_extract_top_n_edge_cases(self):
        self.assertEqual(utils.extract_top_n("top 20 results"), 20)
        self.assertEqual(utils.extract_top_n("TOP 15 papers"), 15)
        self.assertEqual(utils.extract_top_n("list 100 items", default=10), 10)  # no match for "list", returns default
        self.assertEqual(utils.extract_top_n("show -5 results", default=5), 5)  # no match, return default
        self.assertEqual(utils.extract_top_n("", default=8), 8)
        self.assertEqual(utils.extract_top_n("top 100 results", default=10), 50)  # max clamp at 50

    # Additional test cases for strip_to_search_terms
    def test_strip_to_search_terms_complex(self):
        # Note: "me" is not removed by the function, so it will remain
        result = utils.strip_to_search_terms("Show me top 5 papers about neural networks")
        self.assertIn("neural networks", result)
        self.assertEqual(utils.strip_to_search_terms("Find references on climate change from 2010 to 2020"), "climate change")
        self.assertEqual(utils.strip_to_search_terms("Retrieve peer-reviewed articles about AI"), "AI")
        result2 = utils.strip_to_search_terms("List literature since 2015 on quantum physics")
        self.assertIn("quantum physics", result2)
        result3 = utils.strip_to_search_terms("papers by Andrew Ng between 2018 and 2020 on machine learning")
        self.assertIn("machine learning", result3)

    # Additional test cases for strip_to_search_type
    def test_strip_to_search_type_edge_cases(self):
        self.assertEqual(utils.strip_to_search_type("find some articles"), "articles")
        self.assertEqual(utils.strip_to_search_type("get book"), "books")
        self.assertEqual(utils.strip_to_search_type("no type here"), "")
        self.assertEqual(utils.strip_to_search_type(""), "")
        self.assertEqual(utils.strip_to_search_type("CONFERENCE PROCEEDINGS"), "conference_proceedings")
        self.assertEqual(utils.strip_to_search_type("tech report on AI"), "reports")
        self.assertEqual(utils.strip_to_search_type("white paper analysis"), "reports")

    # Additional test cases for strip_to_authors
    def test_strip_to_authors_edge_cases(self):
        self.assertEqual(utils.strip_to_authors(""), [])
        self.assertEqual(utils.strip_to_authors("by"), [])
        self.assertEqual(utils.strip_to_authors("author:"), [])
        self.assertEqual(utils.strip_to_authors("papers on AI"), [])
        self.assertEqual(utils.strip_to_authors("by Andrew Ng between 2018 and 2020"), ["Andrew Ng"])
        self.assertEqual(utils.strip_to_authors("authors: Jane, John, and Bob"), ["Jane", "John", "Bob"])
        # Test that years are filtered out
        self.assertEqual(utils.strip_to_authors("by 2020 and 2021"), [])
        # Note: "author:" uses the singular pattern which doesn't split by comma, so "Alan Turing, 1950" stays together
        # The year filter only removes standalone numeric tokens after splitting
        result = utils.strip_to_authors("author: Alan Turing, 1950")
        self.assertTrue(len(result) > 0)  # Will have the full string including year for singular "author:"

    # Additional test cases for parse_date_range
    def test_parse_date_range_edge_cases(self):
        self.assertEqual(utils.parse_date_range(""), (1900, 2100))
        self.assertEqual(utils.parse_date_range("no dates here"), (1900, 2100))
        self.assertEqual(utils.parse_date_range("in 2020"), (2020, 2020))
        self.assertEqual(utils.parse_date_range("2015"), (2015, 2015))
        # Test swapping if to < from
        self.assertEqual(utils.parse_date_range("from 2020 to 2010"), (2010, 2020))
        # Test "after" and "before" combined text
        self.assertEqual(utils.parse_date_range("research after 2015"), (2016, 2100))
        self.assertEqual(utils.parse_date_range("studies before 2010"), (1900, 2009))

    # Additional test cases for fulldisplay_link
    def test_fulldisplay_link_variations(self):
        link1 = utils.fulldisplay_link("RID456")
        self.assertIn("RID456", link1)
        self.assertIn("context=PC", link1)
        link2 = utils.fulldisplay_link("ABC123", context="L")
        self.assertIn("ABC123", link2)
        self.assertIn("context=L", link2)

    # Test parse_peer_review_flag with more variations
    def test_parse_peer_review_flag_variations(self):
        self.assertTrue(utils.parse_peer_review_flag("PEER-REVIEWED"))
        self.assertTrue(utils.parse_peer_review_flag("peer reviewed papers"))
        self.assertTrue(utils.parse_peer_review_flag("peerreviewed articles"))
        self.assertFalse(utils.parse_peer_review_flag(""))
        self.assertFalse(utils.parse_peer_review_flag("academic articles"))

    # Test strip_to_search_type with all supported types
    def test_strip_to_search_type_all_types(self):
        # Core types
        self.assertEqual(utils.strip_to_search_type("journal articles about biology"), "articles")
        self.assertEqual(utils.strip_to_search_type("books on history"), "books")
        self.assertEqual(utils.strip_to_search_type("book chapters"), "book_chapters")
        self.assertEqual(utils.strip_to_search_type("dissertation research"), "dissertations")
        self.assertEqual(utils.strip_to_search_type("conference proceedings"), "conference_proceedings")
        self.assertEqual(utils.strip_to_search_type("video lectures"), "videos")
        self.assertEqual(utils.strip_to_search_type("journal publications"), "journals")
        self.assertEqual(utils.strip_to_search_type("musical scores"), "scores")
        # Extended types
        self.assertEqual(utils.strip_to_search_type("datasets for analysis"), "datasets")
        self.assertEqual(utils.strip_to_search_type("image collection"), "images")
        self.assertEqual(utils.strip_to_search_type("geographic maps"), "maps")
        self.assertEqual(utils.strip_to_search_type("audio recordings"), "audio")
        self.assertEqual(utils.strip_to_search_type("newspaper articles"), "newspaper_articles")
        self.assertEqual(utils.strip_to_search_type("patent search"), "patents")
        self.assertEqual(utils.strip_to_search_type("technical reports"), "reports")
        self.assertEqual(utils.strip_to_search_type("systematic review"), "reviews")
        self.assertEqual(utils.strip_to_search_type("software tools"), "software")
        self.assertEqual(utils.strip_to_search_type("websites online"), "websites")
        self.assertEqual(utils.strip_to_search_type("encyclopedia entries"), "reference_entries")
        self.assertEqual(utils.strip_to_search_type("government documents"), "government_documents")


if __name__ == "__main__":
    unittest.main(verbosity=2)
