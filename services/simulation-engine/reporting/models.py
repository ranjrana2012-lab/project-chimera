"""Data models for ForumEngine debate system."""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class Argument(BaseModel):
    """A single argument in a debate."""
    agent_id: str
    content: str
    stance: float  # -1.0 (oppose) to 1.0 (support)
    reasoning: str
    created_at: Optional[datetime] = None

    @field_validator('stance')
    @classmethod
    def clamp_stance(cls, v: float) -> float:
        """Ensure stance is within valid range [-1.0, 1.0]."""
        return max(-1.0, min(1.0, v))


class DebateResult(BaseModel):
    """Results from a multi-agent debate."""
    topic: str
    arguments: List[Argument]
    consensus_score: float  # 0-1, higher = more agreement
    confidence_interval: tuple[float, float]  # (lower, upper)
    summary: str
