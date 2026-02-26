"""Response models for OpenClaw Orchestrator API"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    components: Dict[str, str] = Field(
        default_factory=dict, description="Health status of components"
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict, description="Health status of dependencies"
    )


class SkillMetadata(BaseModel):
    """Metadata about a skill."""

    name: str = Field(..., description="Skill name")
    version: str = Field(..., description="Skill version")
    description: str = Field(..., description="Skill description")
    category: str = Field(..., description="Skill category")
    enabled: bool = Field(..., description="Whether the skill is enabled")
    timeout_ms: int = Field(..., description="Default timeout in milliseconds")
    cache_enabled: bool = Field(..., description="Whether caching is enabled")
    cache_ttl_seconds: int = Field(..., description="Cache TTL in seconds")
    inputs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Input schema"
    )
    outputs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Output schema"
    )
    tags: List[str] = Field(default_factory=list, description="Skill tags")


class SkillInvokeResponse(BaseModel):
    """Response from skill invocation."""

    skill_name: str = Field(..., description="Invoked skill name")
    success: bool = Field(..., description="Whether invocation was successful")
    output: Dict[str, Any] = Field(default_factory=dict, description="Skill output data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Invocation metadata"
    )
    latency_ms: float = Field(..., description="Invocation latency in milliseconds")
    cached: bool = Field(default=False, description="Whether result was from cache")


class PipelineStepResult(BaseModel):
    """Result of a single pipeline step."""

    step_number: int = Field(..., description="Step number in pipeline")
    skill_name: str = Field(..., description="Skill name")
    success: bool = Field(..., description="Whether step was successful")
    output: Dict[str, Any] = Field(default_factory=dict, description="Step output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency_ms: float = Field(..., description="Step latency in milliseconds")


class PipelineExecuteResponse(BaseModel):
    """Response from pipeline execution."""

    pipeline_id: Optional[str] = Field(
        default=None, description="Pipeline ID if pre-defined"
    )
    success: bool = Field(..., description="Whether pipeline was successful")
    output: Dict[str, Any] = Field(
        default_factory=dict, description="Final pipeline output"
    )
    steps: List[PipelineStepResult] = Field(
        default_factory=list, description="Results from each step"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata"
    )
    total_latency_ms: float = Field(..., description="Total pipeline latency")


class SkillListResponse(BaseModel):
    """Response listing available skills."""

    skills: List[SkillMetadata] = Field(
        default_factory=list, description="List of available skills"
    )
    total: int = Field(..., description="Total number of skills")
    categories: List[str] = Field(
        default_factory=list, description="Available skill categories"
    )


class PipelineStatus(BaseModel):
    """Status of a running pipeline."""

    pipeline_id: str = Field(..., description="Pipeline ID")
    status: str = Field(
        ..., description="Status: pending, running, completed, failed"
    )
    current_step: Optional[int] = Field(
        default=None, description="Current step number"
    )
    total_steps: int = Field(..., description="Total number of steps")
    started_at: str = Field(..., description="Pipeline start time (ISO 8601)")
    completed_at: Optional[str] = Field(
        default=None, description="Pipeline completion time (ISO 8601)"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
