"""
Schemas API - CRUD for extraction schemas
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db, Schema
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class SchemaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schema_definition: dict
    field_hints: Optional[dict] = {}
    is_template: bool = False


class SchemaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_definition: Optional[dict] = None
    field_hints: Optional[dict] = None


@router.post("/")
async def create_schema(payload: SchemaCreate, db: AsyncSession = Depends(get_db)):
    schema = Schema(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        schema_definition=payload.schema_definition,
        field_hints=payload.field_hints or {},
        is_template=payload.is_template,
    )
    db.add(schema)
    await db.commit()
    await db.refresh(schema)
    return _schema_to_dict(schema)


@router.get("/")
async def list_schemas(
    is_template: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Schema).order_by(Schema.created_at.desc())
    if is_template is not None:
        query = query.where(Schema.is_template == is_template)
    result = await db.execute(query)
    schemas = result.scalars().all()
    return [_schema_to_dict(s) for s in schemas]


@router.get("/{schema_id}")
async def get_schema(schema_id: str, db: AsyncSession = Depends(get_db)):
    schema = await _get_schema_or_404(schema_id, db)
    return _schema_to_dict(schema)


@router.put("/{schema_id}")
async def update_schema(schema_id: str, payload: SchemaUpdate, db: AsyncSession = Depends(get_db)):
    schema = await _get_schema_or_404(schema_id, db)
    if payload.name:
        schema.name = payload.name
    if payload.description is not None:
        schema.description = payload.description
    if payload.schema_definition:
        schema.schema_definition = payload.schema_definition
    if payload.field_hints is not None:
        schema.field_hints = payload.field_hints
    await db.commit()
    await db.refresh(schema)
    return _schema_to_dict(schema)


@router.delete("/{schema_id}")
async def delete_schema(schema_id: str, db: AsyncSession = Depends(get_db)):
    schema = await _get_schema_or_404(schema_id, db)
    await db.delete(schema)
    await db.commit()
    return {"message": "Schema deleted"}


@router.get("/templates/list")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Get built-in schema templates."""
    return SCHEMA_TEMPLATES


def _schema_to_dict(s: Schema) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "schema_definition": s.schema_definition,
        "field_hints": s.field_hints,
        "is_template": s.is_template,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


async def _get_schema_or_404(schema_id: str, db: AsyncSession) -> Schema:
    result = await db.execute(select(Schema).where(Schema.id == schema_id))
    schema = result.scalar_one_or_none()
    if not schema:
        raise HTTPException(404, f"Schema {schema_id} not found")
    return schema


SCHEMA_TEMPLATES = [
    {
        "name": "Invoice",
        "description": "Standard invoice extraction schema",
        "schema_definition": {
            "vendorInfo": {"companyName": "string", "address": "string", "phone": "string", "email": "string"},
            "invoiceInfo": {"invoiceNumber": "string", "invoiceDate": "date", "dueDate": "date", "poNumber": "string"},
            "billingInfo": {"billedTo": "string", "billingAddress": "string"},
            "lineItems": [{"description": "string", "quantity": "number", "unitPrice": "number", "total": "number"}],
            "totals": {"subtotal": "number", "tax": "number", "discount": "number", "totalAmount": "number"},
            "paymentInfo": {"paymentTerms": "string", "bankDetails": "string"},
        },
    },
    {
        "name": "Medical Report",
        "description": "Medical/clinical report extraction",
        "schema_definition": {
            "patientInfo": {"name": "string", "dob": "date", "patientId": "string", "gender": "string"},
            "encounterInfo": {"date": "date", "physician": "string", "facility": "string", "visitType": "string"},
            "diagnosis": [{"code": "string", "description": "string", "type": "string"}],
            "medications": [{"name": "string", "dosage": "string", "frequency": "string"}],
            "vitals": {"bloodPressure": "string", "heartRate": "number", "temperature": "number", "weight": "number"},
            "notes": "string",
        },
    },
    {
        "name": "Purchase Order",
        "description": "Purchase order / procurement document",
        "schema_definition": {
            "poNumber": "string",
            "orderDate": "date",
            "vendor": {"name": "string", "vendorId": "string", "contact": "string"},
            "shipTo": {"address": "string", "attention": "string"},
            "items": [{"itemCode": "string", "description": "string", "quantity": "number", "price": "number", "total": "number"}],
            "totals": {"subtotal": "number", "shippingCost": "number", "tax": "number", "grandTotal": "number"},
            "terms": "string",
            "approvedBy": "string",
        },
    },
    {
        "name": "Receipt",
        "description": "Retail / restaurant receipt",
        "schema_definition": {
            "merchant": {"name": "string", "address": "string", "phone": "string"},
            "transactionDate": "date",
            "transactionTime": "string",
            "items": [{"description": "string", "quantity": "number", "price": "number"}],
            "payment": {"subtotal": "number", "tax": "number", "tip": "number", "total": "number", "method": "string"},
            "receiptNumber": "string",
        },
    },
]
