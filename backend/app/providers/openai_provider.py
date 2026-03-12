"""OpenAI provider adapter."""
from __future__ import annotations

import logging

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        import openai  # lazy import – not required if unused
        if not settings.OPENAI_API_KEY:
            raise AIProviderError("OPENAI_API_KEY is not set")
        self._client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT,
        )
        self._model = settings.OPENAI_MODEL
        logger.info("OpenAI provider ready  model=%s", self._model)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            raise AIProviderError(f"OpenAI error: {exc}") from exc
