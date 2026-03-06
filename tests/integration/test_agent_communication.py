"""
Integration tests for agent-to-agent communication.

Tests communication flows between services:
- SceneSpeak → Captioning
- Captioning → Sentiment
- BSL translation flow
- Health endpoint verification
"""

import pytest
import asyncio
from typing import Dict, Any
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_scenespeak_health(scenespeak_client: AsyncClient):
    """Test SceneSpeak agent health endpoint."""
    response = await scenespeak_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_scenespeak_readiness(scenespeak_client: AsyncClient):
    """Test SceneSpeak agent readiness endpoint."""
    response = await scenespeak_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data


@pytest.mark.asyncio
@pytest.mark.requires_docker
@pytest.mark.slow
async def test_scenespeak_generate_dialogue(
    scenespeak_client: AsyncClient,
    test_dialogue_prompt: Dict[str, Any]
):
    """Test dialogue generation through SceneSpeak agent."""
    response = await scenespeak_client.post(
        "/v1/generate",
        json=test_dialogue_prompt
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "text" in data or "dialogue" in data
    assert "metadata" in data or "source" in data


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_captioning_health(captioning_client: AsyncClient):
    """Test captioning agent health endpoint."""
    response = await captioning_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_captioning_readiness(captioning_client: AsyncClient):
    """Test captioning agent readiness endpoint."""
    response = await captioning_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
@pytest.mark.requires_docker
@pytest.mark.slow
async def test_scenespeak_to_captioning_flow(
    scenespeak_client: AsyncClient,
    captioning_client: AsyncClient
):
    """
    Test SceneSpeak → Captioning flow.

    1. Generate dialogue with SceneSpeak
    2. Send to captioning for processing
    3. Verify captioning responds
    """
    # Generate dialogue
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "Welcome to the show!",
            "max_tokens": 30,
            "temperature": 0.5
        }
    )

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()
    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    assert dialogue_text

    # The captioning service would process this text
    # For now, verify captioning is accessible
    response = await captioning_client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_sentiment_health(sentiment_client: AsyncClient):
    """Test sentiment agent health endpoint."""
    response = await sentiment_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_sentiment_readiness(sentiment_client: AsyncClient):
    """Test sentiment agent readiness endpoint."""
    response = await sentiment_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_sentiment_analyze_text(
    sentiment_client: AsyncClient,
    test_text: str
):
    """Test sentiment analysis on sample text."""
    response = await sentiment_client.post(
        "/v1/analyze",
        json={"text": test_text}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "sentiment" in data
    assert "score" in data
    assert "confidence" in data
    assert data["sentiment"] in ["positive", "negative", "neutral"]


@pytest.mark.asyncio
@pytest.mark.requires_docker
@pytest.mark.slow
async def test_captioning_to_sentiment_flow(
    captioning_client: AsyncClient,
    sentiment_client: AsyncClient,
    test_text: str
):
    """
    Test Captioning → Sentiment flow.

    1. Get captioning (mock this step)
    2. Analyze caption sentiment
    3. Verify results
    """
    # Verify captioning is available
    captioning_health = await captioning_client.get("/health/live")
    assert captioning_health.status_code == 200

    # Analyze sentiment of test text (simulating caption output)
    sentiment_response = await sentiment_client.post(
        "/v1/analyze",
        json={"text": test_text}
    )

    assert sentiment_response.status_code == 200
    sentiment_data = sentiment_response.json()

    # Verify sentiment analysis worked
    assert "sentiment" in sentiment_data
    assert "score" in sentiment_data


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_bsl_health(bsl_client: AsyncClient):
    """Test BSL agent health endpoint."""
    response = await bsl_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_bsl_readiness(bsl_client: AsyncClient):
    """Test BSL agent readiness endpoint."""
    response = await bsl_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
@pytest.mark.requires_docker
@pytest.mark.slow
async def test_bsl_translation_flow(
    bsl_client: AsyncClient,
    test_text_for_translation: str
):
    """Test BSL translation from English text."""
    response = await bsl_client.post(
        "/v1/translate",
        json={
            "text": test_text_for_translation,
            "include_nmm": True,
            "context": {"show_id": "test-show-001"}
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "gloss" in data
    assert "breakdown" in data
    assert "confidence" in data

    # Gloss should be non-empty
    assert len(data["gloss"]) > 0


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_bsl_avatar_render(
    bsl_client: AsyncClient,
    test_text_for_translation: str
):
    """Test BSL avatar rendering."""
    # First translate to get gloss
    translate_response = await bsl_client.post(
        "/v1/translate",
        json={"text": test_text_for_translation}
    )

    assert translate_response.status_code == 200
    gloss = translate_response.json()["gloss"]

    # Render the gloss
    render_response = await bsl_client.post(
        "/v1/render",
        json={
            "gloss": gloss,
            "session_id": "test-session-001",
            "include_nmm": True
        }
    )

    assert render_response.status_code == 200
    data = render_response.json()

    # Verify response
    assert "success" in data
    assert "animation_data" in data
    assert data["success"] is True


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_all_agent_health_endpoints(
    all_services_running: Dict[str, bool],
    scenespeak_client: AsyncClient,
    captioning_client: AsyncClient,
    bsl_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """Verify all agent health endpoints are accessible."""
    agents = {
        "scenespeak": scenespeak_client,
        "captioning": captioning_client,
        "bsl": bsl_client,
        "sentiment": sentiment_client
    }

    for agent_name, client in agents.items():
        if all_services_running.get(agent_name, False):
            response = await client.get("/health/live")
            assert response.status_code == 200, f"{agent_name} health check failed"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_all_agent_readiness_endpoints(
    all_services_running: Dict[str, bool],
    scenespeak_client: AsyncClient,
    captioning_client: AsyncClient,
    bsl_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """Verify all agent readiness endpoints are accessible."""
    agents = {
        "scenespeak": scenespeak_client,
        "captioning": captioning_client,
        "bsl": bsl_client,
        "sentiment": sentiment_client
    }

    for agent_name, client in agents.items():
        if all_services_running.get(agent_name, False):
            response = await client.get("/health/ready")
            assert response.status_code == 200, f"{agent_name} readiness check failed"


@pytest.mark.asyncio
@pytest.mark.requires_docker
@pytest.mark.slow
async def test_sentiment_batch_analysis(
    sentiment_client: AsyncClient
):
    """Test batch sentiment analysis."""
    texts = [
        "I love this show!",
        "This is boring.",
        "What time does it start?",
        "Amazing performance!"
    ]

    response = await sentiment_client.post(
        "/v1/batch",
        json={"texts": texts}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "results" in data
    assert len(data["results"]) == len(texts)

    # Each result should have required fields
    for result in data["results"]:
        assert "sentiment" in result
        assert "score" in result


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_agent_metrics_endpoints(
    scenespeak_client: AsyncClient,
    captioning_client: AsyncClient,
    bsl_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """Test that all agents expose Prometheus metrics."""
    agents = {
        "scenespeak": scenespeak_client,
        "captioning": captioning_client,
        "bsl": bsl_client,
        "sentiment": sentiment_client
    }

    for agent_name, client in agents.items():
        response = await client.get("/metrics")

        # Accept 404 if not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Verify Prometheus format
            metrics_text = response.text
            assert "# HELP" in metrics_text or "# TYPE" in metrics_text


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_concurrent_agent_requests(
    scenespeak_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """Test that agents can handle concurrent requests."""
    # Send multiple concurrent requests to different agents
    tasks = [
        scenespeak_client.get("/health/live"),
        sentiment_client.get("/health/live"),
        scenespeak_client.get("/health/ready"),
        sentiment_client.get("/health/ready"),
    ]

    responses = await asyncio.gather(*tasks)

    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)
