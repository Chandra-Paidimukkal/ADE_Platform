"""Anthropic (Claude) provider adapter."""
from __future__ import annotations

import logging

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    def __init__(self) -> None:
        import anthropic  # lazy import
        if not settings.ANTHROPIC_API_KEY:
            raise AIProviderError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT,
        )
        self._model = settings.ANTHROPIC_MODEL
        logger.info("Anthropic provider ready  model=%s", self._model)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        try:
            kwargs: dict = dict(
                model=self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            if system:
                kwargs["system"] = system
            resp = self._client.messages.create(**kwargs)
            return resp.content[0].text
        except Exception as exc:
            raise AIProviderError(f"Anthropic error: {exc}") from exc
