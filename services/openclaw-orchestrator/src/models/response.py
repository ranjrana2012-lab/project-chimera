"""Response models."""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    """Execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class OrchestrationResponse(BaseModel):
    """Response from orchestration."""
    request_id: str
    status: Status
    results: Dict[str, Any]
    execution_time_ms: float
    gpu_used: bool
    errors: Optional[Dict[str, str]] = None


class SkillResponse(BaseModel):
    """Response from a single skill."""
    skill: str
    status: Status
    output: Dict[str, Any]
    execution_time_ms: float
    error: Optional[str] = None
