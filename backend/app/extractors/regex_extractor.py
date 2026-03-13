"""
RegexExtractor – field-aware pattern matching.

For each schema field it builds regex patterns from:
- field name
- aliases
- human-readable variants

Then it scans the full document text for likely key-value matches.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.app.core.models import (
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
    SchemaField,
)
from backend.app.extractors.base import BaseExtractor
from backend.app.utils.regex_utils import build_kv_pattern, find_all_values

logger = logging.getLogger(__name__)


class RegexExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "regex"

    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
    ) -> dict[str, FieldExtractionResult]:
        results: dict[str, FieldExtractionResult] = {}
        text = doc.full_text
        if not text or not text.strip():
            return results

        for field in schema.fields:
            result = self._extract_field(text, field)
            if result is not None:
                results[field.name] = result

        return results

    # ── Private ──────────────────────────────────────────────────────

    def _extract_field(
        self,
        text: str,
        field: SchemaField,
    ) -> FieldExtractionResult | None:
        labels = self._candidate_labels(field)

        # main key-value style pattern from shared utility
        pattern = build_kv_pattern(labels)
        values = find_all_values(text, pattern)

        # fallback patterns for looser matches
        if not values:
            values = self._fallback_scan(text, labels)

        cleaned_values = self._clean_values(values, field)

        if not cleaned_values:
            return None

        raw: Any = cleaned_values if field.multi_value else cleaned_values[0]
        matched_text = raw if isinstance(raw, str) else ", ".join(map(str, cleaned_values))

        return FieldExtractionResult(
            field_name=field.name,
            value=raw,
            raw_value=values,
            matched_text=matched_text,
            source=self.name,
            confidence=0.75,
        )

    @staticmethod
    def _candidate_labels(field: SchemaField) -> list[str]:
        labels: list[str] = []

        # original field name
        labels.append(field.name)

        # aliases
        labels.extend(field.aliases)

        expanded: list[str] = []
        for label in labels:
            if not label:
                continue

            lbl = label.strip()
            if not lbl:
                continue

            expanded.append(lbl)
            expanded.append(lbl.replace("_", " "))
            expanded.append(lbl.replace("-", " "))
            expanded.append(lbl.replace("_", "-"))

            # title / lower / upper help in noisy docs
            expanded.append(lbl.title())
            expanded.append(lbl.lower())
            expanded.append(lbl.upper())

        # de-duplicate while preserving order
        seen = set()
        final_labels = []
        for item in expanded:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                final_labels.append(item.strip())

        return final_labels

    @staticmethod
    def _fallback_scan(text: str, labels: list[str]) -> list[str]:
        """
        Broader fallback scan for cases like:
        Voltage 115V
        Weight 120 lbs
        Capacity - 23 cu ft
        """
        values: list[str] = []

        for label in labels:
            escaped = re.escape(label)

            patterns = [
                rf"\b{escaped}\b\s*[:\-]\s*([^\n\r|]+)",
                rf"\b{escaped}\b\s+([^\n\r|]+)",
                rf"\b{escaped}\b\s*\(\w+\)\s*[:\-]?\s*([^\n\r|]+)",
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    val = match.group(1).strip()
                    if val:
                        values.append(val)

        return values

    @staticmethod
    def _clean_values(values: list[str], field: SchemaField) -> list[str]:
        """
        Clean noisy regex matches:
        - trim whitespace
        - remove trailing punctuation
        - deduplicate
        - filter obvious junk
        """
        cleaned: list[str] = []
        seen = set()

        for value in values:
            if value is None:
                continue

            v = str(value).strip()
            if not v:
                continue

            # remove common trailing punctuation/noise
            v = re.sub(r"^[\s:;\-|]+", "", v)
            v = re.sub(r"[\s:;\-|]+$", "", v)

            # stop at obvious table spillover / sentence overflow
            v = re.split(r"\s{3,}", v)[0].strip()

            # very long noisy captures are usually bad
            if len(v) > 200:
                continue

            # avoid capturing the label itself as the value
            label_like = {field.name.lower(), field.name.replace("_", " ").lower()}
            if v.lower() in label_like:
                continue

            # de-duplicate
            key = v.lower()
            if key in seen:
                continue

            seen.add(key)
            cleaned.append(v)

        return cleaned