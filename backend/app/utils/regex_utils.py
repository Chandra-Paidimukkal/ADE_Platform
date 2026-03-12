"""
Regex helpers for field extraction.
Generates dynamic patterns from schema field names and aliases.
"""
from __future__ import annotations

import re
from typing import Iterator


# Separators commonly seen between a label and a value
_SEPS = r"[\s\-:=\|]+"

# Value pattern – captures up to end of line or a unit-like token
_VALUE = r"(.+?)(?:\s*\n|$)"


def build_kv_pattern(labels: list[str]) -> re.Pattern:
    """
    Build a regex that matches any of the given labels followed by a separator
    and a value on the same line.
    """
    escaped = [re.escape(lbl) for lbl in labels]
    label_group = "(?:" + "|".join(escaped) + ")"
    pattern = rf"(?i)\b{label_group}{_SEPS}{_VALUE}"
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def find_all_values(text: str, pattern: re.Pattern) -> list[str]:
    return [m.group(1).strip() for m in pattern.finditer(text) if m.group(1).strip()]


def extract_numbers(text: str) -> list[str]:
    """Extract all numeric tokens (int or float, optional unit suffix)."""
    return re.findall(r"\b\d+(?:\.\d+)?(?:\s*[a-zA-Z%/]+)?", text)


def extract_measurement(text: str, unit_hint: str = "") -> str | None:
    """
    Try to pull a measurement like '23 cu ft', '120 lbs', '48.25 in'.
    unit_hint focuses the search (e.g. "lbs").
    """
    if unit_hint:
        pat = rf"\b(\d+(?:\.\d+)?)\s*{re.escape(unit_hint)}\b"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    # Generic: number followed by a unit word
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*([a-zA-Z°%/]+\b)", text)
    return m.group(0).strip() if m else None


def iter_table_kv(rows: list[list[str]]) -> Iterator[tuple[str, str]]:
    """Yield (key, value) pairs from 2-column table rows."""
    for row in rows:
        if len(row) >= 2:
            key = row[0].strip()
            val = row[1].strip()
            if key and val:
                yield key, val
