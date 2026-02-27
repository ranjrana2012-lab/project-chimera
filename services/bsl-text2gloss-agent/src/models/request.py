"""Request models for BSL gloss translation."""

from pydantic import BaseModel, Field
from typing import Optional


class TranslationRequest(BaseModel):
    """Request for English-to-BSL gloss translation.

    Attributes:
        text: English text to translate (1-5000 characters)
        source_lang: Source language code (default: 'en')
        gloss_format: Output gloss notation format (default: 'hamnosys')
        include_breakdown: Include detailed sign breakdown (default: true)
        normalize: Apply text normalization before translation (default: true)
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="English text to translate to BSL gloss"
    )
    source_lang: Optional[str] = Field(
        default="en",
        description="Source language code (ISO 639-1)"
    )
    gloss_format: Optional[str] = Field(
        default="hamnosys",
        description="Gloss notation format: hamnosys, stokoe, or simplified"
    )
    include_breakdown: Optional[bool] = Field(
        default=True,
        description="Include detailed sign breakdown in response"
    )
    normalize: Optional[bool] = Field(
        default=True,
        description="Apply text normalization before translation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Hello, how are you today?",
                    "source_lang": "en",
                    "gloss_format": "hamnosys",
                    "include_breakdown": True,
                    "normalize": True
                },
                {
                    "text": "The weather is beautiful.",
                    "source_lang": "en",
                    "gloss_format": "simplified",
                    "include_breakdown": False,
                    "normalize": True
                }
            ]
        }
    }


class BatchTranslationRequest(BaseModel):
    """Request for batch English-to-BSL gloss translation.

    Attributes:
        texts: List of English texts to translate (1-100 items)
        source_lang: Source language code (default: 'en')
        gloss_format: Output gloss notation format (default: 'hamnosys')
        include_breakdown: Include detailed sign breakdown (default: true)
        normalize: Apply text normalization before translation (default: true)
    """
    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of English texts to translate"
    )
    source_lang: Optional[str] = Field(
        default="en",
        description="Source language code (ISO 639-1)"
    )
    gloss_format: Optional[str] = Field(
        default="hamnosys",
        description="Gloss notation format"
    )
    include_breakdown: Optional[bool] = Field(
        default=True,
        description="Include detailed sign breakdown"
    )
    normalize: Optional[bool] = Field(
        default=True,
        description="Apply text normalization"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "texts": [
                        "Hello, how are you?",
                        "The weather is beautiful.",
                        "I am learning sign language."
                    ],
                    "source_lang": "en",
                    "gloss_format": "hamnosys",
                    "include_breakdown": True,
                    "normalize": True
                }
            ]
        }
    }
