from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def catalog_status():
    return {"status": "catalog service running"}