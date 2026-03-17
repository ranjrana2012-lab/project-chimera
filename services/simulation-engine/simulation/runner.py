import asyncio
import uuid
import time
from typing import List, Optional, Tuple
from datetime import datetime
import logging

from simulation.models import SimulationConfig, SimulationResult, ActionType
from agents.persona import PersonaGenerator
from agents.profile import AgentProfile
from simulation.llm_router import TieredLLMRouter
from graph.models import Graph

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
        start_time = time.time()
        logger.info(f"Starting simulation {simulation_id}")

        # Generate agent personas
        agents = await self.persona_generator.generate_population(
            count=config.agent_count
        )

        logger.info(f"Generated {len(agents)} agents")

        # Run simulation rounds
        total_actions = 0
        action_log = []

        for round_num in range(config.simulation_rounds):
            logger.info(f"Round {round_num + 1}/{config.simulation_rounds}")

            round_actions = await self._run_round(agents, round_num)
            total_actions += len(round_actions)
            action_log.append(round_actions)

        # Generate summary
        summary = await self._generate_summary(
            config,
            agents,
            [action for round_actions in action_log for action in round_actions]
        )

        # Log routing stats
        stats = self.llm_router.get_stats()
        logger.info(f"LLM routing stats: {stats}")

        return SimulationResult(
            simulation_id=simulation_id,
            status="completed",
            rounds_completed=config.simulation_rounds,
            total_actions=total_actions,
            final_summary=summary,
            action_log=action_log,
            start_time=start_time
        )

    async def run_simulation_with_report(
        self,
        agents: List[AgentProfile],
        knowledge_graph: Graph,
        config: SimulationConfig
    ) -> Tuple[SimulationResult, Optional["ComprehensiveReport"]]:
        """Run simulation and optionally generate comprehensive report"""

        # Run simulation
        result = await self.run_simulation(config)

        # Generate report if requested
        if config.generate_report:
            from ..reporting.orchestrator import ReportOrchestrator

            # Build simulation trace from result
            trace = self._build_trace(result, knowledge_graph)

            # Generate comprehensive report
            orchestrator = ReportOrchestrator()
            report = await orchestrator.generate_report(trace)

            return result, report

        return result, None

    def _build_trace(
        self,
        result: SimulationResult,
        knowledge_graph: Graph
    ) -> "SimulationTrace":
        """Build SimulationTrace from SimulationResult"""
        from ..reporting.models import SimulationTrace, SimulationRound, SimulationAction
        from datetime import datetime

        rounds_data = []
        for round_actions in result.action_log:
            actions = [
                SimulationAction(
                    agent_id=action["agent_id"],
                    action_type=action["action_type"],
                    content=action.get("content", ""),
                    timestamp=datetime.fromtimestamp(action.get("timestamp", time.time()))
                )
                for action in round_actions
            ]
            rounds_data.append(SimulationRound(
                round_number=len(rounds_data),
                actions=actions
            ))

        return SimulationTrace(
            simulation_id=result.simulation_id,
            topic=getattr(result, 'scenario_topic', "Simulation"),
            rounds=rounds_data,
            knowledge_graph_entities=[e.id for e in knowledge_graph.entities],
            knowledge_graph_relationships=[
                f"{r.source}-{r.type}->{r.target}"
                for r in knowledge_graph.relationships
            ],
            started_at=datetime.fromtimestamp(result.start_time),
            completed_at=datetime.now()
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
