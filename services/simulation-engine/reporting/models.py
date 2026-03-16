"""Data models for ForumEngine debate system and ReACT ReportAgent."""
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
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


# ReACT ReportAgent Models

class SimulationAction(BaseModel):
    """A single action taken by an agent during simulation."""
    agent_id: str
    action_type: str  # "post", "reply", "like", etc.
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class SimulationRound(BaseModel):
    """A round of simulation containing multiple agent actions."""
    round_number: int
    actions: List[SimulationAction]
    agent_states: Dict[str, Any] = {}


class SimulationTrace(BaseModel):
    """Complete trace of a simulation run."""
    simulation_id: str
    topic: str
    rounds: List[SimulationRound]
    knowledge_graph_entities: List[str] = []
    knowledge_graph_relationships: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class ReportSection(BaseModel):
    """A section of a generated report."""
    title: str
    content: str
    confidence: float = 0.5  # 0-1
    sources: List[str] = []


class Report(BaseModel):
    """Complete simulation report with multiple sections."""
    simulation_id: str
    generated_at: datetime
    executive_summary: ReportSection
    findings: List[ReportSection]
    recommendations: List[ReportSection]
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    metadata: Dict[str, Any] = {}
