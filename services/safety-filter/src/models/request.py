"""Request models for Safety Filter service."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class StrictnessLevel(str, Enum):
    """Strictness levels for safety filtering."""
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    STRICT = "strict"


class ContentCategory(str, Enum):
    """Content categories to check."""
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    SEXUAL_CONTENT = "sexual_content"
    VIOLENCE = "violence"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"
    SPAM = "spam"


class SafetyCheckOptions(BaseModel):
    """Options for safety check.

    Attributes:
        categories: List of content categories to check (default: all)
        strictness: Strictness level for filtering (default: moderate)
        include_details: Whether to include detailed analysis (default: True)
        include_flagged_content: Whether to include flagged content excerpts (default: False)
        context: Optional context for better classification (e.g., "chat", "post")
    """
    categories: Optional[List[ContentCategory]] = Field(
        default_factory=lambda: list(ContentCategory),
        description="Content categories to check"
    )
    strictness: Optional[StrictnessLevel] = Field(
        default=StrictnessLevel.MODERATE,
        description="Strictness level for filtering"
    )
    include_details: Optional[bool] = Field(
        default=True,
        description="Whether to include detailed analysis"
    )
    include_flagged_content: Optional[bool] = Field(
        default=False,
        description="Whether to include flagged content excerpts"
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional context for better classification"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "categories": ["profanity", "hate_speech", "violence"],
                    "strictness": "moderate",
                    "include_details": True,
                    "include_flagged_content": False,
                    "context": "chat"
                },
                {
                    "categories": ["profanity"],
                    "strictness": "strict",
                    "include_details": True,
                    "include_flagged_content": True
                }
            ]
        }
    }


class SafetyCheckRequest(BaseModel):
    """Request for safety check.

    Attributes:
        content: Text content to check (1-10000 characters)
        options: Analysis options
        request_id: Optional unique request identifier for tracking
        user_id: Optional user identifier for audit logging
        source: Optional source identifier (e.g., "chat", "comment", "post")
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text content to check for safety"
    )
    options: Optional[SafetyCheckOptions] = Field(
        default_factory=SafetyCheckOptions,
        description="Analysis options"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracking"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for audit logging"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source identifier (e.g., 'chat', 'comment', 'post')"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "This is a sample message to check for safety.",
                    "options": {
                        "categories": ["profanity", "hate_speech"],
                        "strictness": "moderate",
                        "include_details": True
                    },
                    "request_id": "req-123456",
                    "user_id": "user-789",
                    "source": "chat"
                },
                {
                    "content": "Another message with different content.",
                    "options": {
                        "strictness": "strict"
                    }
                }
            ]
        }
    }


class PolicyRule(BaseModel):
    """A single policy rule.

    Attributes:
        name: Rule name/identifier
        category: Content category this applies to
        action: Action to take (allow, block, flag, warn)
        threshold: Confidence threshold for triggering (0.0-1.0)
        enabled: Whether the rule is enabled
        conditions: Optional conditions for rule application
    """
    name: str = Field(..., description="Rule name/identifier")
    category: ContentCategory = Field(..., description="Content category")
    action: str = Field(..., description="Action to take: allow, block, flag, warn")
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for triggering"
    )
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional conditions for rule application"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "block_profanity",
                    "category": "profanity",
                    "action": "block",
                    "threshold": 0.8,
                    "enabled": True
                },
                {
                    "name": "flag_hate_speech",
                    "category": "hate_speech",
                    "action": "flag",
                    "threshold": 0.7,
                    "enabled": True,
                    "conditions": {"min_severity": "high"}
                }
            ]
        }
    }


class PolicyUpdateRequest(BaseModel):
    """Request to update safety policies.

    Attributes:
        rules: List of policy rules to set
        default_action: Default action when no rules match
        version: Optional policy version identifier
    """
    rules: List[PolicyRule] = Field(..., description="Policy rules to set")
    default_action: str = Field(
        default="flag",
        description="Default action when no rules match"
    )
    version: Optional[str] = Field(
        default=None,
        description="Policy version identifier"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rules": [
                        {
                            "name": "block_profanity",
                            "category": "profanity",
                            "action": "block",
                            "threshold": 0.8,
                            "enabled": True
                        },
                        {
                            "name": "flag_hate_speech",
                            "category": "hate_speech",
                            "action": "flag",
                            "threshold": 0.7,
                            "enabled": True
                        }
                    ],
                    "default_action": "flag",
                    "version": "v1.0.0"
                }
            ]
        }
    }


class SafetyBatchRequest(BaseModel):
    """Request for batch safety check.

    Attributes:
        contents: List of content strings to check (1-100 items)
        options: Analysis options (applied to all items)
        request_id: Optional unique request identifier
    """
    contents: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of content strings to check"
    )
    options: Optional[SafetyCheckOptions] = Field(
        default_factory=SafetyCheckOptions,
        description="Analysis options (applied to all items)"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracking"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contents": [
                        "First message to check",
                        "Second message to check",
                        "Third message to check"
                    ],
                    "options": {
                        "strictness": "moderate",
                        "include_details": True
                    },
                    "request_id": "batch-123456"
                }
            ]
        }
    }
