"""
Pydantic models for all API request bodies and response shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.app.core.enums import ExtractionStatus, FieldType, SourceHint


# ── Shared sub-models ────────────────────────────────────────────────

class NormalizationRuleRequest(BaseModel):
    strip_whitespace: bool = True
    to_uppercase: bool = False
    to_lowercase: bool = False
    replace_patterns: list[dict[str, str]] = Field(default_factory=list)


class SchemaFieldRequest(BaseModel):
    name: str
    type: FieldType = FieldType.string
    instruction: str = ""
    required: bool = False
    aliases: list[str] = Field(default_factory=list)
    multi_value: bool = False
    source_hint: SourceHint = SourceHint.any
    normalization: NormalizationRuleRequest | None = None
    order: int = 0


class SchemaFieldResponse(SchemaFieldRequest):
    pass


class SchemaResponse(BaseModel):
    schema_id: str
    schema_name: str
    version: str = "1.0"
    description: str = ""
    fields: list[SchemaFieldResponse] = Field(default_factory=list)


# ── Document routes ──────────────────────────────────────────────────

class ParseRequest(BaseModel):
    file_path: str = Field(..., description="Absolute or relative path to a PDF")


class ParseBatchRequest(BaseModel):
    folder_path: str = Field(..., description="Folder containing PDFs")
    recursive: bool = False


class ParsedPageResponse(BaseModel):
    page_number: int
    text: str
    table_count: int


class ParsedDocumentResponse(BaseModel):
    file_name: str
    file_path: str
    page_count: int
    full_text: str
    pages: list[ParsedPageResponse]
    parse_error: str | None


# ── Schema routes ────────────────────────────────────────────────────

class CreateSchemaRequest(BaseModel):
    schema_name: str
    version: str = "1.0"
    description: str = ""
    fields: list[SchemaFieldRequest] = Field(default_factory=list)


class UpdateSchemaMetaRequest(BaseModel):
    schema_name: str | None = None
    version: str | None = None
    description: str | None = None


class ReorderFieldsRequest(BaseModel):
    field_order: list[str] = Field(..., description="Ordered list of field names")


class ValidateSchemaResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


# ── Extraction routes ────────────────────────────────────────────────

class ExtractionRequest(BaseModel):
    file_path: str
    schema_id: str
    use_ai: bool = True
    ai_provider: str | None = Field(
        default=None,
        description="Optional provider override: openai | anthropic | gemini | ollama | landingai | custom | none",
    )


class BatchExtractionRequest(BaseModel):
    folder_path: str
    schema_id: str
    use_ai: bool = True
    async_mode: bool = False
    recursive: bool = False
    ai_provider: str | None = Field(
        default=None,
        description="Optional provider override: openai | anthropic | gemini | ollama | landingai | custom | none",
    )


class ExtractionResultResponse(BaseModel):
    file: str
    status: ExtractionStatus
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    field_sources: dict[str, str] = Field(default_factory=dict)
    field_details: dict[str, Any] = Field(default_factory=dict)


class BatchExtractionResponse(BaseModel):
    job_id: str
    status: str
    total_files: int
    processed: int
    succeeded: int
    failed: int
    results: list[ExtractionResultResponse]


# ── Export routes ────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    job_id: str | None = None
    results: list[dict] | None = None
    output_path: str | None = None


class ExportResponse(BaseModel):
    path: str
    records: int


# ── Job routes ───────────────────────────────────────────────────────

class JobResponse(BaseModel):
    job_id: str
    status: str
    total_files: int
    processed: int
    succeeded: int
    failed: int
    progress_pct: float
    started_at: str
    completed_at: str


# ── Generic responses ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Any | None = None