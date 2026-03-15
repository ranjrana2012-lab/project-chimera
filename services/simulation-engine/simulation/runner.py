import asyncio
import uuid
from typing import List
from datetime import datetime
import logging

from simulation.models import SimulationConfig, SimulationResult, ActionType
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter

logger = logging.getLogger(__name__)


class SimulationRunner:
    """OASIS-inspired simulation orchestrator."""

    def __init__(
        self,
        persona_generator: PersonaGenerator,
        llm_router: TieredLLMRouter
    ):
        self.persona_generator = persona_generator
        self.llm_router = llm_router

    async def run_simulation(
        self,
        config: SimulationConfig
    ) -> SimulationResult:
        """Execute simulation rounds."""
        simulation_id = str(uuid.uuid4())
        logger.info(f"Starting simulation {simulation_id}")

        # Generate agent personas
        agents = await self.persona_generator.generate_population(
            count=config.agent_count
        )

        logger.info(f"Generated {len(agents)} agents")

        # Run simulation rounds
        total_actions = 0
        actions_log = []

        for round_num in range(config.simulation_rounds):
            logger.info(f"Round {round_num + 1}/{config.simulation_rounds}")

            round_actions = await self._run_round(agents, round_num)
            total_actions += len(round_actions)
            actions_log.extend(round_actions)

        # Generate summary
        summary = await self._generate_summary(
            config,
            agents,
            actions_log
        )

        # Log routing stats
        stats = self.llm_router.get_stats()
        logger.info(f"LLM routing stats: {stats}")

        return SimulationResult(
            simulation_id=simulation_id,
            status="completed",
            rounds_completed=config.simulation_rounds,
            total_actions=total_actions,
            final_summary=summary
        )

    async def _run_round(self, agents: List, round_num: int) -> List[dict]:
        """Execute a single simulation round."""
        actions = []

        for agent in agents:
            # Determine which LLM to use
            backend = await self.llm_router.route_decision(
                context=f"Agent {agent.id} making decision"
            )

            # For Phase 0, simulate action without actual LLM call
            action = {
                "agent_id": agent.id,
                "round": round_num,
                "action_type": ActionType.POST.value,
                "backend_used": backend.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            actions.append(action)

        return actions

    async def _generate_summary(
        self,
        config: SimulationConfig,
        agents: List,
        actions: List[dict]
    ) -> str:
        """Generate simulation summary."""
        return f"""
Simulation Summary
==================
Scenario: {config.scenario_description}
Agents: {len(agents)}
Rounds: {config.simulation_rounds}
Total Actions: {len(actions)}

This is a Phase 0 placeholder summary.
Phase 1 will use ReACT ReportAgent for detailed analysis.
        """.strip()
