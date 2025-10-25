#!/usr/bin/env python
"""Test API-level filtering"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.csusb_library_client import explore_search

print("Test 1: Search for articles")
results = explore_search("machine learning healthcare", limit=5, resource_type="article")
docs = results.get("docs", [])
print(f"  Returned: {len(docs)} results")
for i, doc in enumerate(docs, 1):
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
    doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
    print(f"  {i}. [{doc_type}] {title[:60]}...")

print("\nTest 2: Search for books")
results = explore_search("machine learning healthcare", limit=5, resource_type="book")
docs = results.get("docs", [])
print(f"  Returned: {len(docs)} results")
for i, doc in enumerate(docs, 1):
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
    doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
    print(f"  {i}. [{doc_type}] {title[:60]}...")

print("\nTest 3: No filter")
results = explore_search("machine learning healthcare", limit=5)
docs = results.get("docs", [])
print(f"  Returned: {len(docs)} results")
for i, doc in enumerate(docs, 1):
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    title = display.get("title", ["No title"])[0] if display.get("title") else "No title"
    doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
    print(f"  {i}. [{doc_type}] {title[:60]}...")
