# core/clients/groq_client.py
import os
from typing import Any, Dict, Iterable, List, Optional, Union
from core.interfaces import ILLMClient
from core.utils.logging_utils import get_logger

logger = get_logger(__name__)

def _as_messages(
    content: Union[str, List[Dict[str, str]]],
    system: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Normalize input into OpenAI/Groq chat 'messages' format.
    """
    if isinstance(content, str):
        messages: List[Dict[str, str]] = [{"role": "user", "content": content}]
    else:
        messages = list(content)

    if system:
        messages = [{"role": "system", "content": system}] + messages
    return messages


class GroqClient(ILLMClient):
    """
    Thin wrapper around the Groq Python client with sane defaults and
    convenience helpers for non-streaming and streaming chat completions.
    Implements ILLMClient interface for dependency inversion.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        try:
            # Groq's official client; install with:  pip install groq
            from groq import Groq  # type: ignore
        except Exception as e:
            raise ImportError(
                "The 'groq' package is not installed. Install it with:\n\n"
                "    pip install groq\n"
            ) from e

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Provide it in the environment or pass api_key=..."
            )

        # Defaults can be overridden via env or constructor
        self.model = (
            model
            or os.getenv("GROQ_MODEL")
            or "llama-3.3-70b-versatile"
        )
        # Safely coerce environment variables for temperature and max_tokens
        temp_env = os.getenv("GROQ_TEMPERATURE")
        if temperature is not None:
            self.temperature = float(temperature)
        elif temp_env is not None:
            try:
                self.temperature = float(temp_env)
            except (ValueError, TypeError):
                self.temperature = 0.2
        else:
            self.temperature = 0.2
        tokens_env = os.getenv("GROQ_MAX_TOKENS")
        if max_tokens is not None:
            self.max_tokens = int(max_tokens)
        elif tokens_env is not None:
            try:
                self.max_tokens = int(tokens_env)
            except (ValueError, TypeError):
                self.max_tokens = 1024
        else:
            self.max_tokens = 1024

        self._client = Groq(api_key=self.api_key)

    def chat(
        self,
        content: Union[str, List[Dict[str, str]]],
        system: Optional[str] = None,
        **extra: Any,
    ) -> str:
        """
        Non-streaming chat completion. Returns assistant message text.
        """
        messages = _as_messages(content, system)
        payload: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )
        if extra:
            payload.update(extra)

        try:
            resp = self._client.chat.completions.create(**payload)
            
            # Log token usage
            usage = getattr(resp, "usage", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)
                logger.info(
                    f"Token usage - Model: {self.model}, "
                    f"Prompt: {prompt_tokens}, "
                    f"Completion: {completion_tokens}, "
                    f"Total: {total_tokens}"
                )
            
            choices = getattr(resp, "choices", None) or []
            if not choices:
                raise RuntimeError(
                    "Groq chat() returned no choices — the response may have been blocked by safety filters."
                )
            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            content_text = getattr(message, "content", "") if message else ""
            return (content_text or "").strip()
        except Exception as e:
            raise RuntimeError(f"Groq chat() failed: {e}") from e

    def chat_stream(
        self,
        content: Union[str, List[Dict[str, str]]],
        system: Optional[str] = None,
        **extra: Any,
    ) -> Iterable[str]:
        """
        Streaming chat completion. Yields text deltas as they arrive.
        """
        messages = _as_messages(content, system)
        payload: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        if extra:
            payload.update(extra)

        try:
            stream = self._client.chat.completions.create(**payload)
            for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    raise RuntimeError(
                        "Groq chat_stream() returned a chunk with no choices — the stream may have been filtered or is malformed."
                    )
                delta = getattr(choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    yield delta.content
                
                # Log token usage from the final chunk (if available)
                usage = getattr(chunk, "usage", None)
                if usage:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0)
                    completion_tokens = getattr(usage, "completion_tokens", 0)
                    total_tokens = getattr(usage, "total_tokens", 0)
                    logger.info(
                        f"Token usage (streaming) - Model: {self.model}, "
                        f"Prompt: {prompt_tokens}, "
                        f"Completion: {completion_tokens}, "
                        f"Total: {total_tokens}"
                    )
        except Exception as e:
            raise RuntimeError(f"Groq chat_stream() failed: {e}") from e