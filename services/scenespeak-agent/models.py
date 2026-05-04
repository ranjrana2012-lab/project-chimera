"""
Pydantic models for SceneSpeak Agent.

Defines request/response models for dialogue generation with GLM 4.7 API integration
and local LLM fallback support.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Request for dialogue generation"""
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: Optional[int] = Field(500, ge=1, le=4096, description="Max tokens")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    context: Optional[dict] = Field(None, description="Additional context")


class DialogueResponse(BaseModel):
    """Response from dialogue generation"""
    text: str
    tokens_used: int
    model: str
    source: str  # "api" or "local"
    duration_ms: int


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    loaded: bool
    version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response"""
    model_config = {"protected_namespaces": ()}

    status: str
    service: str
    model_available: bool
    local_llm_available: Optional[bool] = None
    glm_api_available: Optional[bool] = None
    model_info: Optional[ModelInfo] = None
