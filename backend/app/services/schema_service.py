"""
SchemaService – full CRUD + validation for ExtractionSchema objects.
Schemas are persisted as JSON files in SCHEMA_DIR.

In this design, schema fields are not just metadata. Each field instruction
acts as an extraction rule and AI prompt directive, so validation is stricter.
"""
from __future__ import annotations

import logging
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.exceptions import SchemaNotFoundError, SchemaValidationError
from backend.app.core.models import ExtractionSchema, SchemaField
from backend.app.utils.file_utils import load_json_file, new_id, save_json_file

logger = logging.getLogger(__name__)


class SchemaService:
    def __init__(self, schema_dir: Path | None = None) -> None:
        self._dir = Path(schema_dir or settings.SCHEMA_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── CRUD ─────────────────────────────────────────────────────────

    def create_schema(
        self,
        schema_name: str,
        fields: list[dict] | None = None,
        version: str = "1.0",
        description: str = "",
    ) -> ExtractionSchema:
        schema = ExtractionSchema(
            schema_id=new_id(),
            schema_name=schema_name,
            version=version,
            description=description,
            fields=[SchemaField(**f) for f in (fields or [])],
        )
        self._assign_orders(schema)

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        logger.info("Created schema '%s' id=%s", schema_name, schema.schema_id)
        return schema

    def load_schema(self, schema_id: str) -> ExtractionSchema:
        path = self._schema_path(schema_id)
        if not path.exists():
            raise SchemaNotFoundError(f"Schema not found: {schema_id}")
        data = load_json_file(path)
        return ExtractionSchema(**data)

    def save_schema(self, schema: ExtractionSchema) -> None:
        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        path = self._schema_path(schema.schema_id)
        save_json_file(schema.model_dump(), path)

    def list_schemas(self) -> list[dict]:
        schemas = []
        for p in self._dir.glob("*.json"):
            try:
                data = load_json_file(p)
                schemas.append(
                    {
                        "schema_id": data.get("schema_id"),
                        "schema_name": data.get("schema_name"),
                        "version": data.get("version"),
                        "description": data.get("description", ""),
                        "field_count": len(data.get("fields", [])),
                    }
                )
            except Exception:  # noqa: BLE001
                logger.warning("Could not read schema file: %s", p)
        return schemas

    def delete_schema(self, schema_id: str) -> None:
        path = self._schema_path(schema_id)
        if not path.exists():
            raise SchemaNotFoundError(schema_id)
        path.unlink()

    def upload_schema(self, data: dict) -> ExtractionSchema:
        """
        Import an externally-created schema dict.
        Assigns a new id if missing.
        """
        if "schema_id" not in data or not data["schema_id"]:
            data["schema_id"] = new_id()

        schema = ExtractionSchema(**data)
        self._assign_orders(schema)

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    # ── Metadata update ──────────────────────────────────────────────

    def update_metadata(
        self,
        schema_id: str,
        schema_name: str | None = None,
        version: str | None = None,
        description: str | None = None,
    ) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        if schema_name is not None:
            schema.schema_name = schema_name
        if version is not None:
            schema.version = version
        if description is not None:
            schema.description = description

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    # ── Field operations ─────────────────────────────────────────────

    def add_field(self, schema_id: str, field_data: dict) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        field_name = field_data.get("name", "")
        if any(f.name == field_name for f in schema.fields):
            raise SchemaValidationError(f"Field '{field_name}' already exists")

        field = SchemaField(**field_data)
        field.order = len(schema.fields)
        schema.fields.append(field)

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    def update_field(
        self,
        schema_id: str,
        field_name: str,
        field_data: dict,
    ) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        for i, existing_field in enumerate(schema.fields):
            if existing_field.name == field_name:
                merged = existing_field.model_dump()
                merged.update(field_data)

                new_name = merged.get("name", field_name)
                if new_name != field_name and any(
                    f.name == new_name for f in schema.fields
                ):
                    raise SchemaValidationError(f"Field '{new_name}' already exists")

                schema.fields[i] = SchemaField(**merged)

                errors = self.validate_schema(schema)
                if errors:
                    raise SchemaValidationError("; ".join(errors))

                self.save_schema(schema)
                return schema

        raise SchemaValidationError(f"Field '{field_name}' not found")

    def delete_field(self, schema_id: str, field_name: str) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        before = len(schema.fields)
        schema.fields = [f for f in schema.fields if f.name != field_name]

        if len(schema.fields) == before:
            raise SchemaValidationError(f"Field '{field_name}' not found")

        self._assign_orders(schema)

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    def reorder_fields(
        self,
        schema_id: str,
        field_order: list[str],
    ) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        name_to_field = {f.name: f for f in schema.fields}
        unknown = set(field_order) - set(name_to_field)
        if unknown:
            raise SchemaValidationError(f"Unknown fields: {sorted(unknown)}")

        reordered = [name_to_field[name] for name in field_order]

        mentioned = set(field_order)
        reordered += [f for f in schema.fields if f.name not in mentioned]

        self._assign_orders_list(reordered)
        schema.fields = reordered

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    def duplicate_field(
        self,
        schema_id: str,
        field_name: str,
        new_name: str,
    ) -> ExtractionSchema:
        schema = self.load_schema(schema_id)

        src = next((f for f in schema.fields if f.name == field_name), None)
        if src is None:
            raise SchemaValidationError(f"Field '{field_name}' not found")

        if any(f.name == new_name for f in schema.fields):
            raise SchemaValidationError(f"Field '{new_name}' already exists")

        dup = src.model_copy(update={"name": new_name, "order": len(schema.fields)})
        schema.fields.append(dup)

        errors = self.validate_schema(schema)
        if errors:
            raise SchemaValidationError("; ".join(errors))

        self.save_schema(schema)
        return schema

    # ── Validation ───────────────────────────────────────────────────

    def validate_schema(self, schema: ExtractionSchema | dict) -> list[str]:
        errors: list[str] = []

        if isinstance(schema, dict):
            try:
                schema = ExtractionSchema(**schema)
            except Exception as exc:
                return [str(exc)]

        if not schema.schema_name or not schema.schema_name.strip():
            errors.append("schema_name is required")

        if not schema.fields:
            errors.append("schema must have at least one field")

        names_seen: set[str] = set()

        for field in schema.fields:
            if not field.name or not field.name.strip():
                errors.append("All fields must have a name")
            elif field.name in names_seen:
                errors.append(f"Duplicate field name: {field.name}")
            else:
                names_seen.add(field.name)

            if not field.instruction or not field.instruction.strip():
                errors.append(f"Field '{field.name}' must have an instruction")

            alias_seen: set[str] = set()
            for alias in field.aliases:
                cleaned = alias.strip().lower()
                if not cleaned:
                    errors.append(f"Field '{field.name}' has an empty alias")
                elif cleaned in alias_seen:
                    errors.append(f"Field '{field.name}' has duplicate alias: {alias}")
                else:
                    alias_seen.add(cleaned)

            if field.order < 0:
                errors.append(f"Field '{field.name}' has invalid order: {field.order}")

            if field.normalization:
                if (
                    field.normalization.to_uppercase
                    and field.normalization.to_lowercase
                ):
                    errors.append(
                        f"Field '{field.name}' normalization cannot set both "
                        "to_uppercase and to_lowercase"
                    )

        return errors

    # ── Private helpers ──────────────────────────────────────────────

    def _schema_path(self, schema_id: str) -> Path:
        return self._dir / f"{schema_id}.json"

    @staticmethod
    def _assign_orders(schema: ExtractionSchema) -> None:
        for i, field in enumerate(schema.fields):
            field.order = i

    @staticmethod
    def _assign_orders_list(fields: list[SchemaField]) -> None:
        for i, field in enumerate(fields):
            field.order = i