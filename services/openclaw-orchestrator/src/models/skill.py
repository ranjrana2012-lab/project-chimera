"""Skill data models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Skill(BaseModel):
    """Represents a registered skill."""

    name: str
    version: str
    endpoint: str
    timeout: int = Field(default=5000, ge=100, le=60000)
    gpu_required: bool = False
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillHealth(BaseModel):
    """Skill health status."""

    name: str
    healthy: bool
    last_check: str
    error_message: Optional[str] = None
