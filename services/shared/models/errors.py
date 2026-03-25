"""Shared error models for all Chimera services."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for Chimera services."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
    MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class StandardErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    stack_trace: Optional[str] = Field(None, description="Stack trace (development only)")
