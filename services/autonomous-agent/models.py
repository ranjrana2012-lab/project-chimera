"""Pydantic models for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "autonomous-agent"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskRequest(BaseModel):
    """Request to execute a task."""

    user_request: str = Field(..., description="Natural language description of the task")
    requirements: Optional[List[str]] = Field(default_factory=list, description="Additional requirements")
    timeout: Optional[int] = Field(default=3600, description="Max execution time in seconds")


class TaskResponse(BaseModel):
    """Response from task execution."""

    task_id: str
    status: str  # pending, in_progress, complete, failed
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StatusResponse(BaseModel):
    """Current autonomous agent status."""

    current_task: Optional[str] = None
    completed_tasks: List[str] = Field(default_factory=list)
    pending_tasks: List[str] = Field(default_factory=list)
    retry_count: int = 0
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RalphModeConfig(BaseModel):
    """Ralph Mode configuration."""

    max_retries: int = Field(default=5, ge=1, le=10)
    retry_delay_seconds: int = Field(default=10, ge=1, le=300)


class ExecuteResponse(BaseModel):
    """Response from full execution."""

    task_id: str
    phases_completed: List[str]
    requirements: Dict[str, str]
    plan_tasks: List[str]
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    status: str
