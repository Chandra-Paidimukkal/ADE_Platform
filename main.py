"""
ADE Platform – main entrypoint
Run: uvicorn main:app --reload  (from project root)
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import documents, extraction, jobs, schemas
from backend.app.api.routes import documents, schemas, extraction, jobs
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Schema-driven bulk PDF extraction platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────

app = FastAPI(title="ADE Platform", version="1.0.0")

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(schemas.router, prefix="/schemas", tags=["Schemas"])
app.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])


@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
