from __future__ import annotations

import re

from backend.app.core.models import SchemaField

MISSING_CODE_PATTERNS = [
    r"\bif not found[, ]+return\s+([A-Z0-9_]+)\b",
    r"\bif missing[, ]+return\s+([A-Z0-9_]+)\b",
    r"\bif not available[, ]+return\s+([A-Z0-9_]+)\b",
    r"\bif unavailable[, ]+return\s+([A-Z0-9_]+)\b",
    r"\breturn\s+([A-Z0-9_]+)\s+if not found\b",
]

def extract_missing_code(field: SchemaField) -> str | None:
    instruction = (field.instruction or "").strip()
    if not instruction:
        return None

    for pattern in MISSING_CODE_PATTERNS:
        match = re.search(pattern, instruction, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None