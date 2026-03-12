"""
Core domain models (dataclasses + Pydantic).
These are the internal representations used by services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from backend.app.core.enums import ExtractionStatus, FieldType, SourceHint


# ── Parsed document ──────────────────────────────────────────────────

@dataclass
class ParsedBlock:
    text: str
    bbox: tuple[float, float, float, float] | None = None
    block_type: str = "text"


@dataclass
class ParsedTable:
    rows: list[list[str]]
    headers: list[str] = field(default_factory=list)


@dataclass
class ParsedPage:
    page_number: int
    text: str
    blocks: list[ParsedBlock] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)


@dataclass
class ParsedDocument:
    file_name: str
    file_path: str
    pages: list[ParsedPage] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    parse_error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.parse_error is None and bool(self.full_text.strip())


# ── Schema domain models ─────────────────────────────────────────────

class NormalizationRule(BaseModel):
    strip_whitespace: bool = True
    to_uppercase: bool = False
    to_lowercase: bool = False
    replace_patterns: list[dict[str, str]] = Field(default_factory=list)


class SchemaField(BaseModel):
    name: str
    type: FieldType = FieldType.string
    instruction: str = ""
    required: bool = False
    aliases: list[str] = Field(default_factory=list)
    multi_value: bool = False
    source_hint: SourceHint = SourceHint.any
    normalization: NormalizationRule | None = None
    order: int = 0


class ExtractionSchema(BaseModel):
    schema_id: str
    schema_name: str
    version: str = "1.0"
    description: str = ""
    fields: list[SchemaField] = Field(default_factory=list)

    def get_field(self, name: str) -> SchemaField | None:
        return next((f for f in self.fields if f.name == name), None)

    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]


# ── Extraction result ────────────────────────────────────────────────

@dataclass
class FieldExtractionResult:
    field_name: str
    value: Any
    source: str = "unknown"   # "regex" | "keyvalue" | "table" | "ai" | "schema_rule"
    confidence: float = 1.0
    raw_value: Any = None
    page_number: int | None = None
    matched_text: str | None = None
    schema_rule_applied: bool = False


@dataclass
class DocumentExtractionResult:
    file: str
    status: ExtractionStatus
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    field_sources: dict[str, str] = field(default_factory=dict)
    field_details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "status": self.status.value,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "field_sources": self.field_sources,
            "field_details": self.field_details,
        }


# ── Job model ────────────────────────────────────────────────────────

@dataclass
class BatchJob:
    job_id: str
    total_files: int
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    status: str = "pending"
    results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    @property
    def progress_pct(self) -> float:
        if self.total_files == 0:
            return 0.0
        return round(self.processed / self.total_files * 100, 1)