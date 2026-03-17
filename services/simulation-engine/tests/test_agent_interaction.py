"""Tests for agent interaction and memory modules."""
import pytest
from agents.interaction import AgentInteraction, AgentResponse
from agents.memory import AgentMemory
from agents.profile import AgentProfile, MBTIType, Demographics, BehavioralProfile, PoliticalLeaning


@pytest.mark.asyncio
async def test_store_and_retrieve_memories():
    """Test storing and retrieving agent memories."""
    memory = AgentMemory()

    # Store some actions
    await memory.store_action("agent_001", 1, "post", "Initial thought about policy")
    await memory.store_action("agent_001", 2, "reply", "Response to counter-argument")
    await memory.store_action("agent_001", 3, "post", "Final opinion")

    # Retrieve all memories
    all_memories = await memory.get_memories("agent_001")

    assert len(all_memories) == 3
    assert all_memories[0]["round"] == 1
    assert all_memories[2]["round"] == 3
    assert all_memories[0]["action_type"] == "post"
    assert all_memories[1]["action_type"] == "reply"


@pytest.mark.asyncio
async def test_memory_with_round_filtering():
    """Test retrieving memories for specific time range."""
    memory = AgentMemory()

    # Store actions across multiple rounds
    await memory.store_action("agent_001", 1, "post", "Round 1 content")
    await memory.store_action("agent_001", 2, "reply", "Round 2 content")
    await memory.store_action("agent_001", 3, "post", "Round 3 content")
    await memory.store_action("agent_001", 4, "reply", "Round 4 content")
    await memory.store_action("agent_001", 5, "post", "Round 5 content")

    # Get memory for specific round range
    round_2_3 = await memory.get_memories("agent_001", start_round=2, end_round=3)

    assert len(round_2_3) == 2
    assert round_2_3[0]["round"] == 2
    assert round_2_3[1]["round"] == 3


@pytest.mark.asyncio
async def test_memory_limit_enforcement():
    """Test that memory limit is enforced with FIFO eviction."""
    memory = AgentMemory(max_memories_per_agent=3)

    # Store more memories than the limit
    await memory.store_action("agent_001", 1, "post", "Memory 1")
    await memory.store_action("agent_001", 2, "post", "Memory 2")
    await memory.store_action("agent_001", 3, "post", "Memory 3")
    await memory.store_action("agent_001", 4, "post", "Memory 4")  # Should evict memory 1

    memories = await memory.get_memories("agent_001")

    # Should only have the 3 most recent memories
    assert len(memories) == 3
    assert memories[0]["round"] == 2  # Memory 1 was evicted
    assert memories[2]["round"] == 4


@pytest.mark.asyncio
async def test_get_recent_memories():
    """Test retrieving recent memories."""
    memory = AgentMemory()

    # Store multiple actions
    for i in range(10):
        await memory.store_action("agent_001", i + 1, "post", f"Memory {i + 1}")

    # Get recent 3 memories (should be rounds 10, 9, 8 - most recent first)
    recent = await memory.get_recent_memories("agent_001", count=3)

    assert len(recent) == 3
    assert recent[0]["round"] == 10  # Most recent first
    assert recent[2]["round"] == 8


@pytest.mark.asyncio
async def test_search_memories():
    """Test searching memories by content."""
    memory = AgentMemory()

    await memory.store_action("agent_001", 1, "post", "I support the climate policy")
    await memory.store_action("agent_001", 2, "reply", "What about the economic impact?")
    await memory.store_action("agent_001", 3, "post", "The climate policy needs more research")

    # Search for "climate"
    results = await memory.search_memories("agent_001", "climate")

    assert len(results) == 2
    assert "climate" in results[0]["content"].lower()
    assert "climate" in results[1]["content"].lower()


@pytest.mark.asyncio
async def test_memory_summary():
    """Test getting memory summary."""
    memory = AgentMemory()

    await memory.store_action("agent_001", 1, "post", "Content 1")
    await memory.store_action("agent_001", 2, "reply", "Content 2")
    await memory.store_action("agent_001", 3, "post", "Content 3")

    summary = await memory.get_memory_summary("agent_001")

    assert summary["agent_id"] == "agent_001"
    assert summary["total_memories"] == 3
    assert summary["first_round"] == 1
    assert summary["last_round"] == 3
    assert "post" in summary["action_types"]
    assert summary["action_types"]["post"] == 2
    assert summary["action_types"]["reply"] == 1


@pytest.mark.asyncio
async def test_interview_agent():
    """Test querying individual agent post-simulation."""
    memory = AgentMemory()

    # Store some actions
    await memory.store_action("agent_001", 1, "post", "Shared policy opinion")
    await memory.store_action("agent_001", 2, "reply", "Responded to counter-argument")
    await memory.store_action("agent_001", 3, "post", "Refined position based on feedback")

    interaction = AgentInteraction(memory)

    response = await interaction.interview_agent(
        agent_id="agent_001",
        question="What was your primary concern about the policy?"
    )

    assert response.agent_id == "agent_001"
    assert response.response is not None
    assert len(response.response) > 0
    assert "memories_used" in response.context
    assert response.context["memories_used"] == 3


@pytest.mark.asyncio
async def test_interview_agent_with_no_memories():
    """Test interviewing an agent with no memories."""
    memory = AgentMemory()
    interaction = AgentInteraction(memory)

    response = await interaction.interview_agent(
        agent_id="agent_001",
        question="What do you remember?"
    )

    assert response.agent_id == "agent_001"
    assert "no memories" in response.response.lower() or "don't have" in response.response.lower()


@pytest.mark.asyncio
async def test_get_agent_memory():
    """Test retrieving agent's memory from simulation."""
    memory = AgentMemory()

    # Store some actions
    await memory.store_action("agent_001", 1, "post", "Initial thought")
    await memory.store_action("agent_001", 2, "reply", "Follow-up")
    await memory.store_action("agent_001", 3, "post", "Final opinion")
    await memory.store_action("agent_001", 4, "reply", "Additional comment")

    interaction = AgentInteraction(memory)

    # Get all memory
    all_memory = await interaction.get_agent_memory("agent_001")

    assert len(all_memory) == 4
    assert all_memory[0]["round"] == 1
    assert all_memory[3]["round"] == 4

    # Get memory for specific time range
    recent_memory = await interaction.get_agent_memory(
        "agent_001",
        start_round=2,
        end_round=3
    )

    assert len(recent_memory) == 2
    assert recent_memory[0]["round"] == 2
    assert recent_memory[1]["round"] == 3


@pytest.mark.asyncio
async def test_analyze_agent_behavior():
    """Test behavioral analysis of an agent."""
    memory = AgentMemory()

    # Store varied actions
    await memory.store_action("agent_001", 1, "post", "This is a longer post with more content for analysis")
    await memory.store_action("agent_001", 1, "reply", "Short reply")
    await memory.store_action("agent_001", 2, "post", "Another medium length post content here")
    await memory.store_action("agent_001", 2, "react", "Reaction")

    interaction = AgentInteraction(memory)
    analysis = await interaction.analyze_agent_behavior("agent_001")

    assert analysis["agent_id"] == "agent_001"
    assert analysis["total_memories"] == 4
    assert analysis["rounds_active"] == 2
    assert analysis["actions_per_round"] == 2.0
    assert analysis["first_activity"] == 1
    assert analysis["last_activity"] == 2
    assert "post" in analysis["action_frequency"]
    assert analysis["action_frequency"]["post"] == 2
    assert analysis["engagement_level"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_compare_agents():
    """Test comparing behaviors between multiple agents."""
    memory = AgentMemory()

    # Store memories for agent_001
    await memory.store_action("agent_001", 1, "post", "Agent 1 post")
    await memory.store_action("agent_001", 2, "reply", "Agent 1 reply")

    # Store memories for agent_002
    await memory.store_action("agent_002", 1, "post", "Agent 2 post")
    await memory.store_action("agent_002", 1, "reply", "Agent 2 reply")
    await memory.store_action("agent_002", 2, "post", "Agent 2 second post")
    await memory.store_action("agent_002", 2, "reply", "Agent 2 second reply")

    # Store memories for agent_003
    await memory.store_action("agent_003", 1, "post", "Agent 3 post")

    interaction = AgentInteraction(memory)
    comparison = await interaction.compare_agents(["agent_001", "agent_002", "agent_003"])

    assert comparison["agents_compared"] == 3
    assert comparison["total_memories"] == 7
    assert comparison["avg_memories_per_agent"] == pytest.approx(2.33, rel=0.1)
    assert comparison["most_active_agent"] == "agent_002"
    assert comparison["most_active_count"] == 4
    assert comparison["least_active_agent"] == "agent_003"
    assert comparison["least_active_count"] == 1
    assert "individual_analyses" in comparison


@pytest.mark.asyncio
async def test_get_memory_by_action_type():
    """Test filtering memories by action type."""
    memory = AgentMemory()

    await memory.store_action("agent_001", 1, "post", "Post 1")
    await memory.store_action("agent_001", 2, "reply", "Reply 1")
    await memory.store_action("agent_001", 3, "post", "Post 2")
    await memory.store_action("agent_001", 4, "reply", "Reply 2")

    interaction = AgentInteraction(memory)

    posts = await interaction.get_agent_memory("agent_001", action_type="post")
    replies = await interaction.get_agent_memory("agent_001", action_type="reply")

    assert len(posts) == 2
    assert len(replies) == 2
    assert all(m["action_type"] == "post" for m in posts)
    assert all(m["action_type"] == "reply" for m in replies)


@pytest.mark.asyncio
async def test_clear_memories():
    """Test clearing memories for an agent."""
    memory = AgentMemory()

    await memory.store_action("agent_001", 1, "post", "Memory 1")
    await memory.store_action("agent_001", 2, "post", "Memory 2")

    assert memory.get_memory_count("agent_001") == 2

    await memory.clear_memories("agent_001")

    assert memory.get_memory_count("agent_001") == 0
    assert await memory.get_memories("agent_001") == []


@pytest.mark.asyncio
async def test_multiple_agents():
    """Test handling memories for multiple agents."""
    memory = AgentMemory()

    # Store memories for different agents
    await memory.store_action("agent_001", 1, "post", "Agent 1")
    await memory.store_action("agent_002", 1, "post", "Agent 2")
    await memory.store_action("agent_003", 1, "post", "Agent 3")

    # Check all agent IDs
    all_ids = memory.get_all_agent_ids()
    assert set(all_ids) == {"agent_001", "agent_002", "agent_003"}

    # Verify each agent has correct memories
    mem1 = await memory.get_memories("agent_001")
    mem2 = await memory.get_memories("agent_002")
    mem3 = await memory.get_memories("agent_003")

    assert len(mem1) == 1
    assert len(mem2) == 1
    assert len(mem3) == 1
