# app/core/llm_client.py
from typing import Iterable, List, Dict, Optional
import os
from groq import Groq

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

class GroqLLM:
    """Tiny wrapper around Groq Chat Completions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Missing GROQ_API_KEY. Pass with: -e GROQ_API_KEY=sk_your_key"
            )
        self.client = Groq(api_key=self.api_key)
        self.model = model or DEFAULT_MODEL

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = True,
    ) -> Iterable[str] | str:
        """
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        if stream:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        else:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return resp.choices[0].message.content
