"""Dialogue generation routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

router = APIRouter()


class DialogueRequest(BaseModel):
    """Request for dialogue generation."""

    scene_context: dict = Field(..., description="Current scene context")
    dialogue_context: list = Field(default_factory=list, description="Recent dialogue")
    sentiment_vector: Optional[dict] = Field(None, description="Audience sentiment")


class DialogueResponse(BaseModel):
    """Response from dialogue generation."""

    proposed_lines: str = Field(..., description="Generated dialogue")
    stage_cues: list = Field(default_factory=list, description="Stage cues")
    metadata: dict = Field(default_factory=dict, description="Generation metadata")
    cached: bool = Field(default=False, description="From cache")
    latency_ms: float = Field(..., description="Generation latency")


@router.post("/generate", response_model=DialogueResponse)
async def generate_dialogue(request: DialogueRequest):
    """Generate dialogue for a scene."""
    from ....main import handler

    if not handler:
        raise HTTPException(status_code=503, detail="Handler not initialized")

    try:
        result = await handler.generate_dialogue(
            scene_context=request.scene_context,
            dialogue_context=request.dialogue_context,
            sentiment_vector=request.sentiment_vector,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke")
async def invoke(request: dict):
    """Standard skill invocation endpoint."""
    # Extract from standard skill format
    input_data = request.get("input", {})

    dialogue_request = DialogueRequest(
        scene_context=input_data.get("current_scene", {}),
        dialogue_context=input_data.get("dialogue_context", []),
        sentiment_vector=input_data.get("sentiment_vector"),
    )

    result = await generate_dialogue(dialogue_request)

    return {
        "output": {
            "proposed_lines": result.proposed_lines,
            "stage_cues": result.stage_cues,
            "metadata": result.metadata,
        },
        "cached": result.cached,
        "latency_ms": result.latency_ms,
    }
