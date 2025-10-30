#!/usr/bin/env python
"""Test AI suggestions for no-results queries"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
# Function to get AI suggestions
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
#end of prompt
    try:
        suggestions = groq_client.chat(prompt)
        return suggestions.strip()
    except Exception as e:
        return "- Try using broader search terms\n- Check spelling and try synonyms"

client = GroqClient()
# Define test queries
test_queries = [
    "ott churn causes",
    "quantum entanglement teleportation",
    "machine learning healthcare xyz123",
]

print("Testing AI-generated search suggestions:\n")
# Run tests
for query in test_queries:
    print(f"Original query: '{query}'")
    print("Suggestions:")
    suggestions = suggest_alternative_search(client, query)
    print(suggestions)
    print("\n" + "="*80 + "\n")

