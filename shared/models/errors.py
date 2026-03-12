# shared/models/errors.py
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class StandardErrorResponse(BaseModel):
    """Standard error response format for all Project Chimera services."""

    error: str = Field(..., description="Human readable error message")
    code: str = Field(..., description="Machine-readable error code")
    detail: Optional[str] = Field(None, description="Additional error context")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    retryable: bool = Field(
        default=False,
        description="Whether the request can be retried"
    )


# Error code constants
class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    SAFETY_REJECTED = "SAFETY_REJECTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
