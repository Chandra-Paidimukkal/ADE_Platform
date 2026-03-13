"""
Jobs API - Monitor processing jobs and LLM provider management
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.database import get_db, ProcessingJob, JobStatus, LLMProviderConfig
from core.llm_router import get_llm_router, LLMRouter, PROVIDER_REGISTRY
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List processing jobs."""
    query = select(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(limit)
    if status:
        query = query.where(ProcessingJob.status == status)
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [_job_to_dict(j) for j in jobs]


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job status and details."""
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return _job_to_dict(job)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a queued job."""
    await db.execute(
        update(ProcessingJob)
        .where(ProcessingJob.id == job_id, ProcessingJob.status == JobStatus.QUEUED)
        .values(status=JobStatus.CANCELLED)
    )
    await db.commit()
    return {"message": "Job cancelled"}


# ─── LLM Provider Management ───────────────────────────────────────────────


class ProviderCreate(BaseModel):
    name: str
    provider_type: str
    config: dict
    is_default: bool = False


@router.get("/providers/list")
async def list_providers(llm: LLMRouter = Depends(get_llm_router)):
    """List all registered LLM providers."""
    return {
        "providers": llm.list_providers(),
        "available_types": list(PROVIDER_REGISTRY.keys()),
    }


@router.post("/providers/register")
async def register_provider(
    payload: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Register a new LLM provider dynamically."""
    if payload.provider_type not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider type. Available: {list(PROVIDER_REGISTRY.keys())}")

    # Save to database
    config = LLMProviderConfig(
        name=payload.name,
        provider_type=payload.provider_type,
        config=payload.config,
        is_default=payload.is_default,
    )

    # Check if exists
    existing = await db.execute(
        select(LLMProviderConfig).where(LLMProviderConfig.name == payload.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Provider '{payload.name}' already registered")

    db.add(config)
    await db.commit()

    # Register with live router
    llm.register_provider(payload.name, payload.provider_type, payload.config)
    if payload.is_default:
        llm.set_default(payload.name)

    return {"message": f"Provider '{payload.name}' registered", "providers": llm.list_providers()}


@router.delete("/providers/{name}")
async def remove_provider(
    name: str,
    db: AsyncSession = Depends(get_db),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Remove a registered provider."""
    result = await db.execute(
        select(LLMProviderConfig).where(LLMProviderConfig.name == name)
    )
    config = result.scalar_one_or_none()
    if config:
        await db.delete(config)
        await db.commit()

    if name in llm._providers:
        del llm._providers[name]
        if llm._default_provider == name:
            llm._default_provider = next(iter(llm._providers), None)

    return {"message": f"Provider '{name}' removed"}


@router.post("/providers/{name}/set-default")
async def set_default_provider(name: str, llm: LLMRouter = Depends(get_llm_router)):
    """Set the default LLM provider."""
    llm.set_default(name)
    return {"message": f"Default provider set to '{name}'"}


def _job_to_dict(j: ProcessingJob) -> dict:
    return {
        "id": j.id,
        "document_id": j.document_id,
        "schema_id": j.schema_id,
        "job_type": j.job_type,
        "status": j.status.value if j.status else None,
        "progress": j.progress,
        "total_items": j.total_items,
        "processed_items": j.processed_items,
        "result_ids": j.result_ids,
        "error_message": j.error_message,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
    }
