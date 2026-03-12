"""Google Gemini provider adapter."""
from __future__ import annotations

import logging

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    def __init__(self) -> None:
        import google.generativeai as genai  # lazy import
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("GEMINI_API_KEY is not set")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("Gemini provider ready  model=%s", settings.GEMINI_MODEL)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        try:
            full = f"{system}\n\n{prompt}" if system else prompt
            resp = self._model.generate_content(
                full,
                generation_config={"max_output_tokens": max_tokens},
            )
            return resp.text
        except Exception as exc:
            raise AIProviderError(f"Gemini error: {exc}") from exc
