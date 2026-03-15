import pytest
from simulation.runner import SimulationRunner
from simulation.models import SimulationConfig
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter


@pytest.mark.asyncio
async def test_simulation_runner():
    """Test basic simulation execution."""
    generator = PersonaGenerator(seed=42)
    router = TieredLLMRouter(local_ratio=0.8)
    runner = SimulationRunner(generator, router)

    config = SimulationConfig(
        agent_count=5,
        simulation_rounds=3,
        scenario_description="Test scenario",
        seed_documents=["Test document"]
    )

    result = await runner.run_simulation(config)

    assert result.status == "completed"
    assert result.rounds_completed == 3
    assert result.total_actions == 15  # 5 agents * 3 rounds
    assert len(result.final_summary) > 0


@pytest.mark.asyncio
async def test_llm_router_stats():
    """Test LLM router statistics."""
    router = TieredLLMRouter(local_ratio=0.7)

    backends = [await router.route_decision() for _ in range(100)]

    stats = router.get_stats()

    assert stats["total_calls"] == 100
    # Allow variance due to randomness
    assert 60 <= stats["local_calls"] <= 80
