"""Shared health check models for all Chimera services."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ReadinessResponse(BaseModel):
    """Readiness check response with component status."""
    status: str = Field(..., description="Overall readiness status: ready, not_ready")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Component readiness checks")
    model_info: Optional[ModelInfo] = Field(None, description="Information about ML models used by this service")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelInfo(BaseModel):
    """Information about ML models used by a service."""
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    provider: str = Field(default="local", description="Model provider: local, huggingface, openai, etc.")
    parameters: Optional[int] = Field(None, description="Number of model parameters")
    quantization: Optional[str] = Field(None, description="Model quantization: fp32, fp16, int8, etc.")
    loaded: bool = Field(default=False, description="Whether model is loaded in memory")
    load_time_ms: Optional[float] = Field(None, description="Time taken to load model in milliseconds")


class HealthMetrics(BaseModel):
    """Health metrics for monitoring."""
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    requests_total: int = Field(default=0, description="Total number of requests processed")
    requests_failed: int = Field(default=0, description="Total number of failed requests")
    avg_latency_ms: float = Field(default=0.0, description="Average request latency in milliseconds")
    memory_usage_mb: float = Field(..., description="Current memory usage in MB")
    cpu_usage_percent: float = Field(..., description="Current CPU usage percentage")
    last_check: datetime = Field(default_factory=datetime.utcnow)
