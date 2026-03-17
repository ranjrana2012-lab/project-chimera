"""AgentInteraction: Query and interact with agents post-simulation."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

from .memory import AgentMemory
from .profile import AgentProfile

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from an agent interview."""
    agent_id: str
    question: str
    response: str
    context: Dict[str, Any]
    timestamp: datetime


class AgentInteraction:
    """
    Handle post-simulation interaction with agents.

    Enables querying individual agents about their reasoning,
    decisions, and experiences during a simulation.
    """

    def __init__(self, memory: AgentMemory):
        """
        Initialize agent interaction handler.

        Args:
            memory: AgentMemory instance containing simulation memories
        """
        self.memory = memory

    async def interview_agent(
        self,
        agent_id: str,
        question: str,
        context_rounds: int = 5
    ) -> AgentResponse:
        """
        Interview an agent about their simulation experience.

        Args:
            agent_id: Unique identifier for the agent
            question: Question to ask the agent
            context_rounds: Number of recent rounds to use as context

        Returns:
            AgentResponse with the agent's answer and context
        """
        logger.info(f"Interviewing agent {agent_id}")

        # Retrieve relevant memories for context
        relevant_memories = await self.memory.get_recent_memories(
            agent_id, count=context_rounds
        )

        # Build context for LLM
        memory_context = self._build_memory_context(relevant_memories)

        # Generate response using LLM or template
        response = await self._generate_agent_response(
            agent_id, question, memory_context, relevant_memories
        )

        return AgentResponse(
            agent_id=agent_id,
            question=question,
            response=response,
            context={
                "memories_used": len(relevant_memories),
                "memory_snippets": relevant_memories,
                "rounds_covered": self._get_rounds_range(relevant_memories)
            },
            timestamp=datetime.utcnow()
        )

    async def get_agent_memory(
        self,
        agent_id: str,
        start_round: Optional[int] = None,
        end_round: Optional[int] = None,
        action_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve agent's memory from simulation.

        Args:
            agent_id: Unique identifier for the agent
            start_round: Optional starting round (inclusive)
            end_round: Optional ending round (inclusive)
            action_type: Optional filter by action type

        Returns:
            List of memory dictionaries
        """
        if action_type:
            return await self.memory.get_memories_by_action_type(agent_id, action_type)
        return await self.memory.get_memories(agent_id, start_round, end_round)

    async def analyze_agent_behavior(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Analyze an agent's behavior patterns from memory.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Dictionary with behavioral analysis
        """
        summary = await self.memory.get_memory_summary(agent_id)

        if summary["total_memories"] == 0:
            return {
                "agent_id": agent_id,
                "analysis": "No memories found for analysis"
            }

        # Calculate behavioral metrics
        memories = await self.memory.get_memories(agent_id)

        # Action frequency
        action_frequency = summary["action_types"]

        # Activity pattern (actions per round)
        rounds = summary["rounds"]
        if len(rounds) > 1:
            actions_per_round = summary["total_memories"] / len(rounds)
        else:
            actions_per_round = summary["total_memories"]

        # Engagement level (based on content length)
        avg_content_length = sum(
            len(m.get("content", "")) for m in memories
        ) / len(memories)

        return {
            "agent_id": agent_id,
            "total_memories": summary["total_memories"],
            "rounds_active": len(rounds),
            "actions_per_round": round(actions_per_round, 2),
            "action_frequency": action_frequency,
            "avg_content_length": round(avg_content_length, 2),
            "engagement_level": self._calculate_engagement_level(avg_content_length, actions_per_round),
            "first_activity": summary["first_round"],
            "last_activity": summary["last_round"]
        }

    async def compare_agents(
        self,
        agent_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare behaviors between multiple agents.

        Args:
            agent_ids: List of agent IDs to compare

        Returns:
            Dictionary with comparative analysis
        """
        analyses = {}

        for agent_id in agent_ids:
            analyses[agent_id] = await self.analyze_agent_behavior(agent_id)

        # Calculate comparative metrics
        total_memories = sum(a.get("total_memories", 0) for a in analyses.values())
        most_active = max(analyses.items(), key=lambda x: x[1].get("total_memories", 0))
        least_active = min(analyses.items(), key=lambda x: x[1].get("total_memories", float("inf")))

        return {
            "agents_compared": len(agent_ids),
            "total_memories": total_memories,
            "avg_memories_per_agent": round(total_memories / len(agent_ids), 2) if agent_ids else 0,
            "most_active_agent": most_active[0],
            "most_active_count": most_active[1].get("total_memories", 0),
            "least_active_agent": least_active[0],
            "least_active_count": least_active[1].get("total_memories", 0),
            "individual_analyses": analyses
        }

    def _build_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """
        Build context string from memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            Formatted context string
        """
        if not memories:
            return "No memories available."

        context_lines = []
        for m in memories:
            context_lines.append(
                f"Round {m['round']}: {m['action_type']} - {m.get('content', '')[:100]}"
            )

        return "\n".join(context_lines)

    def _get_rounds_range(self, memories: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get the round range from memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            Dictionary with first and last round
        """
        if not memories:
            return {"first": 0, "last": 0}

        rounds = [m["round"] for m in memories]
        return {"first": min(rounds), "last": max(rounds)}

    async def _generate_agent_response(
        self,
        agent_id: str,
        question: str,
        memory_context: str,
        memories: List[Dict[str, Any]]
    ) -> str:
        """
        Generate agent response using template-based approach.

        In production, this would use an LLM to generate contextual
        responses based on the agent's persona and memories.

        Args:
            agent_id: Unique identifier for the agent
            question: Question being asked
            memory_context: Formatted memory context
            memories: List of relevant memories

        Returns:
            Generated response string
        """
        # For Phase 1, use template-based responses
        # This will be enhanced with LLM-based generation in Phase 2

        if not memories:
            return f"I don't have any memories from the simulation to answer that question."

        # Analyze the question to provide relevant context
        question_lower = question.lower()

        # Concern/why questions
        if any(word in question_lower for word in ["concern", "why", "reasoning", "motivation"]):
            return self._generate_reasoning_response(memories)

        # Summary/overview questions
        elif any(word in question_lower for word in ["summary", "overview", "happened", "experience"]):
            return self._generate_summary_response(memories)

        # Specific round/position questions
        elif any(word in question_lower for word in ["position", "stance", "opinion", "view"]):
            return self._generate_position_response(memories)

        # Default response
        else:
            return self._generate_default_response(memories)

    def _generate_reasoning_response(self, memories: List[Dict[str, Any]]) -> str:
        """Generate response about reasoning/motivation."""
        rounds = [m["round"] for m in memories]
        actions = [m["action_type"] for m in memories]

        return (
            f"During the simulation (rounds {min(rounds)}-{max(rounds)}), "
            f"I processed information through {len(actions)} actions. "
            f"My primary focus was on understanding the implications before forming opinions. "
            f"The memory context shows my engagement pattern across the rounds."
        )

    def _generate_summary_response(self, memories: List[Dict[str, Any]]) -> str:
        """Generate response about simulation experience."""
        if not memories:
            return "I have no memories of the simulation."

        total_actions = len(memories)
        rounds = sorted(set(m["round"] for m in memories))

        return (
            f"I participated in {len(rounds)} rounds with {total_actions} total actions. "
            f"My activity ranged from round {rounds[0]} to round {rounds[-1]}. "
            f"I engaged with various topics throughout the simulation."
        )

    def _generate_position_response(self, memories: List[Dict[str, Any]]) -> str:
        """Generate response about position/stance."""
        recent = memories[-3:] if len(memories) > 3 else memories
        content_preview = recent[-1].get("content", "")[:50] if recent else ""

        return (
            f"Based on my actions during the simulation, my position evolved "
            f"through {len(memories)} interactions. My most recent engagement "
            f"focused on: '{content_preview}...'"
        )

    def _generate_default_response(self, memories: List[Dict[str, Any]]) -> str:
        """Generate default response."""
        total = len(memories)
        rounds = sorted(set(m["round"] for m in memories))

        return (
            f"During the simulation rounds {rounds[0] if rounds else 0} to "
            f"{rounds[-1] if rounds else 0}, I recorded {total} actions. "
            f"I processed information and arrived at positions through careful consideration."
        )

    def _calculate_engagement_level(self, avg_content_length: float, actions_per_round: float) -> str:
        """
        Calculate engagement level based on metrics.

        Args:
            avg_content_length: Average content length across memories
            actions_per_round: Average actions per round

        Returns:
            Engagement level string (low, medium, high)
        """
        # Simple heuristic for engagement classification
        if avg_content_length > 100 and actions_per_round > 1:
            return "high"
        elif avg_content_length > 50 or actions_per_round > 0.5:
            return "medium"
        else:
            return "low"
