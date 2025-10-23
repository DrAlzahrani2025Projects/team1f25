import os
import sys
import unittest
from unittest.mock import MagicMock, patch, Mock

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestAsMessages(unittest.TestCase):
    """Test the _as_messages helper function."""

    def test_string_input_creates_user_message(self):
        """Test that string input creates a user message."""
        from core.groq_client import _as_messages
        
        result = _as_messages("Hello world")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(result[0]["content"], "Hello world")

    def test_list_input_preserves_messages(self):
        """Test that list input is preserved as-is."""
        from core.groq_client import _as_messages
        
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second message"}
        ]
        
        result = _as_messages(messages)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result, messages)

    def test_system_message_prepended_to_string(self):
        """Test that system message is prepended when provided with string input."""
        from core.groq_client import _as_messages
        
        result = _as_messages("Hello", system="You are a helpful assistant")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "You are a helpful assistant")
        self.assertEqual(result[1]["role"], "user")
        self.assertEqual(result[1]["content"], "Hello")

    def test_system_message_prepended_to_list(self):
        """Test that system message is prepended when provided with list input."""
        from core.groq_client import _as_messages
        
        messages = [{"role": "user", "content": "Hello"}]
        result = _as_messages(messages, system="Be helpful")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "Be helpful")
        self.assertEqual(result[1]["role"], "user")

    def test_no_system_message_when_none(self):
        """Test that no system message is added when system is None."""
        from core.groq_client import _as_messages
        
        result = _as_messages("Hello", system=None)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")

    def test_empty_string_input(self):
        """Test that empty string creates user message with empty content."""
        from core.groq_client import _as_messages
        
        result = _as_messages("")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(result[0]["content"], "")

    def test_empty_list_input(self):
        """Test that empty list returns empty list."""
        from core.groq_client import _as_messages
        
        result = _as_messages([])
        
        self.assertEqual(len(result), 0)


class TestGroqClientInit(unittest.TestCase):
    """Test GroqClient initialization and configuration."""

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"})
    @patch("groq.Groq")
    def test_init_with_env_api_key(self, mock_groq):
        """Test initialization with API key from environment."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.api_key, "test-api-key")
        mock_groq.assert_called_once_with(api_key="test-api-key")

    @patch.dict(os.environ, {}, clear=True)
    @patch("groq.Groq")
    def test_init_with_explicit_api_key(self, mock_groq):
        """Test initialization with explicit API key."""
        from core.groq_client import GroqClient
        
        client = GroqClient(api_key="explicit-key")
        
        self.assertEqual(client.api_key, "explicit-key")
        mock_groq.assert_called_once_with(api_key="explicit-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        from core.groq_client import GroqClient
        
        with self.assertRaises(ValueError) as context:
            GroqClient()
        
        self.assertIn("GROQ_API_KEY is not set", str(context.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_default_model(self, mock_groq):
        """Test that default model is set correctly."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.model, "llama-3.3-70b-versatile")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "llama-3.1-8b-instant"})
    @patch("groq.Groq")
    def test_init_with_env_model(self, mock_groq):
        """Test initialization with model from environment."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.model, "llama-3.1-8b-instant")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_explicit_model(self, mock_groq):
        """Test initialization with explicit model."""
        from core.groq_client import GroqClient
        
        client = GroqClient(model="mixtral-8x7b-32768")
        
        self.assertEqual(client.model, "mixtral-8x7b-32768")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_default_temperature(self, mock_groq):
        """Test that default temperature is 0.2."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.temperature, 0.2)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_TEMPERATURE": "0.7"})
    @patch("groq.Groq")
    def test_init_with_env_temperature(self, mock_groq):
        """Test initialization with temperature from environment."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.temperature, 0.7)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_explicit_temperature(self, mock_groq):
        """Test initialization with explicit temperature."""
        from core.groq_client import GroqClient
        
        client = GroqClient(temperature=0.9)
        
        self.assertEqual(client.temperature, 0.9)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_TEMPERATURE": "invalid"})
    @patch("groq.Groq")
    def test_init_with_invalid_env_temperature_uses_default(self, mock_groq):
        """Test that invalid environment temperature falls back to default."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.temperature, 0.2)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_default_max_tokens(self, mock_groq):
        """Test that default max_tokens is 1024."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.max_tokens, 1024)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MAX_TOKENS": "2048"})
    @patch("groq.Groq")
    def test_init_with_env_max_tokens(self, mock_groq):
        """Test initialization with max_tokens from environment."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.max_tokens, 2048)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("groq.Groq")
    def test_init_with_explicit_max_tokens(self, mock_groq):
        """Test initialization with explicit max_tokens."""
        from core.groq_client import GroqClient
        
        client = GroqClient(max_tokens=4096)
        
        self.assertEqual(client.max_tokens, 4096)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MAX_TOKENS": "invalid"})
    @patch("groq.Groq")
    def test_init_with_invalid_env_max_tokens_uses_default(self, mock_groq):
        """Test that invalid environment max_tokens falls back to default."""
        from core.groq_client import GroqClient
        
        client = GroqClient()
        
        self.assertEqual(client.max_tokens, 1024)


class TestGroqClientChat(unittest.TestCase):
    """Test GroqClient.chat() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_groq = patch("groq.Groq").start()
        self.mock_client_instance = MagicMock()
        self.mock_groq.return_value = self.mock_client_instance

    def tearDown(self):
        """Clean up patches."""
        patch.stopall()

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_string_input(self):
        """Test chat with simple string input."""
        from core.groq_client import GroqClient
        
        # Mock response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello! How can I help you?"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("What is AI?")
        
        self.assertEqual(result, "Hello! How can I help you?")
        self.mock_client_instance.chat.completions.create.assert_called_once()

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_system_message(self):
        """Test chat with system message."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "I am a helpful assistant."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("Hello", system="You are a helpful assistant")
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_list_messages(self):
        """Test chat with list of messages."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response to conversation"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"}
        ]
        result = client.chat(messages)
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        passed_messages = call_args.kwargs["messages"]
        
        self.assertEqual(len(passed_messages), 2)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_strips_whitespace(self):
        """Test that chat strips leading/trailing whitespace from response."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "  Response with whitespace  \n"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("Test")
        
        self.assertEqual(result, "Response with whitespace")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_no_choices_raises_error(self):
        """Test that chat raises error when response has no choices."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_response.choices = []
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        
        with self.assertRaises(RuntimeError) as context:
            client.chat("Test")
        
        self.assertIn("returned no choices", str(context.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_extra_parameters(self):
        """Test that chat passes extra parameters to API."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("Test", top_p=0.9, frequency_penalty=0.5)
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        
        self.assertEqual(call_args.kwargs["top_p"], 0.9)
        self.assertEqual(call_args.kwargs["frequency_penalty"], 0.5)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_uses_client_defaults(self):
        """Test that chat uses client's default model, temperature, max_tokens."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient(model="test-model", temperature=0.5, max_tokens=2048)
        result = client.chat("Test")
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        
        self.assertEqual(call_args.kwargs["model"], "test-model")
        self.assertEqual(call_args.kwargs["temperature"], 0.5)
        self.assertEqual(call_args.kwargs["max_tokens"], 2048)
        self.assertFalse(call_args.kwargs["stream"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_api_exception_wrapped(self):
        """Test that API exceptions are wrapped in RuntimeError."""
        from core.groq_client import GroqClient
        
        self.mock_client_instance.chat.completions.create.side_effect = Exception("API Error")
        
        client = GroqClient()
        
        with self.assertRaises(RuntimeError) as context:
            client.chat("Test")
        
        self.assertIn("Groq chat() failed", str(context.exception))
        self.assertIn("API Error", str(context.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_empty_content(self):
        """Test chat handles empty content in response."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = ""
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("Test")
        
        self.assertEqual(result, "")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_with_none_content(self):
        """Test chat handles None content in response."""
        from core.groq_client import GroqClient
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        self.mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = GroqClient()
        result = client.chat("Test")
        
        self.assertEqual(result, "")


class TestGroqClientChatStream(unittest.TestCase):
    """Test GroqClient.chat_stream() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_groq = patch("groq.Groq").start()
        self.mock_client_instance = MagicMock()
        self.mock_groq.return_value = self.mock_client_instance

    def tearDown(self):
        """Clean up patches."""
        patch.stopall()

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_yields_deltas(self):
        """Test that chat_stream yields content deltas."""
        from core.groq_client import GroqClient
        
        # Mock streaming response
        chunks = []
        for text in ["Hello", " world", "!"]:
            chunk = MagicMock()
            choice = MagicMock()
            delta = MagicMock()
            delta.content = text
            choice.delta = delta
            chunk.choices = [choice]
            chunks.append(chunk)
        
        self.mock_client_instance.chat.completions.create.return_value = iter(chunks)
        
        client = GroqClient()
        result = list(client.chat_stream("Test"))
        
        self.assertEqual(result, ["Hello", " world", "!"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_with_system_message(self):
        """Test chat_stream with system message."""
        from core.groq_client import GroqClient
        
        chunk = MagicMock()
        choice = MagicMock()
        delta = MagicMock()
        delta.content = "Response"
        choice.delta = delta
        chunk.choices = [choice]
        
        self.mock_client_instance.chat.completions.create.return_value = iter([chunk])
        
        client = GroqClient()
        result = list(client.chat_stream("Test", system="Be helpful"))
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        
        self.assertEqual(messages[0]["role"], "system")
        self.assertTrue(call_args.kwargs["stream"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_uses_client_defaults(self):
        """Test that chat_stream uses client's default settings."""
        from core.groq_client import GroqClient
        
        chunk = MagicMock()
        choice = MagicMock()
        delta = MagicMock()
        delta.content = "Response"
        choice.delta = delta
        chunk.choices = [choice]
        
        self.mock_client_instance.chat.completions.create.return_value = iter([chunk])
        
        client = GroqClient(model="test-model", temperature=0.8, max_tokens=512)
        result = list(client.chat_stream("Test"))
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        
        self.assertEqual(call_args.kwargs["model"], "test-model")
        self.assertEqual(call_args.kwargs["temperature"], 0.8)
        self.assertEqual(call_args.kwargs["max_tokens"], 512)
        self.assertTrue(call_args.kwargs["stream"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_with_extra_parameters(self):
        """Test that chat_stream passes extra parameters."""
        from core.groq_client import GroqClient
        
        chunk = MagicMock()
        choice = MagicMock()
        delta = MagicMock()
        delta.content = "Response"
        choice.delta = delta
        chunk.choices = [choice]
        
        self.mock_client_instance.chat.completions.create.return_value = iter([chunk])
        
        client = GroqClient()
        result = list(client.chat_stream("Test", top_p=0.95))
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        
        self.assertEqual(call_args.kwargs["top_p"], 0.95)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_skips_empty_deltas(self):
        """Test that chat_stream skips chunks with no content."""
        from core.groq_client import GroqClient
        
        chunks = []
        
        # Chunk with content
        chunk1 = MagicMock()
        choice1 = MagicMock()
        delta1 = MagicMock()
        delta1.content = "Hello"
        choice1.delta = delta1
        chunk1.choices = [choice1]
        chunks.append(chunk1)
        
        # Chunk with empty delta content
        chunk2 = MagicMock()
        choice2 = MagicMock()
        delta2 = MagicMock()
        delta2.content = None
        choice2.delta = delta2
        chunk2.choices = [choice2]
        chunks.append(chunk2)
        
        # Chunk with content
        chunk3 = MagicMock()
        choice3 = MagicMock()
        delta3 = MagicMock()
        delta3.content = "World"
        choice3.delta = delta3
        chunk3.choices = [choice3]
        chunks.append(chunk3)
        
        self.mock_client_instance.chat.completions.create.return_value = iter(chunks)
        
        client = GroqClient()
        result = list(client.chat_stream("Test"))
        
        # Should only yield chunks with actual content
        self.assertEqual(result, ["Hello", "World"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_with_no_choices_raises_error(self):
        """Test that chat_stream raises error when chunk has no choices."""
        from core.groq_client import GroqClient
        
        chunk = MagicMock()
        chunk.choices = []
        
        self.mock_client_instance.chat.completions.create.return_value = iter([chunk])
        
        client = GroqClient()
        
        with self.assertRaises(RuntimeError) as context:
            list(client.chat_stream("Test"))
        
        self.assertIn("returned a chunk with no choices", str(context.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_api_exception_wrapped(self):
        """Test that API exceptions during streaming are wrapped."""
        from core.groq_client import GroqClient
        
        self.mock_client_instance.chat.completions.create.side_effect = Exception("Stream Error")
        
        client = GroqClient()
        
        with self.assertRaises(RuntimeError) as context:
            list(client.chat_stream("Test"))
        
        self.assertIn("Groq chat_stream() failed", str(context.exception))
        self.assertIn("Stream Error", str(context.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    def test_chat_stream_with_list_messages(self):
        """Test chat_stream with list of messages."""
        from core.groq_client import GroqClient
        
        chunk = MagicMock()
        choice = MagicMock()
        delta = MagicMock()
        delta.content = "Response"
        choice.delta = delta
        chunk.choices = [choice]
        
        self.mock_client_instance.chat.completions.create.return_value = iter([chunk])
        
        client = GroqClient()
        messages = [{"role": "user", "content": "Hello"}]
        result = list(client.chat_stream(messages))
        
        call_args = self.mock_client_instance.chat.completions.create.call_args
        passed_messages = call_args.kwargs["messages"]
        
        self.assertEqual(len(passed_messages), 1)
        self.assertEqual(passed_messages[0]["role"], "user")


if __name__ == "__main__":
    unittest.main(verbosity=2)
