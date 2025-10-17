# core/qroq_client.py
# Import required modules and types
#
# Try to import Groq client
#     If import fails, raise error with install instructions
#
# Set default model, temperature, and max_tokens from environment variables
#
# Define function _as_messages(content, system)
#     If content is string:
#         Create user message dict
#     Else:
#         Use content as messages list
#     If system message provided:
#         Prepend system message
#     Return messages list
#
# Define class QroqClient:
#     On initialization:
#         Get API key from environment
#         If missing, raise error
#         Create Groq client with API key
#
#     Define chat method:
#         Prepare messages using _as_messages
#         Build payload with model, temperature, max_tokens, stream=False
#         Merge extra parameters if provided
#         Try to call Groq client for chat completion
#             Return assistant message content
#         If error, raise runtime error
#
#     Define chat_stream method:
#         Prepare messages using _as_messages
#         Build payload with model, temperature, max_tokens, stream=True
#         Merge extra parameters if provided
#         Try to call Groq client for streaming chat completion
#             For each chunk in stream:
#                 Extract delta content
#                 If present, yield delta
#         If error, raise runtime error

import os
from typing import Any, Dict, Iterable, List, Optional, Union

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


class QroqClient:
    """
    Thin wrapper around the Groq Python client with sane defaults and
    convenience helpers for non-streaming and streaming chat completions.
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
            or "llama-3.1-8b-instant"
        )
        self.temperature = float(
            temperature if temperature is not None else os.getenv("GROQ_TEMPERATURE", 0.2)
        )
        self.max_tokens = int(
            max_tokens if max_tokens is not None else os.getenv("GROQ_MAX_TOKENS", 1024)
        )

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
            # Groq uses OpenAI-compatible response schema
            return (resp.choices[0].message.content or "").strip()
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
                # OpenAI-compatible delta format
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    yield delta.content
        except Exception as e:
            raise RuntimeError(f"Groq chat_stream() failed: {e}") from e

