"""Text manipulation helpers."""
from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def to_lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def window_around(text: str, keyword: str, window: int = 200) -> str:
    """Return a substring of *text* centred around *keyword*."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end   = min(len(text), idx + len(keyword) + window)
    return text[start:end]


def extract_between(text: str, start_kw: str, end_kw: str) -> str | None:
    """Return text between two keywords (first occurrence)."""
    s = text.lower().find(start_kw.lower())
    if s == -1:
        return None
    s += len(start_kw)
    e = text.lower().find(end_kw.lower(), s)
    if e == -1:
        return None
    return text[s:e].strip()


def apply_normalization(value: str, rules) -> str:  # rules: NormalizationRule | None
    if not rules:
        return value
    if rules.strip_whitespace:
        value = value.strip()
    if rules.to_uppercase:
        value = value.upper()
    if rules.to_lowercase:
        value = value.lower()
    for rp in rules.replace_patterns or []:
        pattern = rp.get("pattern", "")
        replacement = rp.get("replacement", "")
        if pattern:
            value = re.sub(pattern, replacement, value)
    return value
