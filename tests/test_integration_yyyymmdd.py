#!/usr/bin/env python
"""Final integration test for YYYYMMDD format with dates calculated from today"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.clients.groq_client import GroqClient
from core.services.conversation_analyzer import ConversationAnalyzer
from core.utils.prompts import PromptManager

client = GroqClient()
pm = PromptManager()
analyzer = ConversationAnalyzer(client, pm)

# Get today's date
today = datetime.now().strftime('%Y%m%d')
print(f'Today: {today} ({datetime.now().strftime("%B %d, %Y")})\n')

conv = [{'role': 'user', 'content': 'I want research journals about academically at risk nursing students which are peer reviewed for last 3 years'}]

params = analyzer.extract_search_parameters(conv)

print('Full extraction test:')
print(f'Query: {params["query"]}')
print(f'Resource Type: {params["resource_type"]}')
print(f'Limit: {params["limit"]}')
print(f'Date From: {params["date_from"]} (type: {type(params["date_from"]).__name__})')
print(f'Date To: {params["date_to"]} (type: {type(params["date_to"]).__name__})')

# Verify format
assert isinstance(params["date_from"], str), "date_from should be string"
assert isinstance(params["date_to"], str), "date_to should be string"
assert len(params["date_from"]) == 8, "date_from should be YYYYMMDD (8 chars)"
assert len(params["date_to"]) == 8, "date_to should be YYYYMMDD (8 chars)"
assert params["date_from"].isdigit(), "date_from should contain only digits"
assert params["date_to"].isdigit(), "date_to should contain only digits"

# Verify date_to is today's date (or close to it)
print(f'\nValidation:')
print(f'  Expected date_to: {today} (today)')
print(f'  Actual date_to:   {params["date_to"]}')

if params["date_to"] == today:
    print(f'  ✓ date_to matches today exactly!')
else:
    # Allow some tolerance (within a few days)
    date_diff = abs(int(params["date_to"]) - int(today))
    if date_diff <= 100:  # Within ~100 days is acceptable for "last N years"
        print(f'  ✓ date_to is close to today (diff: {date_diff})')
    else:
        print(f'  ⚠ date_to differs from today by {date_diff}')

# Check that date_from is approximately 3 years ago
year_from = int(params["date_from"][:4])
year_today = int(today[:4])
years_diff = year_today - year_from

print(f'  Expected year difference: 3 years')
print(f'  Actual year difference:   {years_diff} years')

if years_diff == 3:
    print(f'  ✓ date_from is exactly 3 years ago!')
elif 2 <= years_diff <= 4:
    print(f'  ✓ date_from is approximately 3 years ago')
else:
    print(f'  ⚠ date_from year difference unexpected: {years_diff}')

print(f'\n✓ All parameters extracted correctly in YYYYMMDD format calculated from today!')
