"""
SchemaSuggester – derives candidate schema fields from a parsed document
using frequency-based key-value detection (no AI required).
"""
from __future__ import annotations

import logging
import re
from collections import Counter

from backend.app.core.enums import FieldType, SourceHint
from backend.app.core.models import ParsedDocument, SchemaField

logger = logging.getLogger(__name__)

# Tokens that look like keys (title-case or ALL_CAPS or contain a colon)
_KEY_RE = re.compile(
    r"^(?P<key>[A-Z][A-Za-z0-9 _\-/]{2,40})[:\s\-=|]+(?P<val>.+)$",
    re.MULTILINE,
)

# Rough type inference
_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?(?:\s*[a-zA-Z%/]+)?$")


def _infer_type(value: str) -> FieldType:
    if _NUMBER_RE.match(value.strip()):
        return FieldType.number
    if value.strip().lower() in {"yes", "no", "true", "false"}:
        return FieldType.boolean
    return FieldType.string


class SchemaSuggester:
    def suggest_from_document(
        self,
        parsed_doc: ParsedDocument,
        top_n: int = 30,
        schema_name: str = "suggested_schema",
    ) -> dict:
        """
        Scan the document for label:value patterns and return a schema dict
        with suggested fields (sorted by frequency).
        """
        counter: Counter = Counter()
        samples: dict[str, str] = {}

        for m in _KEY_RE.finditer(parsed_doc.full_text):
            key = m.group("key").strip()
            val = m.group("val").strip()
            if 3 <= len(key) <= 50 and len(val) <= 200:
                counter[key] += 1
                samples.setdefault(key, val)

        # Also check table headers
        for page in parsed_doc.pages:
            for table in page.tables:
                for h in table.headers:
                    h = h.strip()
                    if 2 < len(h) < 50:
                        counter[h] += 1

        top = counter.most_common(top_n)
        fields = []
        for i, (name, _count) in enumerate(top):
            sample_val = samples.get(name, "")
            ft = _infer_type(sample_val)
            hint = SourceHint.table if name in {
                h for page in parsed_doc.pages
                for tbl in page.tables for h in tbl.headers
            } else SourceHint.text

            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_")
            fields.append({
                "name":        safe_name,
                "type":        ft.value,
                "instruction": f"Extract the value associated with '{name}'.",
                "fallback":    "NULL",
                "required":    False,
                "aliases":     [name] if name != safe_name else [],
                "multi_value": False,
                "source_hint": hint.value,
                "order":       i,
            })

        return {
            "schema_name": schema_name,
            "version":     "1.0",
            "description": f"Auto-suggested from {parsed_doc.file_name}",
            "fields":      fields,
        }
