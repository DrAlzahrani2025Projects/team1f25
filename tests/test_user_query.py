#!/usr/bin/env python
"""Test the exact user query"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters
from core.services.search_service import perform_library_search

client = GroqClient()
conv = [{'role': 'user', 'content': 'I need 5 journals about machine learning in healthcare'}]

print("User request: 'I need 5 journals about machine learning in healthcare'")
print("\n1. Extracting parameters...")
params = extract_search_parameters(client, conv)
print(f"   Query: {params['query']}")
print(f"   Limit: {params['limit']}")
print(f"   Type: {params['resource_type']}")

print("\n2. Performing search...")
results = perform_library_search(params['query'], params['limit'], params['resource_type'])

if results:
    docs = results.get('docs', [])
    print(f"\n3. Returned {len(docs)} results:")
    
    # Count types
    type_counts = {}
    for i, doc in enumerate(docs, 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
        doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        print(f"   {i}. [{doc_type}] {title[:70]}...")
    
    print(f"\n   Type breakdown:")
    for doc_type, count in sorted(type_counts.items()):
        print(f"     {doc_type}: {count}")
else:
    print("\n❌ No results")

