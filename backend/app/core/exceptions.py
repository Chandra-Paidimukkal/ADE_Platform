"""Domain exceptions for the ADE platform."""
from __future__ import annotations


class ADEBaseError(Exception):
    """Root exception for all ADE errors."""


class PDFParseError(ADEBaseError):
    """Raised when a PDF cannot be parsed."""


class SchemaNotFoundError(ADEBaseError):
    """Raised when a requested schema does not exist."""


class SchemaValidationError(ADEBaseError):
    """Raised when a schema fails validation."""


class ExtractionError(ADEBaseError):
    """Raised when extraction fails unrecoverably for a document."""


class AIProviderError(ADEBaseError):
    """Raised on AI provider communication failures."""


class AIResponseParseError(ADEBaseError):
    """Raised when the AI returns malformed / non-JSON output."""


class BatchError(ADEBaseError):
    """Raised for batch-level failures."""


class ExportError(ADEBaseError):
    """Raised when output export fails."""
