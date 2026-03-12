from __future__ import annotations

from typing import Any

from backend.app.core.enums import FieldType, SourceHint
from backend.app.core.models import ExtractionSchema, SchemaField
from backend.app.utils.file_utils import new_id


class SchemaNormalizer:
    """
    Converts different external schema styles into the platform's
    internal canonical ExtractionSchema format.
    """

    def normalize(self, payload: dict[str, Any]) -> ExtractionSchema:
        if self._looks_like_internal_schema(payload):
            return self._from_internal_schema(payload)

        if self._looks_like_json_schema(payload):
            return self._from_json_schema(payload)

        if self._looks_like_prompt_schema(payload):
            return self._from_prompt_schema(payload)

        raise ValueError("Unsupported schema format")

    # ── Format detection ─────────────────────────────────────────────

    @staticmethod
    def _looks_like_internal_schema(payload: dict[str, Any]) -> bool:
        return "schema_name" in payload and "fields" in payload

    @staticmethod
    def _looks_like_json_schema(payload: dict[str, Any]) -> bool:
        return payload.get("type") == "object" and "properties" in payload

    @staticmethod
    def _looks_like_prompt_schema(payload: dict[str, Any]) -> bool:
        return "instruction" in payload or "prompt" in payload

    # ── Converters ───────────────────────────────────────────────────

    def _from_internal_schema(self, payload: dict[str, Any]) -> ExtractionSchema:
        fields = []
        for i, item in enumerate(payload.get("fields", [])):
            fields.append(
                SchemaField(
                    name=item["name"],
                    type=self._map_type(item.get("type", "string")),
                    instruction=item.get("instruction", ""),
                    required=item.get("required", False),
                    aliases=item.get("aliases", []),
                    multi_value=item.get("multi_value", False),
                    source_hint=self._map_source_hint(item.get("source_hint", "any")),
                    normalization=item.get("normalization"),
                    order=item.get("order", i),
                )
            )

        return ExtractionSchema(
            schema_id=payload.get("schema_id") or new_id(),
            schema_name=payload["schema_name"],
            version=payload.get("version", "1.0"),
            description=payload.get("description", ""),
            fields=fields,
        )

    def _from_json_schema(self, payload: dict[str, Any]) -> ExtractionSchema:
        title = payload.get("title", "imported_schema")
        description = payload.get("description", "")
        properties = payload.get("properties", {})
        required_fields = set(payload.get("required", []))

        fields: list[SchemaField] = []

        for i, (field_name, spec) in enumerate(properties.items()):
            instruction = (
                spec.get("description")
                or spec.get("title")
                or f"Extract {field_name} from the document."
            )

            fields.append(
                SchemaField(
                    name=field_name,
                    type=self._map_type(spec.get("type", "string")),
                    instruction=instruction,
                    required=field_name in required_fields,
                    aliases=[],
                    multi_value=(spec.get("type") == "array"),
                    source_hint=SourceHint.any,
                    order=i,
                )
            )

        return ExtractionSchema(
            schema_id=new_id(),
            schema_name=title,
            version="1.0",
            description=description,
            fields=fields,
        )

    def _from_prompt_schema(self, payload: dict[str, Any]) -> ExtractionSchema:
        prompt = payload.get("instruction") or payload.get("prompt") or ""
        schema_name = payload.get("schema_name", "prompt_schema")

        # Minimal placeholder schema from prompt-style input.
        # Later you can replace this with AI-based schema generation.
        return ExtractionSchema(
            schema_id=new_id(),
            schema_name=schema_name,
            version="1.0",
            description=prompt,
            fields=[],
        )

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _map_type(value: Any) -> FieldType:
        if isinstance(value, FieldType):
            return value

        text = str(value).lower()

        if text in {"string", "str"}:
            return FieldType.string
        if text in {"number", "float", "double", "decimal", "integer", "int"}:
            return FieldType.number
        if text in {"boolean", "bool"}:
            return FieldType.boolean
        if text == "array":
            return FieldType.array
        if text == "date":
            return FieldType.date
        if text == "object":
            return FieldType.object

        return FieldType.string

    @staticmethod
    def _map_source_hint(value: Any) -> SourceHint:
        if isinstance(value, SourceHint):
            return value

        text = str(value).lower()
        if text == "text":
            return SourceHint.text
        if text == "table":
            return SourceHint.table
        if text == "diagram":
            return SourceHint.diagram
        if text == "header":
            return SourceHint.header
        return SourceHint.any