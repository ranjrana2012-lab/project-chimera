"""Skills API routes."""
from fastapi import APIRouter
from ..core.skill_registry import SkillRegistry
from ..models.skill import Skill

router = APIRouter(prefix="/v1/skills", tags=["skills"])

@router.get("", response_model=list[Skill])
async def list_skills():
    """List all registered skills."""
    # TODO: Implement
    return []

@router.get("/{skill_name}", response_model=Skill)
async def get_skill(skill_name: str):
    """Get a specific skill."""
    # TODO: Implement
    pass
