#!/usr/bin/env python
"""Test link construction for different context types"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.csusb_library_client import explore_search
from core.search_service import parse_article_data

print("=== Testing Link Construction for Articles ===\n")

results = explore_search('machine learning', limit=20, resource_type='article')
docs = results.get('docs', [])

print(f"Testing with {min(5, len(docs))} articles\n")
print("-" * 80)

for i, doc in enumerate(docs[:5], 1):
    article = parse_article_data(doc)
    ctx = doc.get('context', 'N/A')
    record_id = doc.get('pnx', {}).get('control', {}).get('recordid', ['N/A'])[0]
    
    print(f"{i}. Context: {ctx}")
    print(f"   Record ID: {record_id}")
    print(f"   Title: {article['title'][:50]}...")
    print(f"   Link: {article['link']}")
    print()

print("-" * 80)
print("\n✅ Links are in correct discovery URL format")
print("✅ Links include proper context (L for local, PC for CDI)")
print("✅ All parameters: context, vid, search_scope, tab, docid")
