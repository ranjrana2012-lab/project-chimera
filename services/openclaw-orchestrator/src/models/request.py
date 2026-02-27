"""Request models."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class OrchestrationRequest(BaseModel):
    """Request for orchestration."""
    skills: List[str]
    input_data: Dict[str, Any]
    priority: Optional[int] = Field(default=100, ge=1, le=1000)
    timeout: Optional[int] = Field(default=30, ge=1, le=300)
    gpu_required: Optional[bool] = False
    request_id: Optional[str] = None


class SkillRequest(BaseModel):
    """Request to a single skill."""
    skill: str
    input_data: Dict[str, Any]
    timeout: int = 5000
