"""AgentMemory: Store and retrieve agent memories from simulation."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Store and retrieve agent memories from simulation.

    Provides in-memory storage for agent actions and experiences
    during simulations, enabling post-simulation querying and analysis.
    """

    def __init__(self, max_memories_per_agent: int = 1000):
        """
        Initialize the agent memory store.

        Args:
            max_memories_per_agent: Maximum number of memories to store per agent
        """
        self._memories: Dict[str, List[Dict[str, Any]]] = {}
        self.max_memories_per_agent = max_memories_per_agent

    async def store_action(
        self,
        agent_id: str,
        round_num: int,
        action_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store an agent action in memory.

        Args:
            agent_id: Unique identifier for the agent
            round_num: Simulation round number
            action_type: Type of action (post, reply, react, etc.)
            content: Content of the action
            metadata: Optional additional metadata
        """
        memory = {
            "agent_id": agent_id,
            "round": round_num,
            "action_type": action_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        if agent_id not in self._memories:
            self._memories[agent_id] = []

        self._memories[agent_id].append(memory)

        # Enforce max memories limit (FIFO eviction)
        if len(self._memories[agent_id]) > self.max_memories_per_agent:
            self._memories[agent_id] = self._memories[agent_id][-self.max_memories_per_agent:]

        logger.debug(f"Stored memory for agent {agent_id}, round {round_num}")

    async def get_memories(
        self,
        agent_id: str,
        start_round: Optional[int] = None,
        end_round: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories for an agent.

        Args:
            agent_id: Unique identifier for the agent
            start_round: Optional starting round (inclusive)
            end_round: Optional ending round (inclusive)
            limit: Optional maximum number of memories to return

        Returns:
            List of memory dictionaries sorted by round
        """
        if agent_id not in self._memories:
            return []

        memories = self._memories[agent_id].copy()

        # Filter by round range
        if start_round is not None:
            memories = [m for m in memories if m["round"] >= start_round]
        if end_round is not None:
            memories = [m for m in memories if m["round"] <= end_round]

        # Apply limit
        if limit is not None:
            memories = memories[:limit]

        return memories

    async def get_recent_memories(
        self,
        agent_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent memories for an agent.

        Args:
            agent_id: Unique identifier for the agent
            count: Number of recent memories to retrieve

        Returns:
            List of the most recent memory dictionaries
        """
        memories = await self.get_memories(agent_id)
        # Sort by round descending to get most recent
        memories = sorted(memories, key=lambda m: m["round"], reverse=True)
        return memories[:count]

    async def get_memories_by_action_type(
        self,
        agent_id: str,
        action_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get memories filtered by action type.

        Args:
            agent_id: Unique identifier for the agent
            action_type: Type of action to filter by

        Returns:
            List of memory dictionaries with matching action type
        """
        memories = await self.get_memories(agent_id)
        return [m for m in memories if m["action_type"] == action_type]

    async def search_memories(
        self,
        agent_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search memories by content.

        Args:
            agent_id: Unique identifier for the agent
            query: Search query string

        Returns:
            List of memory dictionaries matching the query
        """
        memories = await self.get_memories(agent_id)
        query_lower = query.lower()
        return [
            m for m in memories
            if query_lower in m["content"].lower()
        ]

    async def clear_memories(self, agent_id: str) -> None:
        """
        Clear all memories for an agent.

        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self._memories:
            del self._memories[agent_id]
            logger.info(f"Cleared memories for agent {agent_id}")

    def get_memory_count(self, agent_id: str) -> int:
        """
        Get the number of memories stored for an agent.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Number of memories stored
        """
        return len(self._memories.get(agent_id, []))

    def get_all_agent_ids(self) -> List[str]:
        """
        Get all agent IDs that have memories.

        Returns:
            List of agent IDs
        """
        return list(self._memories.keys())

    async def get_memory_summary(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of an agent's memories.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Dictionary with memory statistics
        """
        memories = await self.get_memories(agent_id)

        if not memories:
            return {
                "agent_id": agent_id,
                "total_memories": 0,
                "rounds": [],
                "action_types": {}
            }

        rounds = [m["round"] for m in memories]
        action_types = {}

        for memory in memories:
            at = memory["action_type"]
            action_types[at] = action_types.get(at, 0) + 1

        return {
            "agent_id": agent_id,
            "total_memories": len(memories),
            "rounds": sorted(set(rounds)),
            "action_types": action_types,
            "first_round": min(rounds),
            "last_round": max(rounds)
        }
