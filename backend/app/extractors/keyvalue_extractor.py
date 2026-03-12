"""
KeyValueExtractor – scans structured key:value pairs found in the text.

Parses lines like:
    Voltage: 115V
    Capacity - 23 cu ft
    Weight   120 lbs

Also reads 2-column table-like structures from parsed tables.
"""
from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from backend.app.core.models import (
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
    SchemaField,
)
from backend.app.extractors.base import BaseExtractor
from backend.app.utils.regex_utils import iter_table_kv

logger = logging.getLogger(__name__)

# Label + separator + value
_KV_RE = re.compile(
    r"^(?P<key>[A-Za-z][A-Za-z0-9 _\-/().]{1,80})"
    r"[\s]*[:\-=|][\s]*"
    r"(?P<val>.+)$",
    re.MULTILINE,
)

# Label + whitespace + value (no explicit separator)
_LOOSE_KV_RE = re.compile(
    r"^(?P<key>[A-Za-z][A-Za-z0-9 _\-/().]{1,80})"
    r"\s{1,}"
    r"(?P<val>[^\n\r]+)$",
    re.MULTILINE,
)


def _normalize_key(key: str) -> str:
    key = key.strip().lower()
    key = key.replace("_", " ")
    key = key.replace("-", " ")
    key = re.sub(r"\s+", " ", key)
    return key


def _clean_value(val: str) -> str:
    val = val.strip()
    val = re.sub(r"^[\s:;\-|]+", "", val)
    val = re.sub(r"[\s:;\-|]+$", "", val)
    val = re.split(r"\s{3,}", val)[0].strip()
    return val


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _build_kv_index(text: str) -> dict[str, list[str]]:
    """
    Return {normalized_key: [values...]} from all KV-like pairs in text.
    """
    index: dict[str, list[str]] = {}

    for regex in (_KV_RE, _LOOSE_KV_RE):
        for match in regex.finditer(text):
            key = _normalize_key(match.group("key"))
            val = _clean_value(match.group("val"))

            if not key or not val:
                continue

            # Avoid absurdly long values caused by line spillover
            if len(val) > 300:
                continue

            index.setdefault(key, []).append(val)

    return index


class KeyValueExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "keyvalue"

    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
    ) -> dict[str, FieldExtractionResult]:
        results: dict[str, FieldExtractionResult] = {}

        kv_index = _build_kv_index(doc.full_text)

        # Also index parsed table rows
        for page in doc.pages:
            for table in page.tables:
                for key, val in iter_table_kv(table.rows):
                    norm_key = _normalize_key(key)
                    clean_val = _clean_value(val)
                    if norm_key and clean_val:
                        kv_index.setdefault(norm_key, []).append(clean_val)

        for field in schema.fields:
            result = self._match_field(field, kv_index)
            if result is not None:
                results[field.name] = result

        return results

    # ── Private ──────────────────────────────────────────────────────

    def _match_field(
        self,
        field: SchemaField,
        kv_index: dict[str, list[str]],
    ) -> FieldExtractionResult | None:
        candidates = self._candidate_labels(field)

        # 1. exact normalized match
        for candidate in candidates:
            if candidate in kv_index:
                values = self._dedupe_values(kv_index[candidate])
                value = values if field.multi_value else values[0]

                return FieldExtractionResult(
                    field_name=field.name,
                    value=value,
                    raw_value=values,
                    matched_text=value if isinstance(value, str) else ", ".join(map(str, values)),
                    source=self.name,
                    confidence=0.85,
                )

        # 2. fuzzy key match
        best_key = None
        best_score = 0.0

        for indexed_key in kv_index:
            for candidate in candidates:
                score = _similarity(candidate, indexed_key)
                if score > best_score:
                    best_score = score
                    best_key = indexed_key

        if best_key and best_score >= 0.82:
            values = self._dedupe_values(kv_index[best_key])
            value = values if field.multi_value else values[0]

            return FieldExtractionResult(
                field_name=field.name,
                value=value,
                raw_value=values,
                matched_text=value if isinstance(value, str) else ", ".join(map(str, values)),
                source=self.name,
                confidence=0.80,
            )

        return None

    @staticmethod
    def _candidate_labels(field: SchemaField) -> list[str]:
        labels = [field.name] + list(field.aliases)

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
            expanded.append(lbl.lower())
            expanded.append(lbl.title())

        normalized = [_normalize_key(x) for x in expanded]

        seen = set()
        final = []
        for item in normalized:
            if item and item not in seen:
                seen.add(item)
                final.append(item)

        return final

    @staticmethod
    def _dedupe_values(values: list[str]) -> list[str]:
        seen = set()
        cleaned: list[str] = []

        for value in values:
            v = _clean_value(value)
            if not v:
                continue

            key = v.lower()
            if key in seen:
                continue

            seen.add(key)
            cleaned.append(v)

        return cleaned