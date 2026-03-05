# models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    checks: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GenerateRequest(BaseModel):
    """Base generation request"""
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: Optional[int] = Field(500, ge=1, le=4096, description="Max tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class GenerateResponse(BaseModel):
    """Generation response"""
    text: str
    tokens_used: int
    model: str
    duration_ms: int
