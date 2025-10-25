#!/usr/bin/env python
"""Test journal search and check available facets"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.csusb_library_client import explore_search

print("Test 1: Search with 'journals' facet")
results = explore_search("machine learning healthcare", limit=10, resource_type="journal")
docs = results.get("docs", [])
print(f"  Returned: {len(docs)} results")

# Check what types came back
type_counts = {}
for doc in docs:
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

print("\n  Types returned:")
for doc_type, count in sorted(type_counts.items()):
    print(f"    {doc_type}: {count}")

# Check facets in response
print("\n  Available facets:")
facets = results.get("facets", [])
for facet in facets:
    if facet.get("name") == "rtype":
        print(f"    Resource type facet values:")
        for value in facet.get("values", [])[:10]:
            print(f"      - {value.get('value')}: {value.get('count')}")
