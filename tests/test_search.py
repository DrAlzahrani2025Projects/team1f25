#!/usr/bin/env python
"""Quick test script for library search"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.csusb_library_client import explore_search

# Test the search
query = "machine learning healthcare"
print(f"Testing search with query: {query}")

results = explore_search(query, limit=5)

total = results.get("info", {}).get("total", 0)
docs_count = len(results.get("docs", []))

print(f"\nTotal results available: {total}")
print(f"Docs returned: {docs_count}")

if docs_count > 0:
    print("\n✅ SUCCESS! Found results:")
    for i, doc in enumerate(results.get("docs", [])[:3], 1):
        title = doc.get("pnx", {}).get("display", {}).get("title", ["No title"])[0]
        print(f"  {i}. {title[:80]}...")
else:
    print("\n❌ No results found")
    print(f"Response keys: {results.keys()}")
