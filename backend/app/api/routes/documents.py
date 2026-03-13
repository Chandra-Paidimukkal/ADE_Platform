"""
/documents routes
  POST /documents/parse
  POST /documents/parse-batch
  POST /documents/upload          (multipart – single file)
  POST /documents/upload-batch    (multipart – multiple files)
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.schemas.api_models import (
    MessageResponse,
    ParseBatchRequest,
    ParseRequest,
    ParsedDocumentResponse,
    ParsedPageResponse,
)
from backend.app.services.parse_service import ParseService

router = APIRouter()
_parse_svc = ParseService()

# configurable later if needed
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def _to_response(doc) -> ParsedDocumentResponse:
    return ParsedDocumentResponse(
        file_name=doc.file_name,
        file_path=doc.file_path,
        page_count=doc.page_count,
        full_text=doc.full_text[:5000],   # truncate for API response
        parse_error=doc.parse_error,
        pages=[
            ParsedPageResponse(
                page_number=p.page_number,
                text=p.text[:2000],
                table_count=len(p.tables),
            )
            for p in doc.pages
        ],
    )


def _is_pdf_filename(filename: str | None) -> bool:
    return bool(filename and filename.lower().endswith(".pdf"))


def _safe_pdf_name(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def _save_upload(upload: UploadFile) -> Path:
    if not _is_pdf_filename(upload.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    pdf_dir = Path(settings.PDF_DIR)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_pdf_name(upload.filename or "file.pdf")
    dest = pdf_dir / safe_name

    total = 0
    with open(dest, "wb") as fh:
        while True:
            chunk = await upload.read(1024 * 1024)  # 1 MB
            if not chunk:
                break

            total += len(chunk)
            if total > MAX_UPLOAD_SIZE_BYTES:
                fh.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max allowed size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
                )

            fh.write(chunk)

    await upload.close()
    return dest


@router.post(
    "/parse",
    response_model=ParsedDocumentResponse,
    summary="Parse a single PDF from a local path",
)
def parse_document(req: ParseRequest):
    path = Path(req.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {req.file_path}",
        )

    if path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    doc = _parse_svc.parse_document(path)
    if doc.parse_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=doc.parse_error,
        )
    return _to_response(doc)


@router.post(
    "/parse-batch",
    response_model=list[ParsedDocumentResponse],
    summary="Parse all PDFs in a local folder",
)
def parse_batch(req: ParseBatchRequest):
    folder = Path(req.folder_path)
    if not folder.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Folder not found: {req.folder_path}",
        )

    docs = _parse_svc.parse_batch(folder)
    return [_to_response(d) for d in docs]


@router.post(
    "/upload",
    response_model=ParsedDocumentResponse,
    summary="Upload and parse a single PDF",
)
async def upload_document(file: UploadFile = File(...)):
    dest = await _save_upload(file)
    doc = _parse_svc.parse_document(dest)

    if doc.parse_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=doc.parse_error,
        )

    return _to_response(doc)


@router.post(
    "/upload-batch",
    response_model=list[ParsedDocumentResponse],
    summary="Upload and parse multiple PDFs",
)
async def upload_batch(files: list[UploadFile] = File(...)):
    results: list[ParsedDocumentResponse] = []

    for upload in files:
        if not _is_pdf_filename(upload.filename):
            continue

        try:
            dest = await _save_upload(upload)
            doc = _parse_svc.parse_document(dest)
            results.append(_to_response(doc))
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            results.append(
                ParsedDocumentResponse(
                    file_name=upload.filename or "unknown.pdf",
                    file_path="",
                    page_count=0,
                    full_text="",
                    parse_error=str(exc),
                    pages=[],
                )
            )

    return results