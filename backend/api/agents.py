from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def agent_status():
    return {"status": "agent service running"}