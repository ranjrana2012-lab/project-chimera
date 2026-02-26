"""Skill management routes for OpenClaw Orchestrator"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from ...models.requests import SkillListRequest
from ...models.responses import SkillListResponse, SkillMetadata
from ...core.skill_registry import SkillRegistry
from ...config import Settings

router = APIRouter()


async def get_skill_registry() -> SkillRegistry:
    """Dependency to get skill registry instance."""
    from ....main import skill_registry
    return skill_registry  # type: ignore


@router.get("", response_model=SkillListResponse)
async def list_skills(
    category: str | None = None,
    tags: str | None = None,
    enabled_only: bool = True,
    skill_registry: SkillRegistry = Depends(get_skill_registry)
) -> SkillListResponse:
    """
    List available skills.

    Returns a list of all available skills, optionally filtered by category or tags.
    """
    try:
        tag_list = tags.split(",") if tags else None
        skills = await skill_registry.list_skills(
            category=category,
            tags=tag_list,
            enabled_only=enabled_only
        )

        categories = await skill_registry.list_categories()

        return SkillListResponse(
            skills=skills,
            total=len(skills),
            categories=categories
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}"
        )


@router.get("/{skill_name}", response_model=SkillMetadata)
async def get_skill(
    skill_name: str,
    skill_registry: SkillRegistry = Depends(get_skill_registry)
) -> SkillMetadata:
    """
    Get metadata for a specific skill.

    Returns detailed metadata about the specified skill.
    """
    try:
        skill = await skill_registry.get_skill(skill_name)
        return skill
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {skill_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(e)}"
        )


@router.post("/{skill_name}/enable", status_code=status.HTTP_204_NO_CONTENT)
async def enable_skill(
    skill_name: str,
    skill_registry: SkillRegistry = Depends(get_skill_registry)
) -> None:
    """Enable a skill."""
    try:
        await skill_registry.enable_skill(skill_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {skill_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable skill: {str(e)}"
        )


@router.post("/{skill_name}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_skill(
    skill_name: str,
    skill_registry: SkillRegistry = Depends(get_skill_registry)
) -> None:
    """Disable a skill."""
    try:
        await skill_registry.disable_skill(skill_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {skill_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable skill: {str(e)}"
        )


@router.post("/reload", status_code=status.HTTP_204_NO_CONTENT)
async def reload_skills(
    skill_registry: SkillRegistry = Depends(get_skill_registry)
) -> None:
    """Reload all skills from disk."""
    try:
        await skill_registry.reload_skills()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload skills: {str(e)}"
        )
