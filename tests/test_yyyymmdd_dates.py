#!/usr/bin/env python
"""Test that LLM returns dates in YYYYMMDD format calculated from today"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters

client = GroqClient()

# Get today's date
today = datetime.now()
today_str = today.strftime('%Y%m%d')
print(f"Testing with today's date: {today_str} ({today.strftime('%B %d, %Y')})\n")

test_cases = [
    ("I want journals about nursing from last 3 years", "journal", 3, "last 3 years"),
    ("Find articles about AI from last 5 years", "article", 5, "last 5 years"),
    ("I want thesis about climate change from last 2 years", "thesis", 2, "last 2 years"),
    ("Show me books on history from last 10 years", "book", 10, "last 10 years"),
]

print("Testing LLM returns dates in YYYYMMDD format from today:\n")
print("=" * 80)

all_pass = True

for query, expected_type, years_back, time_phrase in test_cases:
    conv = [{'role': 'user', 'content': query}]
    params = extract_search_parameters(client, conv)
    
    resource_type = params.get('resource_type')
    date_from = params.get('date_from')
    date_to = params.get('date_to')
    
    print(f"\nQuery: '{query}'")
    print(f"Time phrase: '{time_phrase}'")
    print(f"Expected: type={expected_type}, {years_back} years back from today")
    print(f"Got:      type={resource_type}, from={date_from}, to={date_to}")
    
    # Check resource type
    if resource_type != expected_type:
        print(f"  ✗ Resource type mismatch!")
        all_pass = False
    else:
        print(f"  ✓ Resource type correct")
    
    # Check date_to is today (or very close)
    if date_to == today_str:
        print(f"  ✓ Date to matches today exactly: {date_to}")
    elif date_to and abs(int(date_to) - int(today_str)) <= 100:
        print(f"  ✓ Date to is close to today: {date_to} (diff: {abs(int(date_to) - int(today_str))})")
    else:
        print(f"  ✗ Date to doesn't match today: expected {today_str}, got {date_to}")
        all_pass = False
    
    # Check date_from is approximately N years ago
    if date_from:
        year_from = int(date_from[:4])
        year_today = int(today_str[:4])
        years_diff = year_today - year_from
        
        if years_diff == years_back:
            print(f"  ✓ Date from is exactly {years_back} years ago: {date_from}")
        elif abs(years_diff - years_back) <= 1:
            print(f"  ✓ Date from is approximately {years_back} years ago: {date_from} ({years_diff} years)")
        else:
            print(f"  ✗ Date from year mismatch: expected ~{years_back} years, got {years_diff} years")
            all_pass = False
        
        # Check format is string
        if isinstance(date_from, str) and len(date_from) == 8:
            print(f"  ✓ Date from is string in YYYYMMDD format")
        else:
            print(f"  ✗ Date from is not YYYYMMDD string: {type(date_from)} {date_from}")
            all_pass = False
    
    if date_to:
        if isinstance(date_to, str) and len(date_to) == 8:
            print(f"  ✓ Date to is string in YYYYMMDD format")
        else:
            print(f"  ✗ Date to is not YYYYMMDD string: {type(date_to)} {date_to}")
            all_pass = False
    
    print("-" * 80)

print("\n" + "=" * 80)
if all_pass:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed")
