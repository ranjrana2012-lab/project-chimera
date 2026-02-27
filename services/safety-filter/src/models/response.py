"""Response models for Safety Filter service."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SafetyDecision(str, Enum):
    """Safety decision outcomes."""
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"
    WARN = "warn"


class CategoryScore(BaseModel):
    """Safety score for a specific category.

    Attributes:
        category: Content category
        score: Harm probability score (0.0-1.0)
        flagged: Whether the content was flagged for this category
        matched_terms: List of matched terms or patterns
    """
    category: str = Field(..., description="Content category")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Harm probability score"
    )
    flagged: bool = Field(
        ...,
        description="Whether content was flagged for this category"
    )
    matched_terms: List[str] = Field(
        default_factory=list,
        description="Matched terms or patterns"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "profanity",
                    "score": 0.85,
                    "flagged": True,
                    "matched_terms": ["damn", "hell"]
                },
                {
                    "category": "hate_speech",
                    "score": 0.05,
                    "flagged": False,
                    "matched_terms": []
                }
            ]
        }
    }


class FlaggedContent(BaseModel):
    """Details about flagged content.

    Attributes:
        category: Category of the flagged content
        text: The flagged text excerpt
        start_pos: Starting position in original text
        end_pos: Ending position in original text
        reason: Explanation of why it was flagged
        severity: Severity level (low, medium, high)
    """
    category: str = Field(..., description="Category of flagged content")
    text: str = Field(..., description="Flagged text excerpt")
    start_pos: int = Field(..., ge=0, description="Starting position in original text")
    end_pos: int = Field(..., ge=0, description="Ending position in original text")
    reason: str = Field(..., description="Explanation of why it was flagged")
    severity: str = Field(..., description="Severity level (low, medium, high)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "profanity",
                    "text": "damn it",
                    "start_pos": 10,
                    "end_pos": 17,
                    "reason": "Contains profanity",
                    "severity": "medium"
                }
            ]
        }
    }


class SafetyDetails(BaseModel):
    """Detailed safety analysis results.

    Attributes:
        word_filter_results: Results from word list filtering
        ml_filter_results: Results from ML-based classification
        category_scores: Scores for each checked category
        overall_confidence: Overall confidence in the decision
        applied_rules: List of policy rules that were applied
    """
    word_filter_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from word list filtering"
    )
    ml_filter_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from ML-based classification"
    )
    category_scores: List[CategoryScore] = Field(
        default_factory=list,
        description="Scores for each checked category"
    )
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the decision"
    )
    applied_rules: List[str] = Field(
        default_factory=list,
        description="Policy rules that were applied"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "word_filter_results": {
                        "matched_patterns": ["damn", "hell"],
                        "match_count": 2
                    },
                    "ml_filter_results": {
                        "model_version": "bert-safety-v0.1.0",
                        "primary_prediction": "profanity"
                    },
                    "category_scores": [
                        {
                            "category": "profanity",
                            "score": 0.85,
                            "flagged": True,
                            "matched_terms": ["damn", "hell"]
                        },
                        {
                            "category": "hate_speech",
                            "score": 0.05,
                            "flagged": False,
                            "matched_terms": []
                        }
                    ],
                    "overall_confidence": 0.85,
                    "applied_rules": ["block_profanity"]
                }
            ]
        }
    }


class SafetyCheckResponse(BaseModel):
    """Response from safety check.

    Attributes:
        request_id: Unique identifier for the request
        decision: Final safety decision (allow/block/flag/warn)
        safe: Boolean indicating if content is safe
        confidence: Confidence in the decision (0.0-1.0)
        details: Optional detailed analysis results
        flagged_content: Optional list of flagged content excerpts
        processing_time_ms: Processing time in milliseconds
        model_version: Version of the model used
        timestamp: Response timestamp
        explanation: Human-readable explanation of the decision
    """
    request_id: str = Field(..., description="Unique request identifier")
    decision: SafetyDecision = Field(..., description="Final safety decision")
    safe: bool = Field(..., description="Whether content is considered safe")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the decision"
    )
    details: Optional[SafetyDetails] = Field(
        default=None,
        description="Detailed analysis results"
    )
    flagged_content: Optional[List[FlaggedContent]] = Field(
        default=None,
        description="Flagged content excerpts"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Processing time in milliseconds"
    )
    model_version: str = Field(..., description="Model version used")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    explanation: str = Field(..., description="Human-readable explanation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req-123456",
                    "decision": "flag",
                    "safe": False,
                    "confidence": 0.85,
                    "details": {
                        "category_scores": [
                            {
                                "category": "profanity",
                                "score": 0.85,
                                "flagged": True,
                                "matched_terms": ["damn", "hell"]
                            }
                        ],
                        "overall_confidence": 0.85,
                        "applied_rules": ["flag_profanity"]
                    },
                    "flagged_content": [
                        {
                            "category": "profanity",
                            "text": "damn it",
                            "start_pos": 10,
                            "end_pos": 17,
                            "reason": "Contains profanity",
                            "severity": "medium"
                        }
                    ],
                    "processing_time_ms": 45.2,
                    "model_version": "safety-filter-v0.1.0",
                    "explanation": "Content flagged for profanity"
                }
            ]
        }
    }


class SafetyBatchResponse(BaseModel):
    """Response from batch safety check.

    Attributes:
        request_id: Unique identifier for the batch request
        results: List of individual safety check results
        aggregate: Aggregated statistics across all items
        total_processing_time_ms: Total processing time
        model_version: Version of the model used
        timestamp: Response timestamp
    """
    request_id: str = Field(..., description="Unique batch request identifier")
    results: List[SafetyCheckResponse] = Field(
        ...,
        description="Individual safety check results"
    )
    aggregate: Dict[str, Any] = Field(
        ...,
        description="Aggregated statistics"
    )
    total_processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Total processing time in milliseconds"
    )
    model_version: str = Field(..., description="Model version used")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "batch-123456",
                    "results": [
                        {
                            "request_id": "batch-123456-0",
                            "decision": "allow",
                            "safe": True,
                            "confidence": 0.95,
                            "processing_time_ms": 15.2,
                            "model_version": "safety-filter-v0.1.0",
                            "explanation": "Content is safe"
                        }
                    ],
                    "aggregate": {
                        "total_items": 3,
                        "safe_count": 2,
                        "flagged_count": 1,
                        "blocked_count": 0,
                        "average_confidence": 0.85
                    },
                    "total_processing_time_ms": 48.5,
                    "model_version": "safety-filter-v0.1.0"
                }
            ]
        }
    }


class PolicyResponse(BaseModel):
    """Response for policy operations.

    Attributes:
        rules: List of current policy rules
        default_action: Default action for unmatched content
        version: Policy version identifier
        last_updated: Last update timestamp
        active_rule_count: Number of active rules
    """
    rules: List[Dict[str, Any]] = Field(..., description="Current policy rules")
    default_action: str = Field(..., description="Default action")
    version: Optional[str] = Field(
        default=None,
        description="Policy version identifier"
    )
    last_updated: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    active_rule_count: int = Field(..., description="Number of active rules")

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
                    "version": "v1.0.0",
                    "last_updated": "2026-02-27T10:30:00Z",
                    "active_rule_count": 2
                }
            ]
        }
    }


class HealthCheckResponse(BaseModel):
    """Health check response.

    Attributes:
        status: Health status (healthy, degraded, unhealthy)
        version: Service version
        uptime_seconds: Service uptime in seconds
        model_loaded: Whether the ML model is loaded
        word_list_loaded: Whether the word list is loaded
        kafka_connected: Whether Kafka is connected
    """
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime")
    model_loaded: bool = Field(..., description="ML model loaded status")
    word_list_loaded: bool = Field(..., description="Word list loaded status")
    kafka_connected: bool = Field(default=True, description="Kafka connection status")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "0.1.0",
                    "uptime_seconds": 3600.5,
                    "model_loaded": True,
                    "word_list_loaded": True,
                    "kafka_connected": True
                }
            ]
        }
    }
