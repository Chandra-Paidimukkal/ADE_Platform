"""LandingAI ADE provider adapter."""
from __future__ import annotations

import json
import logging
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class LandingAIProvider(BaseProvider):

    def __init__(self) -> None:
        if not settings.LANDINGAI_API_KEY or not settings.LANDINGAI_ENDPOINT:
            raise AIProviderError("LANDINGAI_API_KEY or LANDINGAI_ENDPOINT not set")

        self._base = settings.LANDINGAI_ENDPOINT.rstrip("/")
        self._extract_endpoint = f"{self._base}/v1/ade/extract"

        self._headers = {
            "Authorization": f"Bearer {settings.LANDINGAI_API_KEY}",
        }

        logger.info("LandingAI provider ready endpoint=%s", self._extract_endpoint)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        raise AIProviderError(
            "LandingAI ADE does not support generic completion. "
            "Use extract_structured_from_markdown()."
        )

    def extract_structured_from_markdown(
        self,
        schema: dict,
        markdown_text: str,
        model: str = "extract-latest",
    ) -> dict:

        try:
            logger.info(
                "LandingAI request schema keys: %s",
                list(schema.get("properties", {}).keys()),
            )

            files = {
                "schema": (None, json.dumps(schema), "application/json"),
                "markdown": ("document.md", markdown_text, "text/markdown"),
                "model": (None, model),
            }

            resp = httpx.post(
                self._extract_endpoint,
                files=files,
                headers=self._headers,
                timeout=settings.AI_REQUEST_TIMEOUT,
            )

            resp.raise_for_status()

            data = resp.json()

            logger.info("LandingAI raw response: %s", data)

            # Normalize common LandingAI response formats
            if "data" in data and isinstance(data["data"], dict):
                return data["data"]

            if "extraction" in data and isinstance(data["extraction"], dict):
                return data["extraction"]

            if "result" in data and isinstance(data["result"], dict):
                return data["result"]

            if isinstance(data, dict):
                return data

            return {"raw_response": data}

        except Exception as exc:
            raise AIProviderError(f"LandingAI error: {exc}") from exc