import pytest
from core.services.conversation_analyzer import ConversationAnalyzer


def test_is_generic_article_request_basic_phrases():
    generic_examples = [
        "I need articles",
        "help me find articles",
        "find articles",
        "I would like you to help me with find articles",
        "could you find articles for me",
    ]

    for msg in generic_examples:
        assert ConversationAnalyzer.is_generic_article_request(msg), f"Should detect generic: {msg}"


def test_is_generic_article_request_non_generic():
    non_generic = [
        "I need articles about machine learning in healthcare",
        "Find papers on quantum computing",
        "I want articles about gene therapy",
    ]

    for msg in non_generic:
        assert not ConversationAnalyzer.is_generic_article_request(msg), f"Should not detect generic: {msg}"
