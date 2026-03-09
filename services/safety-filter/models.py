"""
Pydantic models for Safety Filter.

Defines request/response models for content moderation and safety checks.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ModerationLevel(str, Enum):
    """Content moderation severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FilterAction(str, Enum):
    """Actions that can be taken on filtered content"""
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"
    MODIFY = "modify"


class FilterLayer(str, Enum):
    """Safety filter layers"""
    PATTERN = "pattern"
    CLASSIFICATION = "classification"
    CONTEXT = "context"


class ModerateRequest(BaseModel):
    """Request for content moderation"""
    content: str = Field(..., min_length=1, description="Content to moderate")
    content_id: Optional[str] = Field(None, description="Optional content identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    policy: Optional[str] = Field("family", description="Moderation policy to apply")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class MatchedPattern(BaseModel):
    """Details of a matched pattern"""
    pattern: str
    type: str  # profanity, pii, harmful, etc.
    severity: ModerationLevel
    position: Optional[int] = None


class ModerationResult(BaseModel):
    """Result from content moderation"""
    is_safe: bool
    action: FilterAction
    level: ModerationLevel
    confidence: float
    layer: FilterLayer
    reason: str
    matched_patterns: List[MatchedPattern] = []
    processing_time_ms: float
    content_id: Optional[str] = None


class ModerateResponse(BaseModel):
    """Response from moderation endpoint"""
    safe: bool
    result: ModerationResult


class CheckRequest(BaseModel):
    """Request for quick safety check"""
    content: str = Field(..., min_length=1, description="Content to check")
    policy: Optional[str] = Field("family", description="Policy to use for check")


class CheckResponse(BaseModel):
    """Response from quick safety check"""
    safe: bool
    confidence: float
    reason: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    loaded: bool
    version: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    moderator_ready: bool
    policy: Optional[str] = None
    model_info: Optional[ModelInfo] = None


class PolicyInfo(BaseModel):
    """Information about a moderation policy"""
    name: str
    description: str
    level: ModerationLevel
    pattern_count: int


# API-compatible models for /api/moderate endpoint

class APIModerateRequest(BaseModel):
    """Request for /api/moderate endpoint"""
    text: str = Field(..., min_length=1, description="Text content to moderate")
    threshold: Optional[float] = Field(0.5, ge=0, le=1, description="Safety threshold (0-1)")
    categories: Optional[List[str]] = Field(None, description="Specific categories to check")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for awareness")


class CategoryScores(BaseModel):
    """Category scores for moderation result"""
    violence: float = 0.0
    hate: float = 0.0
    sexual: float = 0.0
    self_harm: float = 0.0
    harassment: float = 0.0


class ModerationMetadata(BaseModel):
    """Metadata for moderation result"""
    model: str = "safety-filter-v1"
    latency_ms: float
    policy: str = "family"
    timestamp: str


class APIModerateResponse(BaseModel):
    """Response from /api/moderate endpoint"""
    safe: bool
    confidence: float
    categories: CategoryScores
    flagged_reason: Optional[str] = None
    metadata: ModerationMetadata
