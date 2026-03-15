from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.persona import PersonaGenerator

router = APIRouter()

generator = PersonaGenerator()


class GeneratePersonasRequest(BaseModel):
    count: int
    seed: int = None


@router.post("/generate")
async def generate_personas(request: GeneratePersonasRequest):
    """Generate agent personas for simulation."""
    if request.count < 1 or request.count > 1000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 1000")

    profiles = await generator.generate_population(
        count=request.count,
        diversity_config={}
    )

    return {
        "personas": [p.model_dump() for p in profiles],
        "count": len(profiles)
    }
