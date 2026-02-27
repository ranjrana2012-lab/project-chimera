"""Response models for SceneSpeak dialogue generation."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenerationResponse(BaseModel):
    """Response from dialogue generation.

    Attributes:
        request_id: Unique identifier for the generation request
        dialogue: Generated dialogue text
        character: Character name who spoke the dialogue
        sentiment_used: Actual sentiment value used in generation
        tokens: Number of tokens generated
        confidence: Confidence score (0.0-1.0)
        from_cache: Whether this response came from cache
        generation_time_ms: Time taken to generate in milliseconds
        model_version: Version of the model used
        timestamp: When the response was generated
    """
    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )
    dialogue: str = Field(
        ...,
        description="Generated dialogue text"
    )
    character: str = Field(
        ...,
        description="Character name"
    )
    sentiment_used: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment value used"
    )
    tokens: int = Field(
        ...,
        ge=0,
        description="Number of tokens generated"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    from_cache: bool = Field(
        ...,
        description="Response from cache"
    )
    generation_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Generation time in milliseconds"
    )
    model_version: str = Field(
        ...,
        description="Model version"
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
                    "dialogue": "Hello, my dear friend! What a lovely day it is!",
                    "character": "Alice",
                    "sentiment_used": 0.5,
                    "tokens": 15,
                    "confidence": 0.92,
                    "from_cache": False,
                    "generation_time_ms": 145.3,
                    "model_version": "scenespeak-v0.1.0",
                    "timestamp": "2026-02-27T10:30:00Z"
                }
            ]
        }
    }
