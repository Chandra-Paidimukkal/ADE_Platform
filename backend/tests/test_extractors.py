"""Unit tests for rule-based extractors."""
from __future__ import annotations

import pytest

from backend.app.core.models import (
    ExtractionSchema,
    ParsedDocument,
    ParsedPage,
    ParsedTable,
    SchemaField,
)
from backend.app.extractors.keyvalue_extractor import KeyValueExtractor
from backend.app.extractors.regex_extractor import RegexExtractor
from backend.app.extractors.table_extractor import TableExtractor


def _make_doc(text: str, tables: list | None = None) -> ParsedDocument:
    page = ParsedPage(
        page_number=1,
        text=text,
        tables=tables or [],
    )
    return ParsedDocument(
        file_name="test.pdf",
        file_path="/tmp/test.pdf",
        pages=[page],
        full_text=text,
        page_count=1,
    )


def _make_schema(*field_defs) -> ExtractionSchema:
    fields = []
    for i, (name, aliases) in enumerate(field_defs):
        fields.append(
            SchemaField(
                name=name,
                aliases=aliases,
                order=i,
                fallback="NULL",
            )
        )
    return ExtractionSchema(schema_id="test", schema_name="test", fields=fields)


# ── RegexExtractor ────────────────────────────────────────────────────

class TestRegexExtractor:
    def setup_method(self):
        self.extractor = RegexExtractor()

    def test_extracts_colon_separated(self):
        doc    = _make_doc("Voltage: 115V\nWeight: 120 lbs")
        schema = _make_schema(("Voltage", []), ("Weight", []))
        res    = self.extractor.extract(doc, schema)
        assert "Voltage" in res
        assert "115V" in res["Voltage"].value

    def test_alias_extraction(self):
        doc    = _make_doc("Manufacturer: AirEase")
        schema = _make_schema(("manufacturer_name", ["Manufacturer", "Brand"]))
        res    = self.extractor.extract(doc, schema)
        assert "manufacturer_name" in res

    def test_missing_field_not_in_results(self):
        doc    = _make_doc("Some unrelated text about nothing")
        schema = _make_schema(("model_number", ["Model", "Part No"]))
        res    = self.extractor.extract(doc, schema)
        assert "model_number" not in res


# ── KeyValueExtractor ─────────────────────────────────────────────────

class TestKeyValueExtractor:
    def setup_method(self):
        self.extractor = KeyValueExtractor()

    def test_dash_separated(self):
        doc    = _make_doc("Capacity - 23 cu ft")
        schema = _make_schema(("Capacity", []))
        res    = self.extractor.extract(doc, schema)
        assert "Capacity" in res

    def test_table_kv(self):
        table = ParsedTable(rows=[["Voltage", "208-230V"], ["Weight", "285 lbs"]])
        doc   = _make_doc("", tables=[table])
        schema = _make_schema(("Voltage", []), ("Weight", []))
        res   = self.extractor.extract(doc, schema)
        assert "Voltage" in res
        assert "Weight"  in res


# ── TableExtractor ────────────────────────────────────────────────────

class TestTableExtractor:
    def setup_method(self):
        self.extractor = TableExtractor()

    def test_header_column_match(self):
        table  = ParsedTable(
            headers=["Model", "Voltage", "BTU"],
            rows=[["TGR1SHC", "115V", "24000"]],
        )
        doc    = _make_doc("", tables=[table])
        schema = _make_schema(("Model", []), ("Voltage", []), ("BTU", []))
        res    = self.extractor.extract(doc, schema)
        assert res["Model"].value   == "TGR1SHC"
        assert res["Voltage"].value == "115V"
        assert res["BTU"].value     == "24000"

    def test_two_column_label_value(self):
        table  = ParsedTable(rows=[["Fuel Type", "Natural Gas"], ["Weight (lbs)", "285"]])
        doc    = _make_doc("", tables=[table])
        schema = _make_schema(("Fuel Type", []), ("Weight", ["Weight (lbs)"]))
        res    = self.extractor.extract(doc, schema)
        assert "Fuel Type" in res
