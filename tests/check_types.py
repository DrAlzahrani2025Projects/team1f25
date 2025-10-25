#!/usr/bin/env python
"""Check what resource types are in the results"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.csusb_library_client import explore_search

results = explore_search("machine learning healthcare", limit=20)
docs = results.get("docs", [])

print(f"Found {len(docs)} documents. Resource types:")
type_counts = {}

for doc in docs:
    pnx = doc.get("pnx", {})
    display = pnx.get("display", {})
    doc_type = display.get("type", ["Unknown"])[0] if display.get("type") else "Unknown"
    
    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {doc_type}: {count}")

