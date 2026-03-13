"""
SchemaGenerator – uses the LLM to generate a schema from a user prompt.
Falls back to a minimal stub schema when AI is unavailable.
"""
from __future__ import annotations

import logging
import re

from backend.app.core.llm_router import LLMRouter
from backend.app.core.models import ParsedDocument
from backend.app.utils.json_utils import safe_parse_json

logger = logging.getLogger(__name__)


_SYSTEM = (
    "You are a data schema architect. "
    "Given a user description, create a JSON extraction schema. "
    "Return ONLY a JSON object with: "
    "schema_name (string), version ('1.0'), description (string), "
    "fields (array). "
    "Each field must have: name (snake_case), type (string|number|boolean|array|date|object), "
    "instruction (extraction instruction), fallback ('NULL'), required (bool), "
    "aliases (string array), multi_value (bool), source_hint (text|table|any). "
    "Return raw JSON only – no markdown."
)


class SchemaGenerator:
    def __init__(self, router: LLMRouter | None = None) -> None:
        self._router = router or LLMRouter()

    def generate_from_prompt(
        self,
        user_prompt: str,
        parsed_doc: ParsedDocument | None = None,
        schema_name: str = "generated_schema",
    ) -> dict:
        context = ""
        if parsed_doc and parsed_doc.full_text:
            context = (
                "\n\nContext from a sample document:\n"
                + parsed_doc.full_text[:3000]
            )

        prompt = (
            f"Create a document extraction schema for the following requirement:\n"
            f"{user_prompt}{context}\n\n"
            f"Schema name should be '{schema_name}'."
        )

        if not self._router.available:
            logger.warning("AI unavailable – returning stub schema for prompt")
            return self._stub_schema(schema_name, user_prompt)

        try:
            raw = self._router.complete(prompt, system=_SYSTEM, max_tokens=2048)
            parsed = safe_parse_json(raw)
            if parsed and isinstance(parsed, dict) and "fields" in parsed:
                parsed.setdefault("schema_name", schema_name)
                parsed.setdefault("version", "1.0")
                return parsed
            logger.warning("AI returned unexpected shape – using stub")
        except Exception as exc:  # noqa: BLE001
            logger.error("Schema generation failed: %s", exc)

        return self._stub_schema(schema_name, user_prompt)

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _stub_schema(schema_name: str, description: str) -> dict:
        return {
            "schema_name": schema_name,
            "version":     "1.0",
            "description": description,
            "fields": [
                {
                    "name":        "document_title",
                    "type":        "string",
                    "instruction": "Extract the title or heading of the document.",
                    "fallback":    "NULL",
                    "required":    False,
                    "aliases":     ["title", "heading"],
                    "multi_value": False,
                    "source_hint": "text",
                    "order":       0,
                }
            ],
        }
