"""Data models for ForumEngine debate system."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Argument(BaseModel):
    """A single argument in a debate."""
    agent_id: str
    content: str
    stance: float  # -1.0 (oppose) to 1.0 (support)
    reasoning: str
    created_at: Optional[datetime] = None


class DebateResult(BaseModel):
    """Results from a multi-agent debate."""
    topic: str
    arguments: List[Argument]
    consensus_score: float  # 0-1, higher = more agreement
    confidence_interval: tuple[float, float]  # (lower, upper)
    summary: str
