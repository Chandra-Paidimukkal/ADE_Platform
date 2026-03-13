"""Ollama (local LLM) provider adapter."""
from __future__ import annotations

import logging

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    def __init__(self) -> None:
        import ollama  # lazy import
        self._client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self._model  = settings.OLLAMA_MODEL
        logger.info("Ollama provider ready  base=%s model=%s",
                    settings.OLLAMA_BASE_URL, self._model)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = self._client.chat(
                model=self._model,
                messages=messages,
                options={"num_predict": max_tokens},
            )
            return resp["message"]["content"]
        except Exception as exc:
            raise AIProviderError(f"Ollama error: {exc}") from exc
