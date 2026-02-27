"""Request models for Sentiment Agent."""

from pydantic import BaseModel, Field
from typing import Optional, List


class SentimentAnalysisOptions(BaseModel):
    """Options for sentiment analysis.

    Attributes:
        include_emotions: Whether to include emotion detection
        include_trend: Whether to include trend analysis
        aggregation_window: Time window for aggregation in seconds
        min_confidence: Minimum confidence threshold (0.0-1.0)
    """
    include_emotions: Optional[bool] = Field(
        default=True,
        description="Whether to include emotion detection"
    )
    include_trend: Optional[bool] = Field(
        default=False,
        description="Whether to include trend analysis"
    )
    aggregation_window: Optional[int] = Field(
        default=60,
        ge=1,
        le=3600,
        description="Time window for aggregation in seconds"
    )
    min_confidence: Optional[float] = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "include_emotions": True,
                    "include_trend": False,
                    "aggregation_window": 60,
                    "min_confidence": 0.5
                }
            ]
        }
    }


class SentimentRequest(BaseModel):
    """Request for sentiment analysis.

    Attributes:
        text: Text to analyze (1-5000 characters)
        options: Analysis options
        request_id: Optional unique request identifier
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to analyze for sentiment"
    )
    options: Optional[SentimentAnalysisOptions] = Field(
        default_factory=SentimentAnalysisOptions,
        description="Analysis options"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracking"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I absolutely loved the performance! The actors were amazing and the set design was breathtaking.",
                    "options": {
                        "include_emotions": True,
                        "include_trend": False,
                        "aggregation_window": 60,
                        "min_confidence": 0.5
                    },
                    "request_id": "req-123456"
                },
                {
                    "text": "The show was disappointing. Long wait times and unclear communication.",
                    "options": {
                        "include_emotions": True,
                        "include_trend": False
                    }
                }
            ]
        }
    }


class SentimentBatchRequest(BaseModel):
    """Request for batch sentiment analysis.

    Attributes:
        texts: List of texts to analyze (1-100 texts)
        options: Analysis options
        request_id: Optional unique request identifier
    """
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of texts to analyze"
    )
    options: Optional[SentimentAnalysisOptions] = Field(
        default_factory=SentimentAnalysisOptions,
        description="Analysis options"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracking"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "texts": [
                        "Amazing performance!",
                        "Great show!",
                        "Loved every minute!"
                    ],
                    "options": {
                        "include_emotions": True,
                        "aggregation_window": 60
                    },
                    "request_id": "batch-123456"
                }
            ]
        }
    }
