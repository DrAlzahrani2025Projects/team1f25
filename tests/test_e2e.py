#!/usr/bin/env python
"""Test complete end-to-end flow"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters
from core.search_service import perform_library_search

client = GroqClient()
conv = [{'role': 'user', 'content': 'I need 5 articles about machine learning in healthcare'}]

print("User request: 'I need 5 articles about machine learning in healthcare'")
print("\n1. Extracting parameters...")
params = extract_search_parameters(client, conv)
print(f"   Query: {params['query']}")
print(f"   Limit: {params['limit']}")
print(f"   Type: {params['resource_type']}")

print("\n2. Performing search...")
results = perform_library_search(params['query'], params['limit'], params['resource_type'])

if results:
    docs = results.get('docs', [])
    print(f"\n3. ✅ SUCCESS! Returned {len(docs)} {params['resource_type']}s:")
    for i, doc in enumerate(docs, 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
        doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
        print(f"   {i}. [{doc_type}] {title[:70]}...")
else:
    print("\n❌ No results")
