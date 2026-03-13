from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    return {
        "documents_processed": 0,
        "models_detected": 0,
        "errors": 0
    }