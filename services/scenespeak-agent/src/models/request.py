"""Request models for SceneSpeak dialogue generation."""
from pydantic import BaseModel, Field
from typing import Optional


class GenerationRequest(BaseModel):
    """Request for dialogue generation.

    Attributes:
        context: Scene context description (1-1000 characters)
        character: Character name who will speak
        sentiment: Sentiment value from -1.0 (negative) to 1.0 (positive)
        max_tokens: Maximum tokens to generate (1-1024)
        temperature: Sampling temperature (0.0-2.0, higher = more random)
        top_p: Nucleus sampling threshold (0.0-1.0)
        use_cache: Whether to use cached responses if available
    """
    context: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Scene context"
    )
    character: str = Field(
        ...,
        description="Character name"
    )
    sentiment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Sentiment -1.0 to 1.0"
    )
    max_tokens: Optional[int] = Field(
        default=256,
        ge=1,
        le=1024,
        description="Maximum tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    top_p: Optional[float] = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    use_cache: Optional[bool] = Field(
        default=True,
        description="Whether to use cached responses"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "context": "A sunny garden with blooming flowers",
                    "character": "Alice",
                    "sentiment": 0.5,
                    "max_tokens": 256,
                    "temperature": 0.8,
                    "top_p": 0.95,
                    "use_cache": True
                }
            ]
        }
    }
