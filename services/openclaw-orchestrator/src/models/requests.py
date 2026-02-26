"""Request models for OpenClaw Orchestrator API"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SkillInvokeRequest(BaseModel):
    """Request to invoke a single skill."""

    skill_name: str = Field(..., description="Name of the skill to invoke")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input data for the skill")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional configuration override"
    )
    timeout_ms: Optional[int] = Field(
        default=3000, description="Timeout in milliseconds"
    )


class PipelineStep(BaseModel):
    """A single step in a pipeline."""

    skill_name: str = Field(..., description="Name of the skill to invoke")
    input_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Map output keys from previous steps to this step's input"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional configuration override"
    )
    condition: Optional[str] = Field(
        default=None, description="Conditional expression to execute this step"
    )


class PipelineExecuteRequest(BaseModel):
    """Request to execute a pipeline."""

    pipeline_id: Optional[str] = Field(
        default=None, description="Pre-defined pipeline ID"
    )
    steps: Optional[List[PipelineStep]] = Field(
        default=None, description="Pipeline steps (if not using pre-defined pipeline)"
    )
    input: Dict[str, Any] = Field(default_factory=dict, description="Initial input data")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional pipeline configuration"
    )
    parallel: bool = Field(default=False, description="Execute steps in parallel")
    timeout_ms: int = Field(default=10000, description="Pipeline timeout in milliseconds")


class SkillListRequest(BaseModel):
    """Request to list available skills."""

    category: Optional[str] = Field(default=None, description="Filter by category")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    enabled_only: bool = Field(default=True, description="Return only enabled skills")
