from fastapi import APIRouter

router = APIRouter()


@router.post("/simulate")
async def run_simulation():
    """Run simulation."""
    return {"status": "not_implemented"}
