"""Response models for BSL gloss translation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SignBreakdown(BaseModel):
    """Individual sign information in the breakdown.

    Attributes:
        gloss: The gloss notation for this sign
        english_source: Original English word/phrase
        handshape: Handshape description (if available)
        location: Sign location relative to body
        movement: Movement description
        non_manual: Non-manual markers (facial expressions, etc.)
        confidence: Confidence score for this sign (0.0-1.0)
    """
    gloss: str = Field(
        ...,
        description="Gloss notation for this sign"
    )
    english_source: str = Field(
        ...,
        description="Original English word or phrase"
    )
    handshape: Optional[str] = Field(
        default=None,
        description="Handshape description"
    )
    location: Optional[str] = Field(
        default=None,
        description="Sign location relative to body"
    )
    movement: Optional[str] = Field(
        default=None,
        description="Movement description"
    )
    non_manual: Optional[str] = Field(
        default=None,
        description="Non-manual markers (facial expressions, body posture)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this sign"
    )


class TranslationResponse(BaseModel):
    """Response from English-to-BSL gloss translation.

    Attributes:
        request_id: Unique identifier for the translation request
        gloss_text: Complete BSL gloss notation translation
        source_text: Original English text
        breakdown: Detailed breakdown of individual signs
        notations: Additional notation information
        language: Target language code (bsl)
        gloss_format: Format used for gloss notation
        confidence: Overall confidence score (0.0-1.0)
        translation_time_ms: Time taken for translation in milliseconds
        model_version: Version of the translation model
        timestamp: When the response was generated
    """
    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )
    gloss_text: str = Field(
        ...,
        description="Complete BSL gloss notation translation"
    )
    source_text: str = Field(
        ...,
        description="Original English text"
    )
    breakdown: List[SignBreakdown] = Field(
        default_factory=list,
        description="Detailed breakdown of individual signs"
    )
    notations: dict[str, str] = Field(
        default_factory=dict,
        description="Additional notation information (HamNoSys, Stokoe, etc.)"
    )
    language: str = Field(
        default="bsl",
        description="Target language code"
    )
    gloss_format: str = Field(
        default="hamnosys",
        description="Format used for gloss notation"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score"
    )
    translation_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Translation time in milliseconds"
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
                    "request_id": "req-bsl-123456",
                    "gloss_text": "HELLO HOW YOU",
                    "source_text": "Hello, how are you?",
                    "breakdown": [
                        {
                            "gloss": "HELLO",
                            "english_source": "Hello",
                            "handshape": "open hand",
                            "location": "forehead",
                            "movement": "away from body",
                            "non_manual": "friendly expression",
                            "confidence": 0.92
                        },
                        {
                            "gloss": "HOW",
                            "english_source": "how",
                            "handshape": "index finger",
                            "location": "chest",
                            "movement": "circular",
                            "non_manual": "questioning expression",
                            "confidence": 0.88
                        },
                        {
                            "gloss": "YOU",
                            "english_source": "you",
                            "handshape": "index finger",
                            "location": "pointing forward",
                            "movement": "none",
                            "non_manual": None,
                            "confidence": 0.95
                        }
                    ],
                    "notations": {
                        "hamnosys": "^ forearmback ^handback armclose palmup finger2...",
                        "simplified": "HELLO HOW YOU"
                    },
                    "language": "bsl",
                    "gloss_format": "hamnosys",
                    "confidence": 0.91,
                    "translation_time_ms": 156.8,
                    "model_version": "opus-mt-en-ROMANCE-bsl-v0.1.0",
                    "timestamp": "2026-02-27T10:30:00Z"
                }
            ]
        }
    }


class BatchTranslationResponse(BaseModel):
    """Response from batch English-to-BSL gloss translation.

    Attributes:
        request_id: Unique identifier for the batch request
        translations: List of translation responses
        total_count: Total number of translations
        successful_count: Number of successful translations
        failed_count: Number of failed translations
        total_time_ms: Total time for batch processing
        timestamp: When the response was generated
    """
    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )
    translations: List[TranslationResponse] = Field(
        ...,
        description="List of translation responses"
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of translations"
    )
    successful_count: int = Field(
        ...,
        ge=0,
        description="Number of successful translations"
    )
    failed_count: int = Field(
        ...,
        ge=0,
        description="Number of failed translations"
    )
    total_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Total time for batch processing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req-bsl-batch-789",
                    "translations": [
                        {
                            "request_id": "req-bsl-123456",
                            "gloss_text": "HELLO HOW YOU",
                            "source_text": "Hello, how are you?",
                            "breakdown": [],
                            "notations": {},
                            "language": "bsl",
                            "gloss_format": "hamnosys",
                            "confidence": 0.91,
                            "translation_time_ms": 156.8,
                            "model_version": "opus-mt-en-ROMANCE-bsl-v0.1.0",
                            "timestamp": "2026-02-27T10:30:00Z"
                        }
                    ],
                    "total_count": 3,
                    "successful_count": 3,
                    "failed_count": 0,
                    "total_time_ms": 456.2,
                    "timestamp": "2026-02-27T10:30:01Z"
                }
            ]
        }
    }
