#!/usr/bin/env python
"""Test various journal-related queries"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters

client = GroqClient()

test_cases = [
    "I need 5 journals about machine learning in healthcare",
    "I need 5 journal articles about machine learning in healthcare",
    "Find 3 articles from journals on AI",
    "Show me 7 scholarly articles",
]

print("Testing journal vs journal article distinction:\n")

for query in test_cases:
    conv = [{'role': 'user', 'content': query}]
    params = extract_search_parameters(client, conv)
    print(f"Query: '{query}'")
    print(f"  → Type: {params['resource_type']}, Limit: {params['limit']}")
    print()
