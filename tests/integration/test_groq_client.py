"""
Integration tests for Groq LLM Client.
Tests actual API communication (requires GROQ_API_KEY).
"""
import pytest
import os
from core.clients.groq_client import GroqClient


class TestGroqClientIntegration:
    """Integration tests for Groq LLM API."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")
        
        self.client = GroqClient()
    
    @pytest.mark.integration
    def test_chat_basic_query(self):
        """Test basic chat completion."""
        response = self.client.chat("Say 'test' and nothing else")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.integration
    def test_chat_with_system_prompt(self):
        """Test chat with system prompt."""
        response = self.client.chat(
            "What is 2+2?",
            system="You are a math tutor. Answer briefly."
        )
        
        assert response is not None
        assert "4" in response
    
    @pytest.mark.integration
    def test_chat_with_conversation_history(self):
        """Test chat with conversation history."""
        messages = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Hello Alice!"},
            {"role": "user", "content": "What's my name?"}
        ]
        
        response = self.client.chat(messages)
        
        assert response is not None
        assert "Alice" in response or "alice" in response.lower()
    
    @pytest.mark.integration
    def test_chat_stream_basic(self):
        """Test streaming chat completion."""
        chunks = list(self.client.chat_stream("Count to 3 briefly"))
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        
        # Join chunks to form complete response
        full_response = "".join(chunks)
        assert len(full_response) > 0
    
    @pytest.mark.integration
    def test_chat_json_response(self):
        """Test chat with JSON response format."""
        prompt = 'Return this JSON: {"status": "ok", "value": 42}'
        response = self.client.chat(prompt)
        
        assert response is not None
        # Should contain JSON-like structure
        assert "{" in response or "ok" in response
    
    @pytest.mark.integration
    def test_client_initialization_with_params(self):
        """Test client initialization with custom parameters."""
        client = GroqClient(
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=100
        )
        
        assert client.model == "llama-3.3-70b-versatile"
        assert client.temperature == 0.5
        assert client.max_tokens == 100
    
    @pytest.mark.integration
    def test_error_handling_empty_content(self):
        """Test error handling with problematic input."""
        with pytest.raises(Exception):
            # Empty content should raise an error
            self.client.chat("")
