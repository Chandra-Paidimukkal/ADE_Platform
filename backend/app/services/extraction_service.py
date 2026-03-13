"""
ExtractionService – orchestrates all extractors, merges results,
applies schema instruction rules, normalises values, and returns a
DocumentExtractionResult.

Flow:
  1. Deterministic extractors
  2. Merge best deterministic results
  3. AI only for unresolved fields
  4. Apply schema instruction rule if still missing
  5. Normalize values
  6. Build final structured result
"""
from __future__ import annotations

import logging
from typing import Any

from backend.app.core.enums import ExtractionStatus
from backend.app.core.llm_router import LLMRouter
from backend.app.core.models import (
    DocumentExtractionResult,
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
)
from backend.app.extractors.ai_extractor import AIExtractor
from backend.app.extractors.keyvalue_extractor import KeyValueExtractor
from backend.app.extractors.regex_extractor import RegexExtractor
from backend.app.extractors.table_extractor import TableExtractor
from backend.app.utils.schema_rule_utils import extract_missing_code
from backend.app.utils.text_utils import apply_normalization

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self, router: LLMRouter | None = None) -> None:
        self._regex = RegexExtractor()
        self._kv = KeyValueExtractor()
        self._table = TableExtractor()
        self._ai = AIExtractor(router or LLMRouter())

    # ── Public ───────────────────────────────────────────────────────

    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
        use_ai: bool = True,
    ) -> DocumentExtractionResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not doc.is_valid:
            err = doc.parse_error or "Empty document"
            return DocumentExtractionResult(
                file=doc.file_name,
                status=ExtractionStatus.failed,
                errors=[err],
                metadata={"pages_processed": 0},
            )

        merged: dict[str, FieldExtractionResult] = {}

        # 1. Run deterministic extractors first
        for extractor in (self._kv, self._table, self._regex):
            partial = extractor.extract(doc, schema)
            for fname, res in partial.items():
                existing = merged.get(fname)
                if existing is None or res.confidence > existing.confidence:
                    merged[fname] = res

        # 2. Identify unresolved fields
        unresolved_fields = []
        for field in schema.fields:
            existing = merged.get(field.name)
            if existing is None:
                unresolved_fields.append(field)
                continue

            value = existing.value
            if value is None:
                unresolved_fields.append(field)
            elif isinstance(value, str) and not value.strip():
                unresolved_fields.append(field)

        # 3. AI only for unresolved fields
        if use_ai and unresolved_fields:
            try:
                ai_results = self._ai.extract(
                    doc,
                    schema,
                    unresolved_fields=unresolved_fields,
                )
                for fname, res in ai_results.items():
                    existing = merged.get(fname)
                    if existing is None:
                        merged[fname] = res
                    else:
                        # Only replace empty deterministic result, not good exact match
                        if existing.value is None or (
                            isinstance(existing.value, str) and not existing.value.strip()
                        ):
                            merged[fname] = res
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"AI extractor error: {exc}")
                logger.warning("AI extractor failed on %s: %s", doc.file_name, exc)

        # 4. Build final output using schema instruction as rulebook
        data: dict[str, Any] = {}
        field_sources: dict[str, str] = {}
        field_details: dict[str, Any] = {}

        for field in schema.fields:
            result = merged.get(field.name)

            if result is not None and result.value is not None:
                if isinstance(result.value, str) and result.value.strip():
                    value = self._normalise(result.value, field)
                    source = result.source
                    schema_rule_applied = getattr(result, "schema_rule_applied", False)
                elif not isinstance(result.value, str):
                    value = self._normalise(result.value, field)
                    source = result.source
                    schema_rule_applied = getattr(result, "schema_rule_applied", False)
                else:
                    value = self._apply_schema_rule(field)
                    source = "schema_rule"
                    schema_rule_applied = True
            else:
                value = self._apply_schema_rule(field)
                source = "schema_rule"
                schema_rule_applied = True

            data[field.name] = value
            field_sources[field.name] = source
            field_details[field.name] = {
                "source": source,
                "instruction": field.instruction,
                "missing_code": extract_missing_code(field),
                "schema_rule_applied": schema_rule_applied,
                "confidence": result.confidence if result is not None else 0.0,
                "page_number": getattr(result, "page_number", None) if result is not None else None,
                "matched_text": getattr(result, "matched_text", None) if result is not None else None,
            }

            if field.required and source == "schema_rule":
                warnings.append(
                    f"Required field '{field.name}' not found; schema rule applied"
                )

        # 5. Determine status
        all_schema_rule = all(
            field_sources.get(field.name) == "schema_rule"
            for field in schema.fields
        ) if schema.fields else False

        any_schema_rule = any(
            field_sources.get(field.name) == "schema_rule"
            for field in schema.fields
        )

        if errors:
            status = ExtractionStatus.failed
        elif all_schema_rule:
            status = ExtractionStatus.partial
        elif any_schema_rule:
            status = ExtractionStatus.partial
        else:
            status = ExtractionStatus.success

        return DocumentExtractionResult(
            file=doc.file_name,
            status=status,
            data=data,
            errors=errors,
            warnings=warnings,
            field_sources=field_sources,
            field_details=field_details,
            metadata={
                "pages_processed": doc.page_count,
                "text_length": len(doc.full_text),
                "extractors_used": sorted(list({v for v in field_sources.values() if v != "schema_rule"})),
            },
        )

    # ── Private ──────────────────────────────────────────────────────

    @staticmethod
    def _normalise(value: Any, field) -> Any:  # field: SchemaField
        if isinstance(value, str):
            return apply_normalization(value, field.normalization)
        if isinstance(value, list):
            return [
                apply_normalization(v, field.normalization) if isinstance(v, str) else v
                for v in value
            ]
        return value

    @staticmethod
    def _apply_schema_rule(field) -> Any:
        """
        Read schema instruction and return the code defined there
        when a value is missing.
        Example:
            'If not found return NC.' -> 'NC'
        """
        code = extract_missing_code(field)
        return code