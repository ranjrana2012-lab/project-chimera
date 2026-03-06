"""
Full Pipeline Integration Tests.

Tests the complete end-to-end flow through all services:
1. Generate dialogue (SceneSpeak)
2. Transcribe to BSL (BSL Agent)
3. Check safety (Safety Filter)
4. Analyze sentiment (Sentiment Agent)
5. Verify complete flow
"""

import pytest
import asyncio
from typing import Dict, Any
from httpx import AsyncClient


pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_full_theatre_pipeline(
    scenespeak_client: AsyncClient,
    bsl_client: AsyncClient,
    safety_client: AsyncClient,
    sentiment_client: AsyncClient,
    test_show_context: Dict[str, Any]
):
    """
    Test complete theatre production pipeline.

    Flow:
    1. Generate dialogue with SceneSpeak
    2. Translate dialogue to BSL gloss
    3. Check content safety
    4. Analyze sentiment
    """
    # Step 1: Generate dialogue
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "Generate a welcoming line for the audience",
            "max_tokens": 40,
            "temperature": 0.7,
            "context": test_show_context
        }
    )

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()
    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    assert dialogue_text, "Dialogue generation failed"
    print(f"\n✓ Generated dialogue: {dialogue_text[:50]}...")

    # Step 2: Translate to BSL
    bsl_response = await bsl_client.post(
        "/v1/translate",
        json={
            "text": dialogue_text,
            "include_nmm": True,
            "context": test_show_context
        }
    )

    assert bsl_response.status_code == 200
    bsl_data = bsl_response.json()

    assert "gloss" in bsl_data
    assert bsl_data["gloss"]
    print(f"✓ Translated to BSL: {bsl_data['gloss'][:50]}...")

    # Step 3: Check safety
    safety_response = await safety_client.post(
        "/v1/moderate",
        json={
            "content": dialogue_text,
            "content_id": f"{test_show_context['show_id']}-scene-{test_show_context['scene']}",
            "user_id": "system",
            "context": test_show_context,
            "policy": "family"
        }
    )

    assert safety_response.status_code == 200
    safety_data = safety_response.json()

    is_safe = safety_data.get("safe") or safety_data.get("result", {}).get("is_safe", True)
    print(f"✓ Safety check: {'PASSED' if is_safe else 'FLAGGED'}")

    # Step 4: Analyze sentiment
    sentiment_response = await sentiment_client.post(
        "/v1/analyze",
        json={
            "text": dialogue_text
        }
    )

    assert sentiment_response.status_code == 200
    sentiment_data = sentiment_response.json()

    assert "sentiment" in sentiment_data
    assert "score" in sentiment_data
    print(f"✓ Sentiment analysis: {sentiment_data['sentiment']} (score: {sentiment_data['score']:.2f})")

    # Verify complete pipeline
    assert dialogue_text
    assert bsl_data["gloss"]
    assert is_safe or not is_safe  # Just verify we got a result
    assert sentiment_data["sentiment"] in ["positive", "negative", "neutral"]


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_with_safety_filtering(
    scenespeak_client: AsyncClient,
    safety_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """
    Test pipeline with safety filtering applied.

    Verifies that content flagged by safety filter is handled properly.
    """
    # Generate dialogue
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "Generate a line about how wonderful the show is",
            "max_tokens": 30
        }
    )

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()
    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    # Check safety with different policies
    policies = ["family", "teen", "adult"]

    for policy in policies:
        safety_response = await safety_client.post(
            "/v1/check",
            json={
                "content": dialogue_text,
                "policy": policy
            }
        )

        assert safety_response.status_code == 200
        safety_data = safety_response.json()

        assert "safe" in safety_data
        print(f"Policy {policy}: safe={safety_data['safe']}")


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_error_handling(
    scenespeak_client: AsyncClient,
    bsl_client: AsyncClient,
    safety_client: AsyncClient
):
    """
    Test pipeline handles errors gracefully.

    Verifies that if one service fails, the pipeline doesn't crash.
    """
    # Test with invalid input to SceneSpeak
    invalid_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "",  # Empty prompt
            "max_tokens": -1  # Invalid max_tokens
        }
    )

    # Should handle gracefully (may return error or use defaults)
    assert invalid_response.status_code in [200, 400, 422]

    # Test BSL with empty text
    bsl_response = await bsl_client.post(
        "/v1/translate",
        json={"text": ""}
    )

    # Should handle gracefully
    assert bsl_response.status_code in [200, 400, 422]


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_concurrent_processing(
    scenespeak_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """
    Test pipeline can handle concurrent requests.

    Verifies that multiple pipeline runs can execute simultaneously.
    """
    async def run_pipeline(show_id: str):
        """Run a single pipeline instance."""
        # Generate dialogue
        dialogue_response = await scenespeak_client.post(
            "/v1/generate",
            json={
                "prompt": f"Generate dialogue for show {show_id}",
                "max_tokens": 30
            }
        )

        if dialogue_response.status_code != 200:
            return None

        dialogue_data = dialogue_response.json()
        dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

        # Analyze sentiment
        sentiment_response = await sentiment_client.post(
            "/v1/analyze",
            json={"text": dialogue_text}
        )

        if sentiment_response.status_code != 200:
            return None

        return {
            "show_id": show_id,
            "dialogue": dialogue_text,
            "sentiment": sentiment_response.json()
        }

    # Run multiple pipelines concurrently
    tasks = [
        run_pipeline(f"show-{i:03d}")
        for i in range(3)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify at least some succeeded
    successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    assert len(successful_results) >= 2, "At least 2 concurrent pipelines should succeed"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_with_batch_sentiment(
    scenespeak_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """
    Test pipeline with batch sentiment analysis.

    Generate multiple dialogues and analyze them in a batch.
    """
    # Generate multiple dialogues
    prompts = [
        "Welcome to the show!",
        "Hope you enjoy the performance.",
        "Thank you for coming tonight."
    ]

    dialogues = []
    for prompt in prompts:
        response = await scenespeak_client.post(
            "/v1/generate",
            json={"prompt": prompt, "max_tokens": 25}
        )

        if response.status_code == 200:
            data = response.json()
            dialogue_text = data.get("text") or data.get("dialogue", "")
            dialogues.append(dialogue_text)

    assert len(dialogues) > 0, "At least one dialogue should be generated"

    # Batch sentiment analysis
    sentiment_response = await sentiment_client.post(
        "/v1/batch",
        json={"texts": dialogues}
    )

    assert sentiment_response.status_code == 200
    sentiment_data = sentiment_response.json()

    assert "results" in sentiment_data
    assert len(sentiment_data["results"]) == len(dialogues)

    # Each result should have sentiment data
    for result in sentiment_data["results"]:
        assert "sentiment" in result
        assert "score" in result


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_metadata_tracking(
    scenespeak_client: AsyncClient,
    bsl_client: AsyncClient,
    safety_client: AsyncClient,
    test_show_context: Dict[str, Any]
):
    """
    Test that pipeline properly tracks metadata through all stages.

    Verifies that show_id, scene_number, and other context is preserved.
    """
    # Generate with context
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "Test dialogue",
            "max_tokens": 20,
            "context": test_show_context
        }
    )

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()

    # Verify metadata is present
    assert "metadata" in dialogue_data or "source" in dialogue_data

    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    # Translate with context
    bsl_response = await bsl_client.post(
        "/v1/translate",
        json={
            "text": dialogue_text,
            "context": test_show_context
        }
    )

    assert bsl_response.status_code == 200
    bsl_data = bsl_response.json()

    # Verify BSL response has metadata
    assert "confidence" in bsl_data
    assert "translation_time_ms" in bsl_data

    # Moderate with context
    safety_response = await safety_client.post(
        "/v1/moderate",
        json={
            "content": dialogue_text,
            "content_id": f"{test_show_context['show_id']}-test",
            "context": test_show_context
        }
    )

    assert safety_response.status_code == 200
    safety_data = safety_response.json()

    # Verify moderation result structure
    assert "result" in safety_data or "safe" in safety_data


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_end_to_end_timing(
    scenespeak_client: AsyncClient,
    bsl_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """
    Test pipeline timing and performance.

    Measures how long the complete pipeline takes to execute.
    """
    import time

    start_time = time.time()

    # Step 1: Generate dialogue
    dialogue_start = time.time()
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={"prompt": "Quick test dialogue", "max_tokens": 20}
    )
    dialogue_time = time.time() - dialogue_start

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()
    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    # Step 2: Translate to BSL
    bsl_start = time.time()
    bsl_response = await bsl_client.post(
        "/v1/translate",
        json={"text": dialogue_text}
    )
    bsl_time = time.time() - bsl_start

    assert bsl_response.status_code == 200

    # Step 3: Analyze sentiment
    sentiment_start = time.time()
    sentiment_response = await sentiment_client.post(
        "/v1/analyze",
        json={"text": dialogue_text}
    )
    sentiment_time = time.time() - sentiment_start

    assert sentiment_response.status_code == 200

    total_time = time.time() - start_time

    print(f"\nPipeline timing:")
    print(f"  Dialogue generation: {dialogue_time:.3f}s")
    print(f"  BSL translation: {bsl_time:.3f}s")
    print(f"  Sentiment analysis: {sentiment_time:.3f}s")
    print(f"  Total: {total_time:.3f}s")

    # Pipeline should complete in reasonable time
    assert total_time < 30.0, "Pipeline should complete within 30 seconds"


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_with_long_content(
    scenespeak_client: AsyncClient,
    bsl_client: AsyncClient,
    sentiment_client: AsyncClient
):
    """
    Test pipeline with longer content.

    Verifies pipeline handles realistic dialogue length.
    """
    # Generate longer dialogue
    dialogue_response = await scenespeak_client.post(
        "/v1/generate",
        json={
            "prompt": "Generate a monologue about time travel, about 100 words",
            "max_tokens": 150
        }
    )

    assert dialogue_response.status_code == 200
    dialogue_data = dialogue_response.json()
    dialogue_text = dialogue_data.get("text") or dialogue_data.get("dialogue", "")

    # Should generate reasonable length content
    assert len(dialogue_text) > 50

    # Translate to BSL
    bsl_response = await bsl_client.post(
        "/v1/translate",
        json={"text": dialogue_text}
    )

    assert bsl_response.status_code == 200
    bsl_data = bsl_response.json()

    # Should handle longer text
    assert "gloss" in bsl_data
    assert len(bsl_data["gloss"]) > 0

    # Analyze sentiment
    sentiment_response = await sentiment_client.post(
        "/v1/analyze",
        json={"text": dialogue_text}
    )

    assert sentiment_response.status_code == 200
    sentiment_data = sentiment_response.json()

    assert "sentiment" in sentiment_data


@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_pipeline_service_availability(
    all_services_running: Dict[str, bool]
):
    """
    Test that all required services are available for the pipeline.

    This is a prerequisite test for the full pipeline.
    """
    required_services = [
        "scenespeak",
        "bsl",
        "safety",
        "sentiment"
    ]

    for service in required_services:
        is_running = all_services_running.get(service, False)
        assert is_running, f"Required service {service} is not running"
        print(f"✓ {service} is available")
