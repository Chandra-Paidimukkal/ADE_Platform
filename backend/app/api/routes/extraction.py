"""
/extraction routes
  POST /extraction/run
  POST /extraction/run-batch
  POST /extraction/export/json
  POST /extraction/export/csv
  GET  /extraction/export/download/{filename}
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.exceptions import SchemaNotFoundError
from backend.app.core.llm_router import LLMRouter
from backend.app.schemas.api_models import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    ExportRequest,
    ExportResponse,
    ExtractionRequest,
    ExtractionResultResponse,
)
from backend.app.services.batch_service import BatchService
from backend.app.services.export_service import ExportService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.parse_service import ParseService
from backend.app.services.schema_service import SchemaService

router = APIRouter()
_parse_svc = ParseService()
_schema_svc = SchemaService()
_export_svc = ExportService()


def _make_extraction_service(ai_provider: str | None) -> ExtractionService:
    router_obj = LLMRouter(provider_name=ai_provider) if ai_provider else LLMRouter()
    return ExtractionService(router=router_obj)


def _make_batch_service(ai_provider: str | None) -> BatchService:
    extractor = _make_extraction_service(ai_provider)
    return BatchService(extraction_service=extractor)


@router.post("/run", response_model=ExtractionResultResponse)
def run_extraction(req: ExtractionRequest):
    pdf_path = Path(req.file_path)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found",
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    try:
        schema = _schema_svc.load_schema(req.schema_id)
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    doc = _parse_svc.parse_document(pdf_path)

    extractor = _make_extraction_service(req.ai_provider)
    result = extractor.extract(doc, schema, use_ai=req.use_ai)

    return ExtractionResultResponse(**result.to_dict())


@router.post("/run-batch", response_model=BatchExtractionResponse)
def run_batch_extraction(req: BatchExtractionRequest):
    folder = Path(req.folder_path)

    if not folder.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    if not folder.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided path is not a folder",
        )

    try:
        schema = _schema_svc.load_schema(req.schema_id)
    except SchemaNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    batch_svc = _make_batch_service(req.ai_provider)

    try:
        job = batch_svc.run_folder_batch(
            folder_path=folder,
            schema=schema,
            use_ai=req.use_ai,
            recursive=req.recursive,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch extraction failed: {exc}",
        ) from exc

    return BatchExtractionResponse(
        job_id=job.job_id,
        status=job.status,
        total_files=job.total_files,
        processed=job.processed,
        succeeded=job.succeeded,
        failed=job.failed,
        results=[ExtractionResultResponse(**r) for r in job.results],
    )


# ── Export ───────────────────────────────────────────────────────────

@router.post("/export/json", response_model=ExportResponse)
def export_json(req: ExportRequest):
    results = _resolve_results(req)
    path = _export_svc.export_json(results, output_path=req.output_path)
    return ExportResponse(path=str(path), records=len(results))


@router.post("/export/csv", response_model=ExportResponse)
def export_csv(req: ExportRequest):
    results = _resolve_results(req)
    path = _export_svc.export_csv(results, output_path=req.output_path)
    return ExportResponse(path=str(path), records=len(results))


@router.get("/export/download/{filename}")
def download_export(filename: str):
    path = Path(settings.OUTPUT_DIR) / filename
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return FileResponse(str(path), filename=filename)


# ── Helper ───────────────────────────────────────────────────────────

def _resolve_results(req: ExportRequest) -> list[dict]:
    if req.results:
        return req.results

    if req.job_id:
        # Use a fresh batch service just to read job store through the service API
        batch_svc = BatchService()
        job = batch_svc.get_job(req.job_id)
        if job:
            return job.results

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {req.job_id} not found",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Provide job_id or results",
    )