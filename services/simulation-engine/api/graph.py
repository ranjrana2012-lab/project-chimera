from fastapi import APIRouter

router = APIRouter()


@router.post("/build")
async def build_graph():
    """Build knowledge graph from documents."""
    return {"status": "not_implemented"}
