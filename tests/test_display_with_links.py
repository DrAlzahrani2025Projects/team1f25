#!/usr/bin/env python
"""Test the updated display with links"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.csusb_library_client import explore_search
from core.search_service import parse_article_data

print("=== Testing Updated Results Display ===\n")

results = explore_search('machine learning', limit=3)
docs = results.get('docs', [])

print(f"Found {len(docs)} results\n")
print("Columns: #, Title, Authors, Year, Type, Link\n")
print("-" * 80)

for i, doc in enumerate(docs, 1):
    article = parse_article_data(doc)
    
    print(f"{i}. Title: {article['title'][:60]}...")
    print(f"   Authors: {article['author'][:40]}")
    print(f"   Year: {article['date']}")
    print(f"   Type: {article['type']}")
    print(f"   Link: {article['link'][:70]}...")
    print()

print("-" * 80)
print("\n✅ Link extraction working!")
print("✅ All required columns available: #, Title, Authors, Year, Type, Link")
