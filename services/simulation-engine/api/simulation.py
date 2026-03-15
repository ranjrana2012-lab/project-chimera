from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from simulation.runner import SimulationRunner
from simulation.models import SimulationConfig
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter

router = APIRouter()

runner = None


@router.post("/simulate")
async def run_simulation(config: SimulationConfig):
    """Run a simulation with the given configuration."""
    if runner is None:
        raise HTTPException(status_code=503, detail="Simulation service not initialized")

    result = await runner.run_simulation(config)

    return {
        "simulation_id": result.simulation_id,
        "status": result.status,
        "rounds_completed": result.rounds_completed,
        "total_actions": result.total_actions,
        "summary": result.final_summary
    }
