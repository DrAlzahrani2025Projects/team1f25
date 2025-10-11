# app/core/llm_client.py
from __future__ import annotations
import os
from typing import Iterable, List, Dict, Optional, Union
from groq import Groq

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "30"))

class GroqLLM:
    def __init__(self, model: Optional[str] = None):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set")
        self.client = Groq(api_key=key, timeout=TIMEOUT)
        self.model = model or DEFAULT_MODEL

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = 700,
        stream: bool = False,
    ) -> Union[str, Iterable[str]]:
        if temperature is None:
            try:
                temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
            except Exception:
                temperature = 0.2

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        if stream:
            def gen():
                for chunk in resp:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
            return gen()
        else:
            return resp.choices[0].message.content or ""
