"""
/jobs routes – query async batch job status
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.api_models import JobResponse
from backend.app.services.batch_service import _JOB_STORE

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Job '{job_id}' not found")
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        total_files=job.total_files,
        processed=job.processed,
        succeeded=job.succeeded,
        failed=job.failed,
        progress_pct=job.progress_pct,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/", response_model=list[JobResponse])
def list_jobs():
    return [
        JobResponse(
            job_id=j.job_id,
            status=j.status,
            total_files=j.total_files,
            processed=j.processed,
            succeeded=j.succeeded,
            failed=j.failed,
            progress_pct=j.progress_pct,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )
        for j in _JOB_STORE.values()
    ]
