#!/usr/bin/env python
"""Test the OTT churn query that returned no results"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services.search_service import perform_library_search

print("Test 1: Original query that failed")
results = perform_library_search("ott churn causes", limit=10, resource_type=None)

if results is None:
    print("  ❌ Search error (API failure)")
elif len(results.get("docs", [])) == 0:
    print(f"  ⚠️  No results found")
    print(f"  Total available in database: {results.get('info', {}).get('total', 0)}")
else:
    print(f"  ✅ Found {len(results.get('docs', []))} results")

print("\nTest 2: Try broader search - just 'churn'")
results2 = perform_library_search("churn", limit=10, resource_type=None)

if results2 and len(results2.get("docs", [])) > 0:
    print(f"  ✅ Found {len(results2.get('docs', []))} results")
    print("  First 3 results:")
    for i, doc in enumerate(results2.get("docs", [])[:3], 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
        print(f"    {i}. {title[:80]}...")
else:
    print("  ⚠️  Still no results")

print("\nTest 3: Try 'customer retention'")
results3 = perform_library_search("customer retention", limit=10, resource_type=None)

if results3 and len(results3.get("docs", [])) > 0:
    print(f"  ✅ Found {len(results3.get('docs', []))} results")
    print("  First 3 results:")
    for i, doc in enumerate(results3.get("docs", [])[:3], 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
        print(f"    {i}. {title[:80]}...")
else:
    print("  ⚠️  Still no results")

