"""Unit tests for SchemaService."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from backend.app.core.exceptions import SchemaNotFoundError, SchemaValidationError
from backend.app.services.schema_service import SchemaService


@pytest.fixture
def svc(tmp_path):
    return SchemaService(schema_dir=tmp_path)


def _sample_fields():
    return [
        {
            "name": "model_number",
            "type": "string",
            "instruction": "Extract the model number.",
            "fallback": "NULL",
            "required": True,
            "aliases": ["model", "part number"],
            "multi_value": False,
            "source_hint": "text",
        }
    ]


def test_create_schema(svc):
    schema = svc.create_schema("test_schema", fields=_sample_fields())
    assert schema.schema_name == "test_schema"
    assert len(schema.fields) == 1
    assert schema.fields[0].name == "model_number"


def test_load_schema(svc):
    created = svc.create_schema("load_test", fields=_sample_fields())
    loaded  = svc.load_schema(created.schema_id)
    assert loaded.schema_id == created.schema_id


def test_schema_not_found(svc):
    with pytest.raises(SchemaNotFoundError):
        svc.load_schema("nonexistent-id")


def test_add_field(svc):
    schema = svc.create_schema("edit_test", fields=_sample_fields())
    svc.add_field(
        schema.schema_id,
        {"name": "voltage", "type": "string", "fallback": "NC"},
    )
    reloaded = svc.load_schema(schema.schema_id)
    assert any(f.name == "voltage" for f in reloaded.fields)


def test_duplicate_field_name_raises(svc):
    schema = svc.create_schema("dup_test", fields=_sample_fields())
    with pytest.raises(SchemaValidationError):
        svc.add_field(schema.schema_id, {"name": "model_number", "type": "string"})


def test_delete_field(svc):
    schema = svc.create_schema("del_test", fields=_sample_fields())
    svc.delete_field(schema.schema_id, "model_number")
    reloaded = svc.load_schema(schema.schema_id)
    assert not any(f.name == "model_number" for f in reloaded.fields)


def test_reorder_fields(svc):
    fields = [
        {"name": "a", "type": "string"},
        {"name": "b", "type": "string"},
        {"name": "c", "type": "string"},
    ]
    schema = svc.create_schema("order_test", fields=fields)
    svc.reorder_fields(schema.schema_id, ["c", "b", "a"])
    reloaded = svc.load_schema(schema.schema_id)
    assert [f.name for f in reloaded.fields] == ["c", "b", "a"]


def test_validate_empty_schema(svc):
    schema = svc.create_schema("val_test")
    errors = svc.validate_schema(schema)
    assert any("field" in e.lower() for e in errors)
