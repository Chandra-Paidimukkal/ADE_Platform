"""
TableExtractor – searches parsed tables for schema field values.

Handles:
  - Multi-row spec tables (header row + data rows)
  - Two-column label/value tables
  - Header-indexed tables (field name matches a column header)
  - Alias-aware matching
  - Basic fuzzy matching
"""
from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from backend.app.core.models import (
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
    ParsedTable,
    SchemaField,
)
from backend.app.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

_SIMILARITY_THRESHOLD = 0.78


def _normalize_label(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_value(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^[\s:;\-|]+", "", text)
    text = re.sub(r"[\s:;\-|]+$", "", text)
    return text.strip()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize_label(a), _normalize_label(b)).ratio()


def _best_match(needle: str, haystack: list[str]) -> tuple[int, float]:
    best_idx, best_score = -1, 0.0
    for i, item in enumerate(haystack):
        score = _similarity(needle, item)
        if score > best_score:
            best_score, best_idx = score, i
    return best_idx, best_score


class TableExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "table"

    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
    ) -> dict[str, FieldExtractionResult]:
        results: dict[str, FieldExtractionResult] = {}

        for page in doc.pages:
            for table in page.tables:
                for field in schema.fields:
                    if field.name in results:
                        continue

                    result = self._search_table(table, field, page.page_number)
                    if result is not None:
                        results[field.name] = result

        return results

    # ── Private ──────────────────────────────────────────────────────

    def _search_table(
        self,
        table: ParsedTable,
        field: SchemaField,
        page_number: int,
    ) -> FieldExtractionResult | None:
        candidates = self._candidate_labels(field)

        # Strategy 1: match against column headers
        header_result = self._extract_from_headers(table, field, candidates, page_number)
        if header_result is not None:
            return header_result

        # Strategy 2: 2-column / first-column label-value matching
        label_result = self._extract_from_first_column(table, field, candidates, page_number)
        if label_result is not None:
            return label_result

        return None

    def _extract_from_headers(
        self,
        table: ParsedTable,
        field: SchemaField,
        candidates: list[str],
        page_number: int,
    ) -> FieldExtractionResult | None:
        if not table.headers:
            return None

        normalized_headers = [_normalize_label(h) for h in table.headers]

        best_idx = -1
        best_score = 0.0
        best_candidate = None

        for candidate in candidates:
            idx, score = _best_match(candidate, normalized_headers)
            if score > best_score:
                best_idx = idx
                best_score = score
                best_candidate = candidate

        if best_idx < 0 or best_score < _SIMILARITY_THRESHOLD:
            return None

        values: list[str] = []
        for row in table.rows:
            if best_idx < len(row):
                val = _clean_value(row[best_idx])
                if val:
                    values.append(val)

        values = self._dedupe(values)
        if not values:
            return None

        final_value = values if field.multi_value else values[0]

        return FieldExtractionResult(
            field_name=field.name,
            value=final_value,
            raw_value=values,
            matched_text=f"header={table.headers[best_idx]}",
            page_number=page_number,
            source=self.name,
            confidence=round(best_score, 2),
        )

    def _extract_from_first_column(
        self,
        table: ParsedTable,
        field: SchemaField,
        candidates: list[str],
        page_number: int,
    ) -> FieldExtractionResult | None:
        matched_values: list[str] = []
        best_score = 0.0
        best_label = None

        for row in table.rows:
            if not row or len(row) < 2:
                continue

            first_col = _normalize_label(row[0])
            if not first_col:
                continue

            for candidate in candidates:
                score = _similarity(candidate, first_col)
                if score >= _SIMILARITY_THRESHOLD:
                    val = _clean_value(row[1])
                    if val:
                        matched_values.append(val)
                        if score > best_score:
                            best_score = score
                            best_label = row[0]

        matched_values = self._dedupe(matched_values)
        if not matched_values:
            return None

        final_value = matched_values if field.multi_value else matched_values[0]

        return FieldExtractionResult(
            field_name=field.name,
            value=final_value,
            raw_value=matched_values,
            matched_text=best_label,
            page_number=page_number,
            source=self.name,
            confidence=round(best_score, 2) if best_score else 0.82,
        )

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

        normalized = [_normalize_label(x) for x in expanded]

        seen = set()
        final = []
        for item in normalized:
            if item and item not in seen:
                seen.add(item)
                final.append(item)

        return final

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
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