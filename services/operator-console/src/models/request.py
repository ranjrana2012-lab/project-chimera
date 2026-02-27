"""Request models for Operator Console."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OverrideType(str, Enum):
    """Types of manual overrides."""

    EMERGENCY_STOP = "emergency_stop"
    CONTENT_REPLACE = "content_replace"
    SERVICE_PAUSE = "service_pause"
    GENERATION_SKIP = "generation_skip"


class OverrideRequest(BaseModel):
    """Request for manual override."""

    override_type: OverrideType = Field(..., description="Type of override to perform")
    target_service: str = Field(..., description="Service to apply override to")
    reason: str = Field(..., description="Reason for override")
    parameter: Optional[dict] = Field(None, description="Optional override parameters")


class ApprovalStatus(str, Enum):
    """Approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Request for content approval."""

    request_id: str = Field(..., description="Unique request identifier")
    source_service: str = Field(..., description="Service requesting approval")
    content_type: str = Field(..., description="Type of content (script, lighting, etc)")
    content_preview: str = Field(..., description="Preview of content to approve")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    priority: str = Field(default="normal", description="Priority level")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class ApprovalResponse(BaseModel):
    """Response to approval request."""

    request_id: str = Field(..., description="Request being responded to")
    status: ApprovalStatus = Field(..., description="Approval decision")
    reason: Optional[str] = Field(None, description="Reason for decision")
    approved_by: str = Field(..., description="Operator who made decision")
    modifications: Optional[dict] = Field(None, description="Any approved modifications")
