#!/usr/bin/env python
"""Test trigger keyword detection"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock
from core.services.conversation_analyzer import ConversationAnalyzer

# Create mock dependencies
mock_llm = Mock()
mock_prompt = Mock()
analyzer = ConversationAnalyzer(mock_llm, mock_prompt)

test_phrases = [
    ("give me research articles about ADHD", True),
    ("I want thesis about nursing", True),
    ("I need 5 books on history", True),
    ("find me articles", True),
    ("show me journals", True),
    ("get me books", True),
    ("search for articles", True),
    ("I need help", False),  # Should NOT trigger
    ("I want to learn about AI", False),  # Should NOT trigger (no resource type)
    ("articles about AI", False),  # Should NOT trigger
    ("tell me about machine learning", False),  # Should NOT trigger
]

print('Testing trigger keyword detection:\n')
print('=' * 80)

all_pass = True

for phrase, should_trigger in test_phrases:
    # Test using instance method
    triggers = analyzer.should_trigger_search(phrase)
    status = "✓" if triggers == should_trigger else "✗"
    trigger_text = "TRIGGERS" if triggers else "no trigger"
    expected = "expected" if triggers == should_trigger else f"UNEXPECTED (expected {'trigger' if should_trigger else 'no trigger'})"
    
    if triggers != should_trigger:
        all_pass = False
    
    print(f"{status} {phrase:50} → {trigger_text:12} ({expected})")

print('=' * 80)

if all_pass:
    print("\n✓ All tests passed!")
else:
    print("\n✗ Some tests failed")
    sys.exit(1)
