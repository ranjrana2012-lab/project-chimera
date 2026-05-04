# shared/models/health.py
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    """Health status of a service dependency."""
    status: str = Field(..., description="Dependency status: healthy, unhealthy, unknown")
    latency_ms: Optional[float] = Field(None, description="Latency to dependency in milliseconds")


class ModelInfo(BaseModel):
    """Information about loaded ML models."""
    loaded: bool = Field(..., description="Whether model is loaded")
    name: Optional[str] = Field(None, description="Model name/version")
    last_loaded: Optional[datetime] = Field(None, description="When model was loaded")


class HealthMetrics(BaseModel):
    """Service health metrics."""
    requests_total: int = Field(default=0, description="Total requests served")
    errors_total: int = Field(default=0, description="Total errors encountered")
    avg_latency_ms: float = Field(default=0.0, description="Average request latency")


class ReadinessResponse(BaseModel):
    """Service readiness response."""
    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Overall status: ready, not_ready")
    version: Optional[str] = Field(None, description="Service version")
    uptime: Optional[int] = Field(None, description="Service uptime in seconds")
    dependencies: Dict[str, DependencyHealth] = Field(default_factory=dict, description="Dependency health status")
    model_info: Optional[ModelInfo] = Field(None, description="ML model information")
    metrics: Optional[HealthMetrics] = Field(None, description="Service metrics")
