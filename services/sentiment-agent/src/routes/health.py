from fastapi import APIRouter

router = APIRouter()

@router.get("")
@router.get("/live")
async def liveness():
    return {"status": "healthy"}

@router.get("/ready")
async def readiness():
    return {"status": "ready"}
