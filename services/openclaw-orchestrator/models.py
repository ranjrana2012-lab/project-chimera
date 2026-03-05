from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class OrchestrateRequest(BaseModel):
    skill: str = Field(..., description="Name of skill to invoke")
    input: Dict[str, Any] = Field(..., description="Skill-specific input data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class OrchestrateResponse(BaseModel):
    result: Dict[str, Any]
    skill_used: str
    execution_time: float
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    checks: Optional[Dict[str, bool]] = None
