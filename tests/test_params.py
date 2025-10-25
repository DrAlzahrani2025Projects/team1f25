#!/usr/bin/env python
"""Test search parameter extraction"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters

# Initialize client
client = GroqClient()

# Test cases
test_conversations = [
    [{"role": "user", "content": "I need 5 articles about machine learning in healthcare"}],
    [{"role": "user", "content": "Find 10 books on climate change"}],
    [{"role": "user", "content": "Show me research on diabetes"}],
]

print("Testing parameter extraction:\n")

for i, conv in enumerate(test_conversations, 1):
    print(f"Test {i}: {conv[0]['content']}")
    params = extract_search_parameters(client, conv)
    print(f"  Query: {params.get('query')}")
    print(f"  Limit: {params.get('limit')}")
    print(f"  Type: {params.get('resource_type')}")
    print()

