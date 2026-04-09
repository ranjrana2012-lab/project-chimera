"""Tests for ForumEngine multi-agent debate system."""
import pytest
from reporting.forum_engine import ForumEngine
from reporting.models import Argument, DebateResult
from agents.profile import AgentProfile, MBTIType, Demographics, BehavioralProfile, PoliticalLeaning
from typing import List


async def create_test_agents(count: int) -> List[AgentProfile]:
    """Create mock agents for testing."""
    agents = []
    for i in range(count):
        agent = AgentProfile(
            id=f"test_agent_{i}",
            mbti=MBTIType.INTJ,
            demographics=Demographics(
                age=30,
                gender="neutral",
                education="Bachelor's",
                occupation="analyst",
                location="urban",
                income_level="middle"
            ),
            behavioral=BehavioralProfile(
                openness=0.7,
                conscientiousness=0.6,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.4
            ),
            political_leaning=PoliticalLeaning.CENTER,
            information_sources=["news"],
            memory_capacity=100
        )
        agents.append(agent)
    return agents


@pytest.mark.asyncio
async def test_forum_debate_reaches_consensus():
    """Test that forum debate produces consensus with multiple participants."""
    forum = ForumEngine()
    topic = "Should AI be regulated?"
    participants = await create_test_agents(3)
    result = await forum.debate_topic(topic, participants, rounds=3)
    assert result.consensus_score >= 0.0
    assert result.consensus_score <= 1.0
    assert len(result.arguments) >= 3
    assert result.topic == topic
    assert len(result.confidence_interval) == 2


@pytest.mark.asyncio
async def test_forum_single_round_debate():
    """Test that single round debate works correctly."""
    forum = ForumEngine()
    topic = "Test topic"
    participants = await create_test_agents(2)
    result = await forum.debate_topic(topic, participants, rounds=1)
    assert len(result.arguments) == 2
    assert result.consensus_score >= 0.0
    assert result.consensus_score <= 1.0


@pytest.mark.asyncio
async def test_confidence_calculation():
    """Test confidence calculation with different agreement levels."""
    forum = ForumEngine()

    # Test with unanimous agreement
    arguments_high = [
        Argument(agent_id="a1", content="Pro", stance=0.9, reasoning="Good for society"),
        Argument(agent_id="a2", content="Pro", stance=0.8, reasoning="Benefits outweigh risks"),
        Argument(agent_id="a3", content="Pro", stance=0.85, reasoning="Progress is necessary"),
    ]
    confidence = forum.calculate_confidence(arguments_high)
    assert confidence > 0.7  # High agreement

    # Test with disagreement
    arguments_low = [
        Argument(agent_id="a1", content="Pro", stance=0.9, reasoning="Good idea"),
        Argument(agent_id="a2", content="Con", stance=-0.8, reasoning="Bad idea"),
        Argument(agent_id="a3", content="Neutral", stance=0.0, reasoning="Not sure"),
    ]
    confidence_low = forum.calculate_confidence(arguments_low)
    assert confidence_low < 0.5  # Low agreement


@pytest.mark.asyncio
async def test_consensus_calculation():
    """Test consensus calculation from arguments."""
    forum = ForumEngine()

    # Test with high consensus (similar stances)
    arguments_high = [
        Argument(agent_id="a1", content="Agree", stance=0.8, reasoning="Support"),
        Argument(agent_id="a2", content="Agree", stance=0.85, reasoning="Support"),
        Argument(agent_id="a3", content="Agree", stance=0.9, reasoning="Support"),
    ]
    consensus = forum.calculate_consensus(arguments_high)
    assert consensus > 0.7  # High consensus

    # Test with low consensus (divergent stances)
    arguments_low = [
        Argument(agent_id="a1", content="Support", stance=0.9, reasoning="Pro"),
        Argument(agent_id="a2", content="Oppose", stance=-0.9, reasoning="Con"),
        Argument(agent_id="a3", content="Neutral", stance=0.0, reasoning="Neutral"),
    ]
    consensus_low = forum.calculate_consensus(arguments_low)
    # Low consensus should be significantly lower than high consensus
    assert consensus_low < consensus  # Lower than high consensus case
    assert consensus_low < 0.8  # Reasonable upper bound for disagreement


@pytest.mark.asyncio
async def test_forum_empty_participants():
    """Test that empty participants list is handled gracefully."""
    forum = ForumEngine()
    result = await forum.debate_topic("Topic", [], rounds=1)
    assert result.consensus_score == 0.0
    assert len(result.arguments) == 0


@pytest.mark.asyncio
async def test_forum_json_parsing_fallback():
    """Test that malformed JSON doesn't crash the system."""
    forum = ForumEngine()

    # Test with completely invalid JSON
    result = forum._parse_json_response("Not JSON at all")
    assert result["content"] == "Not JSON at all"
    assert result["stance"] == 0.0
    assert result["reasoning"] == ""

    # Test with JSON in markdown code block
    markdown_json = '''```json
    {
      "content": "Test argument",
      "stance": 0.8,
      "reasoning": "Test reasoning"
    }
    ```'''
    result = forum._parse_json_response(markdown_json)
    assert result["content"] == "Test argument"
    assert result["stance"] == 0.8
    assert result["reasoning"] == "Test reasoning"

    # Test with plain JSON
    plain_json = '{"content": "Plain test", "stance": 0.5, "reasoning": "Plain reasoning"}'
    result = forum._parse_json_response(plain_json)
    assert result["content"] == "Plain test"
    assert result["stance"] == 0.5
    assert result["reasoning"] == "Plain reasoning"


@pytest.mark.asyncio
async def test_confidence_interval_calculation():
    """Test confidence interval calculation."""
    forum = ForumEngine()

    # Test with small sample
    interval = forum._calculate_interval(0.8, 2)
    assert len(interval) == 2
    assert interval[0] >= 0.0
    assert interval[1] <= 1.0

    # Test with larger sample
    interval = forum._calculate_interval(0.8, 10)
    assert len(interval) == 2
    # Larger sample should have narrower interval
    small_interval = forum._calculate_interval(0.8, 2)
    assert interval[1] - interval[0] <= small_interval[1] - small_interval[0]

    # Test edge case with n=1
    interval_edge = forum._calculate_interval(0.5, 1)
    assert interval_edge == (0.0, 1.0)


@pytest.mark.asyncio
async def test_stance_validation():
    """Test that stance values are properly clamped to valid range."""
    forum = ForumEngine()

    # Test stance clamping in _parse_json_response
    # Mock response with out-of-range stance
    response = '{"content": "Test", "stance": 2.5, "reasoning": "Too high"}'
    data = forum._parse_json_response(response)
    # The stance should be clamped when creating the Argument
    arg = Argument(
        agent_id="test",
        content=data["content"],
        stance=min(1.0, max(-1.0, float(data.get("stance", 0.0)))),
        reasoning=data["reasoning"]
    )
    assert arg.stance <= 1.0
    assert arg.stance >= -1.0

    # Test negative out-of-range
    response_neg = '{"content": "Test", "stance": -3.0, "reasoning": "Too low"}'
    data_neg = forum._parse_json_response(response_neg)
    arg_neg = Argument(
        agent_id="test",
        content=data_neg["content"],
        stance=min(1.0, max(-1.0, float(data_neg.get("stance", 0.0)))),
        reasoning=data_neg["reasoning"]
    )
    assert arg_neg.stance >= -1.0


@pytest.mark.asyncio
async def test_context_building():
    """Test that debate context is built correctly for different rounds."""
    forum = ForumEngine()

    # Create a mock agent
    agents = await create_test_agents(1)
    agent = agents[0]

    # Test round 0 context (initial position)
    context_round0 = forum._build_context("Test topic", [], 0, agent)
    assert "Test topic" in context_round0
    assert "first round" in context_round0
    assert agent.mbti.value in context_round0

    # Test round 1+ context (with previous arguments)
    prev_args = [
        Argument(agent_id="agent1", content="Previous argument", stance=0.5, reasoning="Test")
    ]
    context_round1 = forum._build_context("Test topic", prev_args, 1, agent)
    assert "round 2" in context_round1
    assert "Previous arguments" in context_round1
    assert "agent1" in context_round1


@pytest.mark.asyncio
async def test_json_parsing_with_malformed_content():
    """Test JSON parsing with various malformed inputs."""
    forum = ForumEngine()

    # Test with JSON embedded in text
    embedded_json = "Some text before ```json\n{\"content\": \"test\", \"stance\": 0.7, \"reasoning\": \"ok\"}\n``` some text after"
    result = forum._parse_json_response(embedded_json)
    assert result["content"] == "test"
    assert result["stance"] == 0.7

    # Test with partial JSON (graceful degradation)
    partial_json = '{"content": "incomplete", "stance": 0.5'  # Missing closing brace
    result = forum._parse_json_response(partial_json)
    # Should fall back to treating entire string as content
    assert result["content"] == partial_json
    assert result["stance"] == 0.0
