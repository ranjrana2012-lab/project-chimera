"""Response models for Sentiment Agent."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .context import GlobalContext


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EmotionScores(BaseModel):
    """Emotion detection scores.

    Attributes:
        joy: Joy/happiness score (0.0-1.0)
        sadness: Sadness score (0.0-1.0)
        anger: Anger score (0.0-1.0)
        fear: Fear score (0.0-1.0)
        surprise: Surprise score (0.0-1.0)
        disgust: Disgust score (0.0-1.0)
    """
    joy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Joy/happiness score"
    )
    sadness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Sadness score"
    )
    anger: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Anger score"
    )
    fear: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fear score"
    )
    surprise: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Surprise score"
    )
    disgust: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Disgust score"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "joy": 0.85,
                    "sadness": 0.05,
                    "anger": 0.02,
                    "fear": 0.03,
                    "surprise": 0.30,
                    "disgust": 0.01
                }
            ]
        }
    }


class SentimentScore(BaseModel):
    """Detailed sentiment score.

    Attributes:
        label: Sentiment classification (positive/negative/neutral)
        confidence: Confidence score (0.0-1.0)
        positive_score: Raw positive score (0.0-1.0)
        negative_score: Raw negative score (0.0-1.0)
    """
    label: SentimentLabel = Field(
        ...,
        description="Sentiment classification"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    positive_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw positive score"
    )
    negative_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw negative score"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "label": "positive",
                    "confidence": 0.95,
                    "positive_score": 0.98,
                    "negative_score": 0.02
                }
            ]
        }
    }


class TrendDataPoint(BaseModel):
    """Single data point in a trend analysis.

    Attributes:
        timestamp: Timestamp of the data point
        score: Average sentiment score (-1.0 to 1.0)
        count: Number of samples aggregated
    """
    timestamp: datetime = Field(
        ...,
        description="Timestamp of the data point"
    )
    score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Average sentiment score"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of samples aggregated"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "timestamp": "2026-02-27T10:30:00Z",
                    "score": 0.75,
                    "count": 15
                }
            ]
        }
    }


class SentimentTrend(BaseModel):
    """Sentiment trend analysis.

    Attributes:
        current_score: Current average sentiment score
        direction: Trend direction (rising/falling/stable)
        change_percent: Percentage change from previous period
        data_points: Historical data points
    """
    current_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Current average sentiment score"
    )
    direction: str = Field(
        ...,
        description="Trend direction (rising/falling/stable)"
    )
    change_percent: float = Field(
        ...,
        description="Percentage change from previous period"
    )
    data_points: List[TrendDataPoint] = Field(
        default_factory=list,
        description="Historical data points"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_score": 0.65,
                    "direction": "rising",
                    "change_percent": 12.5,
                    "data_points": [
                        {
                            "timestamp": "2026-02-27T10:25:00Z",
                            "score": 0.58,
                            "count": 12
                        },
                        {
                            "timestamp": "2026-02-27T10:30:00Z",
                            "score": 0.65,
                            "count": 15
                        }
                    ]
                }
            ]
        }
    }


class SentimentResponse(BaseModel):
    """Response from sentiment analysis.

    Attributes:
        request_id: Unique identifier for the request
        text: Original text analyzed
        sentiment: Sentiment score details
        emotions: Optional emotion detection scores
        trend: Optional trend analysis
        context: Optional global context from WorldMonitor
        processing_time_ms: Processing time in milliseconds
        model_version: Version of the model used
        timestamp: Response timestamp
    """
    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )
    text: str = Field(
        ...,
        description="Original text analyzed"
    )
    sentiment: SentimentScore = Field(
        ...,
        description="Sentiment score details"
    )
    emotions: Optional[EmotionScores] = Field(
        default=None,
        description="Emotion detection scores"
    )
    trend: Optional[SentimentTrend] = Field(
        default=None,
        description="Trend analysis"
    )
    context: Optional[GlobalContext] = Field(
        default=None,
        description="Global context from WorldMonitor"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Processing time in milliseconds"
    )
    model_version: str = Field(
        ...,
        description="Model version used"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req-123456",
                    "text": "I absolutely loved the performance!",
                    "sentiment": {
                        "label": "positive",
                        "confidence": 0.98,
                        "positive_score": 0.99,
                        "negative_score": 0.01
                    },
                    "emotions": {
                        "joy": 0.92,
                        "sadness": 0.05,
                        "anger": 0.02,
                        "fear": 0.01,
                        "surprise": 0.35,
                        "disgust": 0.01
                    },
                    "trend": None,
                    "processing_time_ms": 45.2,
                    "model_version": "distilbert-sst-2-v0.1.0",
                    "timestamp": "2026-02-27T10:30:00Z"
                }
            ]
        }
    }


class SentimentBatchResponse(BaseModel):
    """Response from batch sentiment analysis.

    Attributes:
        request_id: Unique identifier for the batch request
        results: List of individual sentiment results
        aggregate: Aggregated sentiment across all texts
        total_processing_time_ms: Total processing time
        model_version: Version of the model used
        timestamp: Response timestamp
    """
    request_id: str = Field(
        ...,
        description="Unique batch request identifier"
    )
    results: List[SentimentResponse] = Field(
        ...,
        description="Individual sentiment analysis results"
    )
    aggregate: Dict[str, Any] = Field(
        ...,
        description="Aggregated sentiment statistics"
    )
    total_processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Total processing time in milliseconds"
    )
    model_version: str = Field(
        ...,
        description="Model version used"
    )
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
                            "text": "Amazing!",
                            "sentiment": {
                                "label": "positive",
                                "confidence": 0.95,
                                "positive_score": 0.97,
                                "negative_score": 0.03
                            },
                            "emotions": {
                                "joy": 0.88,
                                "sadness": 0.05,
                                "anger": 0.02,
                                "fear": 0.01,
                                "surprise": 0.25,
                                "disgust": 0.01
                            },
                            "processing_time_ms": 15.2,
                            "model_version": "distilbert-sst-2-v0.1.0"
                        }
                    ],
                    "aggregate": {
                        "overall_label": "positive",
                        "average_confidence": 0.95,
                        "positive_count": 3,
                        "negative_count": 0,
                        "neutral_count": 0,
                        "average_score": 0.85
                    },
                    "total_processing_time_ms": 48.5,
                    "model_version": "distilbert-sst-2-v0.1.0",
                    "timestamp": "2026-02-27T10:30:00Z"
                }
            ]
        }
    }
