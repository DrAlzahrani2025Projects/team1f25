#!/usr/bin/env python
"""Test the updated conversation flow"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.clients.groq_client import GroqClient
from core.ai_assistant import generate_follow_up_question

client = GroqClient()

print("=== Testing Updated Conversation Flow ===\n")

# Test Case 1: User provides broad topic, then specific aspect
print("Test 1: Broad topic → Specific aspect → Resource type")
print("-" * 60)

conv1 = [
    {"role": "user", "content": "I want to research about machine learning"}
]
print(f"User: {conv1[0]['content']}")
response1 = generate_follow_up_question(client, conv1)
print(f"Bot: {response1}")

if "READY_TO_SEARCH" not in response1:
    conv1.append({"role": "assistant", "content": response1})
    conv1.append({"role": "user", "content": "I am looking for algorithms"})
    print(f"\nUser: I am looking for algorithms")
    response2 = generate_follow_up_question(client, conv1)
    print(f"Bot: {response2}")
    
    if "READY_TO_SEARCH" not in response2:
        conv1.append({"role": "assistant", "content": response2})
        conv1.append({"role": "user", "content": "articles please"})
        print(f"\nUser: articles please")
        response3 = generate_follow_up_question(client, conv1)
        print(f"Bot: {response3}")
        print(f"\n✓ Expected READY_TO_SEARCH: {'YES' if 'READY_TO_SEARCH' in response3 else 'NO'}")
    else:
        print("\n❌ Bot triggered search too early (after only specific aspect)")
else:
    print("\n❌ Bot triggered search too early (after only broad topic)")

print("\n" + "=" * 60)

# Test Case 2: User provides complete info upfront
print("\nTest 2: Complete information provided upfront")
print("-" * 60)

conv2 = [
    {"role": "user", "content": "I need 5 articles about machine learning algorithms"}
]
print(f"User: {conv2[0]['content']}")
response = generate_follow_up_question(client, conv2)
print(f"Bot: {response}")
print(f"\n✓ Expected READY_TO_SEARCH: {'YES' if 'READY_TO_SEARCH' in response else 'NO'}")

print("\n" + "=" * 60)

# Test Case 3: User says "any type" for resources
print("\nTest 3: User accepts any resource type")
print("-" * 60)

conv3 = [
    {"role": "user", "content": "I'm researching neural networks"}
]
print(f"User: {conv3[0]['content']}")
response1 = generate_follow_up_question(client, conv3)
print(f"Bot: {response1}")

if "READY_TO_SEARCH" not in response1:
    conv3.append({"role": "assistant", "content": response1})
    conv3.append({"role": "user", "content": "any type is fine"})
    print(f"\nUser: any type is fine")
    response2 = generate_follow_up_question(client, conv3)
    print(f"Bot: {response2}")
    print(f"\n✓ Expected READY_TO_SEARCH: {'YES' if 'READY_TO_SEARCH' in response2 else 'NO'}")

print("\n" + "=" * 60)
print("\n✅ Conversation flow test complete!")

