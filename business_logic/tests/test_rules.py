from business_logic.rules import Answer, AnswerPolicy, Citation
import pytest

def test_answer_requires_citation():
    policy = AnswerPolicy(require_citations=True)
    ans = Answer("q1", "Relativity", policy)
    try:
        ans.finalize()
        assert False, "Expected ValueError for missing citation"
    except ValueError as e:
        assert "Missing" in str(e)

def test_answer_with_citation_ok():
    policy = AnswerPolicy()
    ans = Answer("q1", "Relativity", policy)
    ans.add_citation(Citation("S1", "p3"))
    result = ans.finalize()
    assert len(result["citations"]) == 1

