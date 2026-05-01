"""Tests for Kimi agent coordinator."""

import pytest
from unittest.mock import AsyncMock, Mock
from services.kimi_super_agent.agent_coordinator import AgentCoordinator


@pytest.fixture
def coordinator():
    return AgentCoordinator()


@pytest.mark.asyncio
async def test_coordinate_sentiment_agent(coordinator):
    """Test coordinating sentiment agent call"""
    # Mock the HTTP client's post method
    mock_response = Mock()
    mock_response.json = Mock(return_value={"sentiment": "positive", "confidence": 0.9})
    mock_response.raise_for_status = Mock()

    coordinator.client.post = AsyncMock(return_value=mock_response)

    result = await coordinator.call_agent("sentiment", {"text": "I'm happy!"})

    assert result["sentiment"] == "positive"
    assert result["_success"] is True
    assert result["_agent"] == "sentiment"
    assert "_timing_ms" in result


@pytest.mark.asyncio
async def test_coordinate_multiple_agents(coordinator):
    """Test coordinating multiple agents in parallel"""
    # Mock the HTTP client's post method
    mock_response = Mock()
    mock_response.json = Mock(return_value={"result": "ok"})
    mock_response.raise_for_status = Mock()

    coordinator.client.post = AsyncMock(return_value=mock_response)

    agent_calls = [
        {"agent": "sentiment", "data": {"text": "test"}},
        {"agent": "safety", "data": {"text": "test"}}
    ]

    results = await coordinator.coordinate_agents(agent_calls)

    assert len(results) == 2
    assert all(r["result"] == "ok" for r in results)
