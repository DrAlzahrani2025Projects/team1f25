import os
import sys
import unittest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents import orchestrator_agent
from core.schemas import AgentInput


class TestOrchestratorAgentUnit(unittest.TestCase):
    def test_handle_empty_terms(self):
        out = orchestrator_agent.handle(AgentInput(user_input="Show top 5"))
        self.assertIn("Please provide search terms", out.text)
        self.assertEqual(out.briefs, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
