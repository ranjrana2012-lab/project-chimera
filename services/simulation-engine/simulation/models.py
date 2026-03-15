from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ActionType(str, Enum):
    """Social action types from OASIS framework."""
    POST = "post"
    REPLY = "reply"
    RETWEET = "retweet"
    LIKE = "like"
    FOLLOW = "follow"
    QUOTE = "quote"


class SimulationConfig(BaseModel):
    """Configuration for simulation run."""
    agent_count: int = Field(default=10, ge=1, le=1000)
    simulation_rounds: int = Field(default=10, ge=1, le=100)
    scenario_description: str
    seed_documents: List[str]


class SimulationResult(BaseModel):
    """Results from a simulation run."""
    simulation_id: str
    status: str
    rounds_completed: int
    total_actions: int
    final_summary: str
