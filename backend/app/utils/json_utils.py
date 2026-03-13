"""Safe JSON parsing utilities."""
from __future__ import annotations

import json
import re


def safe_parse_json(text: str) -> dict | list | None:
    """
    Try multiple strategies to extract a JSON object/array from *text*.
    Returns None if all strategies fail.
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences ```json … ```
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Extract first {...} block
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 4. Extract first [...] block
    m = re.search(r"(\[.*\])", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    return None


def flatten_nested(data: dict, prefix: str = "", sep: str = ".") -> dict:
    """Flatten a nested dict to dot-separated keys."""
    items: dict = {}
    for k, v in data.items():
        new_key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten_nested(v, new_key, sep))
        elif isinstance(v, list):
            items[new_key] = ", ".join(str(i) for i in v)
        else:
            items[new_key] = v
    return items
