from pydantic import BaseModel, Field


class GenerationParams(BaseModel):
    duration_seconds: int = Field(..., ge=15, le=300)
    format: str = Field(default="wav")
    sample_rate: int = Field(default=44100)
