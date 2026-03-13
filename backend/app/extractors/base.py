"""Abstract base extractor – all extractors implement this contract."""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.core.models import (
    ExtractionSchema,
    FieldExtractionResult,
    ParsedDocument,
)


class BaseExtractor(ABC):
    """
    An extractor attempts to extract one or more field values from a
    ParsedDocument according to the active ExtractionSchema.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in field_sources."""

    @abstractmethod
    def extract(
        self,
        doc: ParsedDocument,
        schema: ExtractionSchema,
    ) -> dict[str, FieldExtractionResult]:
        """
        Return a mapping of field_name → FieldExtractionResult.
        Fields that are not found should not be included in the dict;
        the ExtractionService applies fallbacks.
        """
