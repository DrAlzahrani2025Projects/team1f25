#!/usr/bin/env python
"""Test the strictly scholarly assistant behavior"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.groq_client import GroqClient
from core.ai_assistant import generate_follow_up_question

client = GroqClient()

print("=== Testing Strict Scholarly Assistant ===\n")

test_cases = [
    {
        "name": "Academic Query (ACCEPT)",
        "messages": [{"role": "user", "content": "I want to research machine learning"}],
        "expected": "Should ask for specific aspect"
    },
    {
        "name": "Off-topic: Weather (REJECT)",
        "messages": [{"role": "user", "content": "What's the weather today?"}],
        "expected": "Should redirect to research"
    },
    {
        "name": "Off-topic: Joke (REJECT)",
        "messages": [{"role": "user", "content": "Tell me a joke"}],
        "expected": "Should redirect to research"
    },
    {
        "name": "Off-topic: Casual Chat (REJECT)",
        "messages": [{"role": "user", "content": "How are you doing?"}],
        "expected": "Should redirect to research"
    },
    {
        "name": "Academic Query: Complete (ACCEPT)",
        "messages": [{"role": "user", "content": "I need 5 articles about climate change"}],
        "expected": "Should trigger READY_TO_SEARCH"
    }
]

print("-" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['name']}")
    print(f"User: {test['messages'][0]['content']}")
    print(f"Expected: {test['expected']}")
    
    response = generate_follow_up_question(client, test['messages'])
    print(f"Bot: {response}")
    
    # Check if redirect message appears for off-topic
    is_redirect = "scholarly research assistant" in response.lower() and "designed to help" in response.lower()
    is_ready = "READY_TO_SEARCH" in response
    
    if "REJECT" in test['name']:
        if is_redirect:
            print("✅ PASS - Correctly redirected off-topic query")
        else:
            print("❌ FAIL - Should have redirected to research")
    elif "Complete" in test['name']:
        if is_ready:
            print("✅ PASS - Correctly triggered search")
        else:
            print("❌ FAIL - Should have triggered search")
    else:
        if not is_redirect and not is_ready:
            print("✅ PASS - Correctly asked follow-up")
        else:
            print("⚠️ CHECK - Review response")
    
    print("-" * 80)

print("\n✅ Strict scholarly assistant test complete!")
