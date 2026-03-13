"""
Documents API - Upload, parse, split, and manage documents.
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.database import get_db, Document, DocumentStatus, ProcessingJob, JobStatus
from core.parser import DocumentParser
from core.llm_router import get_llm_router, LLMRouter
from agents.pipeline import AgentOrchestrator, SchemaSuggestionAgent, SplitAgent
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Upload a single document for processing."""
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {content_type}. Allowed: PDF, PNG, JPEG")

    doc_id = str(uuid.uuid4())
    ext = ALLOWED_TYPES[content_type]
    filename = f"{doc_id}{ext}"
    file_path = UPLOAD_DIR / filename

    # Save file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 50MB.")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create document record
    doc = Document(
        id=doc_id,
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_type=content_type,
        file_size=len(content),
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Start background parsing
    background_tasks.add_task(parse_document_bg, doc_id, str(file_path), content_type, llm)

    return {
        "id": doc_id,
        "filename": file.filename,
        "size": len(content),
        "status": "pending",
        "message": "Document uploaded. Parsing started in background.",
    }


@router.post("/upload/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Upload multiple documents for batch processing."""
    results = []
    for file in files:
        try:
            result = await upload_document(file, background_tasks, db, llm)
            results.append({"file": file.filename, "status": "success", **result})
        except HTTPException as e:
            results.append({"file": file.filename, "status": "error", "error": e.detail})

    return {"uploaded": len([r for r in results if r["status"] == "success"]), "results": results}


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all documents."""
    query = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    if status:
        query = query.where(Document.status == status)
    result = await db.execute(query)
    docs = result.scalars().all()
    return [_doc_to_dict(d) for d in docs]


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get document details."""
    doc = await _get_doc_or_404(doc_id, db)
    return _doc_to_dict(doc, include_content=True)


@router.get("/{doc_id}/parsed")
async def get_parsed_content(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get parsed document structure."""
    doc = await _get_doc_or_404(doc_id, db)
    if not doc.parsed_content:
        raise HTTPException(404, "Document not yet parsed")
    return doc.parsed_content


@router.get("/{doc_id}/layout")
async def get_layout(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get document layout analysis."""
    doc = await _get_doc_or_404(doc_id, db)
    return doc.layout_data or {}


@router.post("/{doc_id}/split")
async def split_document(
    doc_id: str,
    split_config: dict = None,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Detect and apply document splitting."""
    doc = await _get_doc_or_404(doc_id, db)
    if not doc.parsed_content:
        raise HTTPException(400, "Document must be parsed before splitting")

    parser = DocumentParser()
    doc_text = parser.get_document_text(doc.parsed_content)
    
    agent = SplitAgent(llm)
    result = await agent.detect_splits(doc.parsed_content, doc_text)

    await db.execute(
        update(Document)
        .where(Document.id == doc_id)
        .values(split_segments=result, status=DocumentStatus.SPLIT)
    )
    await db.commit()
    return result


@router.post("/{doc_id}/suggest-schema")
async def suggest_schema_for_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """AI-powered schema suggestion based on document content."""
    doc = await _get_doc_or_404(doc_id, db)
    if not doc.parsed_content:
        raise HTTPException(400, "Document must be parsed first")

    parser = DocumentParser()
    doc_text = parser.get_document_text(doc.parsed_content)

    agent = SchemaSuggestionAgent(llm)
    suggestion = await agent.suggest_schema(doc_text, doc.parsed_content)
    return suggestion


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a document and its files."""
    doc = await _get_doc_or_404(doc_id, db)
    
    # Delete file
    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


async def parse_document_bg(doc_id: str, file_path: str, file_type: str, llm: LLMRouter):
    """Background task: parse document and analyze layout."""
    from core.database import AsyncSessionLocal
    from agents.pipeline import LayoutAgent

    async with AsyncSessionLocal() as db:
        try:
            await db.execute(
                update(Document).where(Document.id == doc_id).values(status=DocumentStatus.PARSING)
            )
            await db.commit()

            # Parse
            parser = DocumentParser()
            parsed = await parser.parse(file_path, file_type)
            parsed_dict = parsed.to_dict()
            doc_text = parser.get_document_text(parsed_dict)

            # Layout analysis
            layout_agent = LayoutAgent(llm)
            layout = await layout_agent.analyze_layout(parsed_dict, doc_text)

            await db.execute(
                update(Document)
                .where(Document.id == doc_id)
                .values(
                    parsed_content=parsed_dict,
                    layout_data=layout,
                    page_count=parsed.page_count,
                    status=DocumentStatus.PARSED,
                )
            )
            await db.commit()
            logger.info(f"Document {doc_id} parsed successfully")
        except Exception as e:
            logger.error(f"Parsing failed for {doc_id}: {e}")
            await db.execute(
                update(Document).where(Document.id == doc_id).values(status=DocumentStatus.ERROR)
            )
            await db.commit()


def _doc_to_dict(doc: Document, include_content: bool = False) -> dict:
    d = {
        "id": doc.id,
        "filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status.value if doc.status else None,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "has_layout": bool(doc.layout_data),
        "has_splits": bool(doc.split_segments),
    }
    if include_content:
        d["parsed_content"] = doc.parsed_content
        d["layout_data"] = doc.layout_data
        d["split_segments"] = doc.split_segments
    return d


async def _get_doc_or_404(doc_id: str, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, f"Document {doc_id} not found")
    return doc
