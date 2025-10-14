# business_logic/rules.py

class Citation:
    def __init__(self, source_id, span):
        if not source_id or not span:
            raise ValueError("Invalid citation")
        self.source_id = source_id
        self.span = span


class AnswerPolicy:
    def __init__(self, require_citations=True):
        self.require_citations = require_citations


class Answer:
    def __init__(self, query_id, text, policy: AnswerPolicy):
        self.query_id = query_id
        self.text = text
        self.policy = policy
        self.citations = []

    def add_citation(self, citation: Citation):
        self.citations.append(citation)

    def finalize(self):
        if self.policy.require_citations and not self.citations:
            raise ValueError("Missing citation")
        return {
            "query_id": self.query_id,
            "text": self.text,
            "citations": [c.__dict__ for c in self.citations],
        }

