#!/usr/bin/env python
"""Simulate the complete conversation flow with OTT churn"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import extract_search_parameters
from core.services.search_service import perform_library_search

def suggest_alternative_search(groq_client: GroqClient, original_query: str) -> str:
    """Use AI to suggest alternative search terms when no results found."""
    prompt = f"""The user searched for "{original_query}" in an academic library database but got 0 results.

Suggest 2-3 alternative, broader search terms that might work better. Keep suggestions short and relevant.

Format your response as a simple list:
- suggestion 1
- suggestion 2
- suggestion 3

Example:
If user searched: "ott churn causes"
Suggest:
- customer churn
- subscriber retention
- streaming service analytics"""

    try:
        suggestions = groq_client.chat(prompt)
        return suggestions.strip()
    except Exception as e:
        return "- Try using broader search terms\n- Check spelling and try synonyms"

# Simulate the conversation
client = GroqClient()

conversation = [
    {"role": "assistant", "content": "Hello! I'm your Scholar AI Assistant..."},
    {"role": "user", "content": "Ott churn"},
    {"role": "assistant", "content": "Ott churn is a specific topic. Are you looking to explore the causes of churn..."},
    {"role": "user", "content": "causes of churn"},
]

print("="*80)
print("SIMULATING THE CONVERSATION FLOW")
print("="*80)
print("\nUser's conversation:")
for msg in conversation:
    if msg["role"] == "user":
        print(f"  User: {msg['content']}")

print("\n" + "-"*80)
print("STEP 1: Extract search parameters")
print("-"*80)

params = extract_search_parameters(client, conversation)
print(f"Query: {params['query']}")
print(f"Limit: {params['limit']}")
print(f"Type: {params['resource_type']}")

print("\n" + "-"*80)
print("STEP 2: Perform search")
print("-"*80)

results = perform_library_search(params['query'], params['limit'], params['resource_type'])

if results is None:
    print("❌ ERROR: API failure")
elif len(results.get("docs", [])) == 0:
    print(f"⚠️  NO RESULTS for '{params['query']}'")
    print(f"Total in database: {results.get('info', {}).get('total', 0)}")
    
    print("\n" + "-"*80)
    print("STEP 3: Generate alternative suggestions")
    print("-"*80)
    
    suggestions = suggest_alternative_search(client, params['query'])
    print(suggestions)
    
    print("\n" + "-"*80)
    print("FINAL MESSAGE TO USER:")
    print("-"*80)
    msg = f"I searched the library but couldn't find any results for '{params['query']}'.\n\n"
    msg += "Try these alternative searches:\n" + suggestions
    print(msg)
else:
    print(f"✅ SUCCESS: Found {len(results.get('docs', []))} results")

print("\n" + "="*80)

