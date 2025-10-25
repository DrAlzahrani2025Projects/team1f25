#!/usr/bin/env python
"""Test search with filtering"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services.search_service import perform_library_search

print("Test 1: 5 articles about machine learning healthcare")
results = perform_library_search("machine learning healthcare", limit=5, resource_type="article")
if results:
    docs = results.get("docs", [])
    print(f"  Returned: {len(docs)} results")
    for i, doc in enumerate(docs, 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0]
        doc_type = display.get("type", ["Unknown"])[0]
        print(f"  {i}. [{doc_type}] {title[:60]}...")
else:
    print("  No results")

print("\nTest 2: 5 books about machine learning healthcare")
results = perform_library_search("machine learning healthcare", limit=5, resource_type="book")
if results:
    docs = results.get("docs", [])
    print(f"  Returned: {len(docs)} results")
    for i, doc in enumerate(docs, 1):
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        title = display.get("title", ["No title"])[0]
        doc_type = display.get("type", ["Unknown"])[0]
        print(f"  {i}. [{doc_type}] {title[:60]}...")
else:
    print("  No results")

