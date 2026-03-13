"""Integration tests for ExtractionService (no AI)."""
from __future__ import annotations

import pytest

from backend.app.core.enums import ExtractionStatus
from backend.app.core.models import (
    ExtractionSchema,
    ParsedDocument,
    ParsedPage,
    ParsedTable,
    SchemaField,
)
from backend.app.services.extraction_service import ExtractionService


def _doc(text: str) -> ParsedDocument:
    page = ParsedPage(page_number=1, text=text)
    return ParsedDocument(
        file_name="test.pdf",
        file_path="/tmp/test.pdf",
        pages=[page],
        full_text=text,
        page_count=1,
    )


def _schema(fields: list[dict]) -> ExtractionSchema:
    return ExtractionSchema(
        schema_id="s1",
        schema_name="test",
        fields=[SchemaField(**f) for f in fields],
    )


@pytest.fixture
def svc():
    # Initialise with no AI router
    from backend.app.core.llm_router import LLMRouter
    return ExtractionService(router=LLMRouter(provider_name="none"))


def test_full_extraction(svc):
    doc = _doc("Voltage: 115V\nWeight: 120 lbs\nModel: TGR1SHC")
    schema = _schema([
        {"name": "Voltage", "fallback": "NC", "aliases": []},
        {"name": "Weight",  "fallback": "NC", "aliases": []},
        {"name": "Model",   "fallback": "NC", "aliases": []},
    ])
    result = svc.extract(doc, schema, use_ai=False)
    assert result.status == ExtractionStatus.success
    assert result.data["Voltage"] == "115V"
    assert result.data["Model"]   == "TGR1SHC"


def test_fallback_applied(svc):
    doc = _doc("Nothing relevant here")
    schema = _schema([
        {"name": "Voltage", "fallback": "NC", "aliases": []},
    ])
    result = svc.extract(doc, schema, use_ai=False)
    assert result.data["Voltage"] == "NC"
    assert result.field_sources["Voltage"] == "fallback"


def test_failed_doc(svc):
    doc = ParsedDocument(
        file_name="broken.pdf",
        file_path="/tmp/broken.pdf",
        parse_error="Corrupted PDF",
    )
    schema = _schema([{"name": "Model", "fallback": "NULL", "aliases": []}])
    result = svc.extract(doc, schema, use_ai=False)
    assert result.status == ExtractionStatus.failed
    assert "Corrupted PDF" in result.errors
