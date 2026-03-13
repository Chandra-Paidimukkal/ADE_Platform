"""
Universal LLM Router.
Routes extraction/generation calls to the configured AI provider.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import settings
from backend.app.core.enums import AIProvider
from backend.app.core.exceptions import AIProviderError

logger = logging.getLogger(__name__)


class LLMRouter:

    def __init__(self, provider_name: str | None = None) -> None:
        name = (provider_name or settings.AI_PROVIDER).lower()
        try:
            self._provider_enum = AIProvider(name)
        except ValueError:
            self._provider_enum = AIProvider.none

        self._adapter = self._build_adapter()

    @property
    def available(self) -> bool:
        return self._adapter is not None

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        if self._adapter is None:
            raise AIProviderError("No AI provider configured")

        return self._adapter.complete(prompt, system=system, max_tokens=max_tokens)

    def extract_structured(
        self,
        schema: Any,
        document_text: str,
        extra_context: str = "",
        target_fields: list[Any] | None = None,
    ) -> dict:

        from backend.app.utils.json_utils import safe_parse_json

        # ── LandingAI ADE path ───────────────────────────────
        if self._provider_enum == AIProvider.landingai:

            fields = target_fields or schema.fields

            json_schema = {
                "type": "object",
                "properties": {},
                "required": [],
            }

            for f in fields:

                field_type = f.type.value

                if field_type == "number":
                    js_type = "number"
                elif field_type == "boolean":
                    js_type = "boolean"
                elif field_type == "array":
                    js_type = "array"
                elif field_type == "object":
                    js_type = "object"
                else:
                    js_type = "string"

                prop = {
                    "type": js_type,
                    "description": f.instruction or f"Extract {f.name}",
                }

                if js_type == "array":
                    prop["items"] = {"type": "string"}

                json_schema["properties"][f.name] = prop

                if f.required:
                    json_schema["required"].append(f.name)

            logger.info(
                "Using AI provider: %s | target_fields=%s | text_len=%d",
                self._provider_enum.value,
                [f.name for f in fields],
                len(document_text),
            )

            return self._adapter.extract_structured_from_markdown(
                schema=json_schema,
                markdown_text=document_text,
                model="extract-latest",
            )

        # ── Generic LLM path ─────────────────────────────────
        system = (
            "You are a schema-driven document extraction specialist. "
            "Extract only the fields explicitly requested. "
            "Return JSON only."
        )

        prompt = f"{system}\n\n{document_text[:12000]}"

        raw = self.complete(prompt, system=system, max_tokens=4096)

        parsed = safe_parse_json(raw)

        if parsed is None:
            raise AIProviderError("AI returned non-JSON response")

        return parsed

    def _build_adapter(self):

        p = self._provider_enum

        try:

            if p == AIProvider.openai:
                from backend.app.providers.openai_provider import OpenAIProvider
                return OpenAIProvider()

            if p == AIProvider.anthropic:
                from backend.app.providers.anthropic_provider import AnthropicProvider
                return AnthropicProvider()

            if p == AIProvider.gemini:
                from backend.app.providers.gemini_provider import GeminiProvider
                return GeminiProvider()

            if p == AIProvider.ollama:
                from backend.app.providers.ollama_provider import OllamaProvider
                return OllamaProvider()

            if p == AIProvider.landingai:
                from backend.app.providers.landingai_provider import LandingAIProvider
                return LandingAIProvider()

        except Exception as exc:
            logger.warning("Could not initialise provider %s: %s", p.value, exc)

        return None