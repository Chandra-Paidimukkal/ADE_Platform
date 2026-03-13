"""Platform-wide enumerations."""
from __future__ import annotations

from enum import Enum


class FieldType(str, Enum):
    string  = "string"
    number  = "number"
    boolean = "boolean"
    array   = "array"
    date    = "date"
    object  = "object"


class SourceHint(str, Enum):
    text    = "text"
    table   = "table"
    diagram = "diagram"
    header  = "header"
    any     = "any"


class ExtractionStatus(str, Enum):
    success  = "success"
    partial  = "partial"
    failed   = "failed"
    skipped  = "skipped"


class AIProvider(str, Enum):
    openai    = "openai"
    anthropic = "anthropic"
    gemini    = "gemini"
    ollama    = "ollama"
    landingai = "landingai"
    custom    = "custom"
    none      = "none"


class JobStatus(str, Enum):
    pending          = "pending"
    running          = "running"
    completed        = "completed"
    failed           = "failed"
    partial_success  = "partial_success"