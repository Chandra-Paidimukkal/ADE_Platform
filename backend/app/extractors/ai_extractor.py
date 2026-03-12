"""
AIExtractor – uses the LLMRouter to extract schema-driven fields.

AI should mainly be used for unresolved or ambiguous fields.
Failures are logged and an empty dict is returned so the pipeline
can continue with rule-based results.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.app.core.exceptions import AIProviderError, AIResponseParseError
from backend.app.core.llm_router import LLMRouter
from backend.app.core.models import (
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
    SchemaField,
)
from backend.app.extractors.base import BaseExtractor
from backend.app.utils.schema_rule_utils import extract_missing_code

logger = logging.getLogger(__name__)


class AIExtractor(BaseExtractor):
    def __init__(self, router: LLMRouter | None = None) -> None:
        self._router = router or LLMRouter()

    @property
    def name(self) -> str:
        return "ai"

    @property
    def available(self) -> bool:
        return self._router.available

    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
        unresolved_fields: list[SchemaField] | None = None,
    ) -> dict[str, FieldExtractionResult]:
        if not self.available:
            logger.debug("AI extractor skipped – no provider configured")
            return {}

        target_fields = unresolved_fields or schema.fields
        if not target_fields:
            logger.debug("AI extractor skipped – no target fields")
            return {}

        logger.info("AI extractor called for fields: %s", [f.name for f in target_fields])

        try:
            raw: dict[str, Any] = self._router.extract_structured(
                schema=schema,
                document_text=doc.full_text,
                extra_context=f"File: {doc.file_name}",
                target_fields=target_fields,
            )
        except (AIProviderError, AIResponseParseError) as exc:
            logger.warning("AI extraction failed for %s: %s", doc.file_name, exc)
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected AI error for %s: %s", doc.file_name, exc)
            return {}

        results: dict[str, FieldExtractionResult] = {}

        for field in target_fields:
            if field.name not in raw:
                continue

            value = raw[field.name]

            if value is None:
                continue

            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue

            expected_missing_code = extract_missing_code(field)
            schema_rule_applied = False

            if isinstance(value, str) and expected_missing_code:
                if value.upper() == expected_missing_code.upper():
                    schema_rule_applied = True

            results[field.name] = FieldExtractionResult(
                field_name=field.name,
                value=value,
                raw_value=value,
                source=self.name,
                confidence=0.90 if not schema_rule_applied else 0.60,
                schema_rule_applied=schema_rule_applied,
            )

        return results