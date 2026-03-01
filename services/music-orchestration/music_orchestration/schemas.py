from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class UseCase(str, Enum):
    MARKETING = "marketing"
    SHOW = "show"


class Role(str, Enum):
    SOCIAL_MEDIA_USER = "social_media_user"
    SHOW_OPERATOR = "show_operator"
    DEVELOPER = "developer"
    ADMIN = "admin"


class MusicRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=1000)
    use_case: UseCase
    duration_seconds: int = Field(..., ge=15, le=300)
    format: str = Field(default="mp3")

    # Optional structured overrides
    genre: str | None = Field(None, max_length=100)
    mood: str | None = Field(None, max_length=100)
    tempo: int | None = Field(None, ge=40, le=240)
    key_signature: str | None = Field(None, max_length=20)

    @property
    def cache_key(self) -> str:
        """Generate cache key from prompt and parameters"""
        import hashlib
        key_data = f"{self.prompt}:{self.use_case}:{self.duration_seconds}"
        if self.genre:
            key_data += f":genre={self.genre}"
        if self.mood:
            key_data += f":mood={self.mood}"
        if self.tempo:
            key_data += f":tempo={self.tempo}"
        return hashlib.sha256(key_data.encode()).hexdigest()


class MusicResponse(BaseModel):
    request_id: str
    music_id: str | None = None
    status: Literal["cached", "generating", "completed", "failed"]
    audio_url: str | None = None
    duration_seconds: int
    format: str
    was_cache_hit: bool
    estimated_completion: str | None = None


class GenerationProgress(BaseModel):
    request_id: str
    type: Literal["started", "progress", "completed", "failed"]
    progress: int | None = None  # 0-100
    stage: str | None = None
    eta_seconds: int | None = None
    error: str | None = None


class UserContext(BaseModel):
    service_name: str
    role: Role
    permissions: list[str]


class ModulationParams(BaseModel):
    tempo_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    brightness_delta: float = Field(default=0.0, ge=-0.5, le=0.5)
    volume_adjust_db: float = Field(default=0.0, ge=-10.0, le=10.0)


class SentimentScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    trend: Literal["rising", "falling", "stable"]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
