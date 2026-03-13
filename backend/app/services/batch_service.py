"""
BatchService – runs extraction over many PDFs concurrently.
Captures per-file success/failure; never aborts the full batch.
"""
from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.enums import JobStatus
from backend.app.core.models import BatchJob, DocumentExtractionResult, ExtractionSchema
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.parse_service import ParseService

logger = logging.getLogger(__name__)

# In-memory job store (replace with Redis/DB for production)
_JOB_STORE: dict[str, BatchJob] = {}


class BatchService:
    def __init__(
        self,
        parse_service: ParseService | None = None,
        extraction_service: ExtractionService | None = None,
        max_workers: int | None = None,
    ) -> None:
        self._parser = parse_service or ParseService()
        self._extractor = extraction_service or ExtractionService()
        self._workers = max_workers or settings.BATCH_MAX_WORKERS

    # ── Public ───────────────────────────────────────────────────────

    def run_folder_batch(
        self,
        folder_path: str | Path,
        schema: ExtractionSchema,
        use_ai: bool = True,
        recursive: bool = False,
    ) -> BatchJob:
        folder = Path(folder_path)
        if recursive:
            pdfs = sorted([p for p in folder.rglob("*.pdf") if p.is_file()])
        else:
            pdfs = sorted([p for p in folder.glob("*.pdf") if p.is_file()])
        return self._run_batch(pdfs, schema, use_ai)

    def run_file_batch(
        self,
        file_paths: list[str | Path],
        schema: ExtractionSchema,
        use_ai: bool = True,
    ) -> BatchJob:
        pdfs = [Path(p) for p in file_paths if Path(p).suffix.lower() == ".pdf"]
        return self._run_batch(pdfs, schema, use_ai)

    def get_job(self, job_id: str) -> BatchJob | None:
        return _JOB_STORE.get(job_id)

    def aggregate_results(self, job: BatchJob) -> dict:
        """Merge all per-file result dicts into a summary structure."""
        return {
            "job_id": job.job_id,
            "status": job.status,
            "total": job.total_files,
            "processed": job.processed,
            "succeeded": job.succeeded,
            "failed": job.failed,
            "progress_pct": job.progress_pct,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "errors": job.errors,
            "results": job.results,
        }

    # ── Private ──────────────────────────────────────────────────────

    def _run_batch(
        self,
        pdf_paths: list[Path],
        schema: ExtractionSchema,
        use_ai: bool,
    ) -> BatchJob:
        job = BatchJob(
            job_id=str(uuid.uuid4()),
            total_files=len(pdf_paths),
            status=JobStatus.running.value,
            started_at=_now(),
        )
        _JOB_STORE[job.job_id] = job

        logger.info("Batch job %s started – %d files", job.job_id, len(pdf_paths))

        if not pdf_paths:
            job.status = JobStatus.failed.value
            job.completed_at = _now()
            job.errors.append("No PDF files found to process")
            logger.warning("Batch job %s failed – no PDF files found", job.job_id)
            return job

        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            futures = {
                pool.submit(self._process_one, pdf_path, schema, use_ai): pdf_path
                for pdf_path in pdf_paths
            }

            for future in as_completed(futures):
                pdf_path = futures[future]

                try:
                    # as_completed already yields completed futures,
                    # so no extra timeout is necessary here.
                    result: DocumentExtractionResult = future.result()

                    job.results.append(result.to_dict())

                    if result.status.value == "failed":
                        job.failed += 1
                    else:
                        job.succeeded += 1

                except Exception as exc:  # noqa: BLE001
                    logger.error("Unhandled error for %s: %s", pdf_path.name, exc)
                    job.failed += 1
                    job.errors.append(f"{pdf_path.name}: {exc}")
                    job.results.append(
                        {
                            "file": pdf_path.name,
                            "status": "failed",
                            "data": {},
                            "errors": [str(exc)],
                            "warnings": [],
                            "metadata": {},
                            "field_sources": {},
                            "field_details": {},
                        }
                    )
                finally:
                    job.processed += 1

        # Final status resolution
        if job.failed == job.total_files:
            job.status = JobStatus.failed.value
        elif job.failed > 0:
            # if your enum does not contain partial_success, add it there
            job.status = getattr(JobStatus, "partial_success", JobStatus.completed).value
        else:
            job.status = JobStatus.completed.value

        job.completed_at = _now()

        logger.info(
            "Batch job %s done – %d succeeded / %d failed / status=%s",
            job.job_id,
            job.succeeded,
            job.failed,
            job.status,
        )

        return job

    def _process_one(
        self,
        pdf_path: Path,
        schema: ExtractionSchema,
        use_ai: bool,
    ) -> DocumentExtractionResult:
        doc = self._parser.parse_document(pdf_path)
        result = self._extractor.extract(doc, schema, use_ai=use_ai)
        return result


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()