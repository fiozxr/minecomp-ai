"""LLM interface for OpenAI-compatible APIs (OpenRouter, NVIDIA, etc.).

Usage:
    from minecomp.llm import LLM
    llm = LLM(api_key="...", model="google/gemini-2.0-flash")
    resp = asyncio.run(llm.complete(messages))
"""

import os
from typing import Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError(
        "The 'openai' package is required. Install with: "
        "pip install openai"
    )


class LLM:
    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-2.0-flash",
                 base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MINECOMP_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Pass api_key= or set MINECOMP_API_KEY env var."
            )

        self.base_url = base_url or os.environ.get(
            "MINECOMP_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.model = model

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": "https://minecomp.ai",
                "X-Title": "minecomp-ai",
            },
        )

    async def complete(self, messages, temperature: float = 0.7, max_tokens: int = 2048):
        """Call the LLM and return the assistant's reply text."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def embed(self, text: str):
        """Return an embedding vector for the given text (OpenRouter-only)."""
        response = await self._client.embeddings.create(
            model=self.model, input=text
        )
        return response.data[0].embedding

    async def list_models(self):
        """Fetch available models from the API provider.

        Returns a list of model names (e.g., ['google/gemini-2.0-flash',
        'openai/gpt-4o-mini']). If the API doesn't support this endpoint,
        returns an empty list.
        """
        try:
            response = await self._client.models.list()
            return [m.id for m in response.data]
        except Exception as e:
            print(f"[!] Could not fetch models: {e}")
            return []
