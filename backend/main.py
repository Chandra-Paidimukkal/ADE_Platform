from fastapi import FastAPI

from api import documents, extraction, agents, dashboard, catalog

app = FastAPI(title="DocExtract Platform")

app.include_router(documents.router, prefix="/api/v1/documents")
app.include_router(extraction.router, prefix="/api/v1/extraction")
app.include_router(agents.router, prefix="/api/v1/agents")
app.include_router(dashboard.router, prefix="/api/v1/dashboard")
app.include_router(catalog.router, prefix="/api/v1/catalog")


@app.get("/")
def root():
    return {"status": "DocExtract backend running"}