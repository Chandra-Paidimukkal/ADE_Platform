from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.core.exceptions import SchemaNotFoundError, SchemaValidationError
from backend.app.schemas.api_models import (
    CreateSchemaRequest,
    MessageResponse,
    ReorderFieldsRequest,
    SchemaFieldRequest,
    SchemaResponse,
    UpdateSchemaMetaRequest,
    ValidateSchemaResponse,
)
from backend.app.services.schema_normalizer import SchemaNormalizer
from backend.app.services.schema_service import SchemaService

router = APIRouter()
_schema_svc = SchemaService()
_normalizer = SchemaNormalizer()


@router.post("/create", response_model=SchemaResponse)
def create_schema(req: CreateSchemaRequest):
    try:
        schema = _schema_svc.create_schema(
            schema_name=req.schema_name,
            fields=[f.model_dump() for f in req.fields],
            version=req.version,
            description=req.description,
        )
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/import", response_model=SchemaResponse)
def import_schema(body: dict):
    try:
        normalized = _normalizer.normalize(body)
        schema = _schema_svc.upload_schema(normalized.model_dump())
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema import failed: {exc}",
        ) from exc


@router.post("/upload", response_model=SchemaResponse)
def upload_schema(body: dict):
    try:
        schema = _schema_svc.upload_schema(body)
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[dict])
def list_schemas():
    return _schema_svc.list_schemas()


@router.get("/{schema_id}", response_model=SchemaResponse)
def get_schema(schema_id: str):
    try:
        schema = _schema_svc.load_schema(schema_id)
        return SchemaResponse(**schema.model_dump())
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/{schema_id}", response_model=SchemaResponse)
def update_schema_metadata(schema_id: str, req: UpdateSchemaMetaRequest):
    try:
        schema = _schema_svc.update_metadata(
            schema_id=schema_id,
            schema_name=req.schema_name,
            version=req.version,
            description=req.description,
        )
        return SchemaResponse(**schema.model_dump())
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete("/{schema_id}", response_model=MessageResponse)
def delete_schema(schema_id: str):
    try:
        _schema_svc.delete_schema(schema_id)
        return MessageResponse(message="Schema deleted successfully")
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{schema_id}/fields", response_model=SchemaResponse)
def add_field(schema_id: str, req: SchemaFieldRequest):
    try:
        schema = _schema_svc.add_field(schema_id, req.model_dump())
        return SchemaResponse(**schema.model_dump())
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.put("/{schema_id}/fields/{field_name}", response_model=SchemaResponse)
def update_field(schema_id: str, field_name: str, req: SchemaFieldRequest):
    try:
        schema = _schema_svc.update_field(schema_id, field_name, req.model_dump())
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete("/{schema_id}/fields/{field_name}", response_model=SchemaResponse)
def delete_field(schema_id: str, field_name: str):
    try:
        schema = _schema_svc.delete_field(schema_id, field_name)
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{schema_id}/reorder", response_model=SchemaResponse)
def reorder_fields(schema_id: str, req: ReorderFieldsRequest):
    try:
        schema = _schema_svc.reorder_fields(schema_id, req.field_order)
        return SchemaResponse(**schema.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{schema_id}/validate", response_model=ValidateSchemaResponse)
def validate_schema(schema_id: str):
    try:
        schema = _schema_svc.load_schema(schema_id)
        errors = _schema_svc.validate_schema(schema)
        return ValidateSchemaResponse(valid=(len(errors) == 0), errors=errors)
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc