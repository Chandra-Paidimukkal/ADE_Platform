"""
Database - SQLite with SQLAlchemy async ORM
Stores documents, schemas, extraction results, and processing jobs.
"""

import uuid
from datetime import datetime
from typing import Optional, Any, AsyncGenerator

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


DATABASE_URL = "sqlite+aiosqlite:///./docextract.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    SPLITTING = "splitting"
    SPLIT = "split"
    ERROR = "error"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.PENDING)
    page_count = Column(Integer, nullable=True)
    parsed_content = Column(JSON, nullable=True)
    layout_data = Column(JSON, nullable=True)
    split_segments = Column(JSON, nullable=True)
    doc_meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    extractions = relationship("ExtractionResult", back_populates="document", cascade="all, delete")
    jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete")


class Schema(Base):
    __tablename__ = "schemas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=False)
    field_hints = Column(JSON, default=dict)  # Optional extraction hints per field
    is_template = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    extractions = relationship("ExtractionResult", back_populates="schema")


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    schema_id = Column(String, ForeignKey("schemas.id"), nullable=False)
    extracted_data = Column(JSON, nullable=True)
    confidence_scores = Column(JSON, nullable=True)  # Per-field confidence
    validation_errors = Column(JSON, default=list)
    validation_passed = Column(Boolean, default=False)
    provider_used = Column(String, nullable=True)
    segment_index = Column(Integer, default=0)  # For split documents
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="extractions")
    schema = relationship("Schema", back_populates="extractions")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    schema_id = Column(String, nullable=True)
    job_type = Column(String, nullable=False)  # parse, extract, batch, etc.
    status = Column(SAEnum(JobStatus), default=JobStatus.QUEUED)
    progress = Column(Float, default=0.0)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    result_ids = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="jobs")


class LLMProviderConfig(Base):
    __tablename__ = "llm_provider_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    provider_type = Column(String, nullable=False)
    config = Column(JSON, nullable=False)  # Stored encrypted in production
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
