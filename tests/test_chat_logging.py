#!/usr/bin/env python
"""Test that chat handler logging works correctly"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from unittest.mock import Mock, patch, MagicMock
from core.clients.groq_client import GroqClient
from ui.chat_handler import ChatOrchestrator

# Set up logging to capture log messages
logging.basicConfig(level=logging.INFO, format='%(name)s | %(levelname)s | %(message)s')

def test_trigger_keyword_logging():
    """Test that trigger keywords are logged"""
    print("\n=== Testing Trigger Keyword Logging ===\n")
    
    # Mock dependencies
    mock_llm = Mock(spec=GroqClient)
    mock_llm.chat.return_value = '{"query": "ADHD", "limit": 10, "resource_type": "article", "date_from": "20221110", "date_to": "20251110"}'
    
    orchestrator = ChatOrchestrator(mock_llm)
    
    # Test trigger detection
    test_messages = [
        "give me research articles about ADHD",
        "I want thesis about nursing",
        "find me books on history",
    ]
    
    for msg in test_messages:
        print(f"Testing: '{msg}'")
        result = orchestrator.analyzer.should_trigger_search(msg)
        print(f"  → Triggers: {result}\n")

def test_conversation_response_logging():
    """Test that AI responses are logged"""
    print("\n=== Testing AI Response Logging ===\n")
    
    # Mock dependencies
    mock_llm = Mock(spec=GroqClient)
    mock_llm.chat.return_value = "What specific aspect of machine learning are you interested in?"
    
    orchestrator = ChatOrchestrator(mock_llm)
    
    conversation = [
        {"role": "user", "content": "I want to learn about machine learning"}
    ]
    
    print("Getting conversation response...")
    response = orchestrator.get_conversation_response(conversation)
    print(f"AI Response: {response}\n")

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Chat Handler Logging")
    print("=" * 80)
    
    test_trigger_keyword_logging()
    test_conversation_response_logging()
    
    print("=" * 80)
    print("✓ Logging tests completed - check logs above")
    print("=" * 80)
