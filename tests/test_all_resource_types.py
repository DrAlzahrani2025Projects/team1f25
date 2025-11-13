#!/usr/bin/env python
"""Test extraction of all resource types"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters

client = GroqClient()

test_cases = [
    # Articles
    ("I need 5 articles about machine learning", "article"),
    ("Find peer reviewed articles on AI", "article"),
    ("I want journal articles about robotics", "article"),
    
    # Journals
    ("I need 5 journals about machine learning", "journal"),
    ("Find peer reviewed journals on nursing", "journal"),
    ("I want research journals about education", "journal"),
    
    # Thesis/Dissertations
    ("I want thesis about nursing students", "thesis"),
    ("Find dissertations on machine learning", "thesis"),
    ("Show me doctoral dissertations about AI", "thesis"),
    ("I need theses on climate change", "thesis"),
    
    # Books
    ("Find 10 books on climate change", "book"),
    ("I need ebooks about AI", "book"),
    
    # With dates
    ("I want thesis about academically at risk nursing students which are peer reviewed for last 3 years", "thesis"),
    ("I want research journals about nursing which are peer reviewed for last 3 years", "journal"),
]

print("Testing all resource type extractions:\n")
print("=" * 80)

for query, expected_type in test_cases:
    conv = [{'role': 'user', 'content': query}]
    params = extract_search_parameters(client, conv)
    actual_type = params['resource_type']
    status = "✓" if actual_type == expected_type else "✗"
    
    print(f"{status} Query: '{query}'")
    print(f"  Expected: {expected_type}, Got: {actual_type}")
    if actual_type != expected_type:
        print(f"  ⚠️  MISMATCH!")
    print()

print("=" * 80)
