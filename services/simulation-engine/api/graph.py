from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.neo4j_client import Neo4jClient
from graph.builder import GraphBuilder

router = APIRouter()

client = None
builder = None


class GraphBuildRequest(BaseModel):
    documents: list[str]


class GraphBuildResponse(BaseModel):
    graph_id: str
    entities: int
    relationships: int


@router.post("/build", response_model=GraphBuildResponse)
async def build_graph(request: GraphBuildRequest):
    """Build knowledge graph from documents."""
    if builder is None:
        raise HTTPException(status_code=503, detail="Graph service not initialized")

    result = await builder.build_from_documents(request.documents)

    return GraphBuildResponse(
        graph_id="temp_graph_1",
        entities=result["entities"],
        relationships=result["relationships"]
    )
