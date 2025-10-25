#!/usr/bin/env python
"""Comprehensive test of all scenarios"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters
from core.services.search_service import perform_library_search

client = GroqClient()

test_queries = [
    ("I need 5 journals about machine learning in healthcare", "Should return journals"),
    ("I need 5 journal articles about machine learning in healthcare", "Should return articles"),
    ("Find 5 books on machine learning in healthcare", "Should return books"),
]

for query, expected in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: '{query}'")
    print(f"Expected: {expected}")
    print('='*80)
    
    conv = [{'role': 'user', 'content': query}]
    params = extract_search_parameters(client, conv)
    
    print(f"\n✓ Extracted: {params['limit']} {params['resource_type']}s")
    
    results = perform_library_search(params['query'], params['limit'], params['resource_type'])
    
    if results:
        docs = results.get('docs', [])
        total = results.get('info', {}).get('total', 0)
        print(f"✓ API returned: {len(docs)} results (out of {total} available)")
        
        # Verify all results match the requested type
        type_counts = {}
        for doc in docs:
            pnx = doc.get("pnx", {})
            display = pnx.get("display", {})
            doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        print(f"✓ Result types: {dict(type_counts)}")
        
        # Check if all match requested type
        requested_type = params['resource_type']
        if all(requested_type in doc_type.lower() for doc_type in type_counts.keys()):
            print(f"✅ SUCCESS: All results are {requested_type}s!")
        else:
            print(f"❌ MISMATCH: Got {list(type_counts.keys())} but requested {requested_type}")
    else:
        print("❌ No results returned")

print("\n" + "="*80)
print("Tests complete!")

