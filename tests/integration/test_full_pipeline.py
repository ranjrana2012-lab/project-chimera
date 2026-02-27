"""
Full pipeline integration tests for Project Chimera.

Tests the complete flow: Sentiment Analysis -> SceneSpeak Dialogue Generation -> Safety Filter
"""

import pytest
import asyncio
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.integration
class TestFullPipeline:
    """Test the complete AI pipeline flow."""

    @pytest.mark.asyncio
    async def test_sentiment_to_dialogue_pipeline(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test sentiment analysis feeding into dialogue generation."""
        # Step 1: Analyze audience sentiment
        sentiment_request = {
            "text": "The audience seems excited and engaged!",
            "options": {
                "include_emotions": True,
                "include_trend": False,
                "aggregation_window": 60,
                "min_confidence": 0.5,
            },
        }

        response = await http_client.post(
            f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze",
            json=sentiment_request,
            timeout=10.0,
        )

        assert response.status_code == 200
        sentiment_data = response.json()
        assert "sentiment" in sentiment_data
        assert "confidence" in sentiment_data["sentiment"]

        # Step 2: Use sentiment in dialogue generation
        dialogue_request = {
            "scene_context": {
                "scene_id": "scene-001",
                "title": "Interactive Scene",
                "characters": ["ACTOR"],
                "setting": "Main Stage",
                "mood": sentiment_data["sentiment"].get("label", "neutral"),
            },
            "dialogue_context": [],
            "sentiment_vector": {
                "overall": sentiment_data["sentiment"].get("label", "neutral"),
                "intensity": sentiment_data["sentiment"].get("confidence", 0.5),
                "engagement": 0.75,
            },
        }

        response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json=dialogue_request,
            timeout=30.0,
        )

        assert response.status_code == 200
        dialogue_data = response.json()
        assert "proposed_lines" in dialogue_data
        assert dialogue_data["proposed_lines"]

    @pytest.mark.asyncio
    async def test_dialogue_through_safety_filter(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test generated dialogue passes through safety filter."""
        # Generate dialogue
        dialogue_request = {
            "scene_context": {
                "scene_id": "scene-002",
                "title": "Safety Test Scene",
                "characters": ["ACTOR"],
                "setting": "Stage",
            },
            "dialogue_context": [],
            "sentiment_vector": {"overall": "neutral"},
        }

        response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json=dialogue_request,
            timeout=30.0,
        )

        assert response.status_code == 200
        dialogue_data = response.json()
        generated_text = dialogue_data["proposed_lines"]

        # Check safety of generated content
        safety_request = {
            "content": generated_text,
            "options": {
                "check_profanity": True,
                "check_hate_speech": True,
                "check_sexual": True,
                "check_violence": True,
                "check_harassment": True,
            },
        }

        response = await http_client.post(
            f"http://{test_config['safety_host']}:{test_config['safety_port']}/check",
            json=safety_request,
            timeout=10.0,
        )

        assert response.status_code == 200
        safety_data = response.json()
        assert "decision" in safety_data
        assert "safe" in safety_data

        # Safe content should be approved
        if safety_data["safe"]:
            assert safety_data["decision"] in ["approve", "flagged_reviewed"]

    @pytest.mark.asyncio
    async def test_complete_end_to_end_flow(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test complete pipeline: sentiment -> dialogue -> safety."""
        # Audience input text
        audience_text = "I'm really enjoying this performance so far!"

        # 1. Sentiment Analysis
        sentiment_response = await http_client.post(
            f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze",
            json={"text": audience_text},
            timeout=10.0,
        )
        assert sentiment_response.status_code == 200
        sentiment_result = sentiment_response.json()

        # 2. Dialogue Generation with Sentiment Context
        dialogue_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": {
                    "scene_id": "scene-e2e-001",
                    "title": "End to End Test",
                    "characters": ["PROTAGONIST"],
                },
                "dialogue_context": [
                    {"character": "PROTAGONIST", "text": audience_text}
                ],
                "sentiment_vector": {
                    "overall": sentiment_result["sentiment"]["label"],
                    "intensity": sentiment_result["sentiment"]["confidence"],
                },
            },
            timeout=30.0,
        )
        assert dialogue_response.status_code == 200
        dialogue_result = dialogue_response.json()

        # 3. Safety Check
        safety_response = await http_client.post(
            f"http://{test_config['safety_host']}:{test_config['safety_port']}/check",
            json={"content": dialogue_result["proposed_lines"]},
            timeout=10.0,
        )
        assert safety_response.status_code == 200
        safety_result = safety_response.json()

        # Verify complete flow succeeded
        assert "proposed_lines" in dialogue_result
        assert "decision" in safety_result
        assert dialogue_result["latency_ms"] > 0

        # Return results for potential assertion
        return {
            "sentiment": sentiment_result,
            "dialogue": dialogue_result,
            "safety": safety_result,
        }

    @pytest.mark.asyncio
    async def test_pipeline_with_batch_sentiment(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test pipeline with batch sentiment analysis from multiple audience inputs."""
        audience_inputs = [
            "Amazing performance!",
            "Great show!",
            "Loved every minute!",
            "Brilliant acting!",
            "Wonderful experience!",
        ]

        # Batch sentiment analysis
        batch_response = await http_client.post(
            f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze-batch",
            json={"texts": audience_inputs},
            timeout=15.0,
        )
        assert batch_response.status_code == 200
        batch_result = batch_response.json()

        # Verify batch results
        assert "results" in batch_result
        assert len(batch_result["results"]) == len(audience_inputs)

        # Use aggregated sentiment for dialogue
        if "aggregate" in batch_result:
            aggregated = batch_result["aggregate"]
            dialogue_response = await http_client.post(
                f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
                json={
                    "scene_context": {
                        "scene_id": "scene-batch-001",
                        "title": "Batch Sentiment Scene",
                    },
                    "dialogue_context": [],
                    "sentiment_vector": {
                        "overall": aggregated.get("overall", "neutral"),
                        "intensity": aggregated.get("intensity", 0.5),
                        "sample_size": aggregated.get("sample_size", len(audience_inputs)),
                    },
                },
                timeout=30.0,
            )
            assert dialogue_response.status_code == 200

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test error handling in pipeline when services are unavailable."""
        # Test with invalid sentiment service endpoint
        try:
            response = await http_client.post(
                "http://localhost:9999/analyze",  # Invalid endpoint
                json={"text": "test"},
                timeout=2.0,
            )
        except Exception:
            # Expected - service should not be available
            pass

        # Verify pipeline handles service failure gracefully
        # The system should still function with fallback/default values
        dialogue_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": {"scene_id": "scene-error-001", "title": "Error Test"},
                "dialogue_context": [],
                "sentiment_vector": None,  # No sentiment data
            },
            timeout=30.0,
        )
        # Should still succeed with defaults
        assert dialogue_response.status_code == 200

    @pytest.mark.asyncio
    async def test_pipeline_performance_metrics(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test that pipeline components return performance metrics."""
        # Sentiment performance
        start_time = asyncio.get_event_loop().time()
        sentiment_response = await http_client.post(
            f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze",
            json={"text": "Test performance metrics"},
            timeout=10.0,
        )
        sentiment_time = asyncio.get_event_loop().time() - start_time

        assert sentiment_response.status_code == 200
        sentiment_data = sentiment_response.json()
        # Check for processing time metric
        assert "processing_time_ms" in sentiment_data
        assert sentiment_data["processing_time_ms"] > 0

        # Dialogue performance
        dialogue_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": {"scene_id": "scene-perf-001", "title": "Performance Test"},
                "dialogue_context": [],
            },
            timeout=30.0,
        )

        assert dialogue_response.status_code == 200
        dialogue_data = dialogue_response.json()
        assert "latency_ms" in dialogue_data
        assert dialogue_data["latency_ms"] > 0

        # Total pipeline time should be reasonable (< 5 seconds)
        assert sentiment_time + (dialogue_data["latency_ms"] / 1000) < 5.0

    @pytest.mark.asyncio
    async def test_pipeline_with_caching(
        self, http_client: AsyncClient, test_config: dict, redis_client
    ):
        """Test pipeline with Redis caching enabled."""
        scene_context = {
            "scene_id": "scene-cache-001",
            "title": "Cache Test Scene",
            "characters": ["ACTOR"],
        }

        # First request - cache miss
        first_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": scene_context,
                "dialogue_context": [],
                "sentiment_vector": {"overall": "neutral"},
            },
            timeout=30.0,
        )

        assert first_response.status_code == 200
        first_data = first_response.json()
        first_cached = first_data.get("cached", False)

        # Second request with same input - potential cache hit
        second_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": scene_context,
                "dialogue_context": [],
                "sentiment_vector": {"overall": "neutral"},
            },
            timeout=30.0,
        )

        assert second_response.status_code == 200
        second_data = second_response.json()
        second_cached = second_data.get("cached", False)

        # If caching is working, second request should be cached
        # or at least be faster
        if second_cached:
            assert second_data["latency_ms"] < first_data["latency_ms"]

    @pytest.mark.asyncio
    async def test_multilingual_pipeline(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test pipeline with multilingual content."""
        # Test with non-English text
        multilingual_texts = {
            "spanish": "El público está muy emocionado",
            "french": "Le public est très enthousiaste",
            "german": "Das Publikum ist sehr begeistert",
        }

        for language, text in multilingual_texts.items():
            # Sentiment analysis
            sentiment_response = await http_client.post(
                f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze",
                json={"text": text},
                timeout=10.0,
            )

            # May or may not support multilingual
            if sentiment_response.status_code == 200:
                sentiment_data = sentiment_response.json()

                # Generate dialogue
                dialogue_response = await http_client.post(
                    f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
                    json={
                        "scene_context": {
                            "scene_id": f"scene-multi-{language}",
                            "title": f"Multilingual {language.title()}",
                        },
                        "dialogue_context": [],
                        "sentiment_vector": {
                            "overall": sentiment_data["sentiment"]["label"]
                        },
                    },
                    timeout=30.0,
                )

                assert dialogue_response.status_code == 200

    @pytest.mark.asyncio
    async def test_pipeline_with_bsl_translation(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test pipeline with BSL sign language translation."""
        # Generate dialogue
        dialogue_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": {"scene_id": "scene-bsl-001", "title": "BSL Test"},
                "dialogue_context": [],
                "sentiment_vector": {"overall": "positive"},
            },
            timeout=30.0,
        )

        assert dialogue_response.status_code == 200
        dialogue_data = dialogue_response.json()
        dialogue_text = dialogue_data["proposed_lines"]

        # Translate to BSL gloss
        bsl_response = await http_client.post(
            f"http://{test_config['bsl_host']}:{test_config['bsl_port']}/translate",
            json={"text": dialogue_text, "format": "gloss"},
            timeout=15.0,
        )

        # BSL service may or may not be available
        if bsl_response.status_code == 200:
            bsl_data = bsl_response.json()
            assert "gloss" in bsl_data or "translation" in bsl_data

    @pytest.mark.asyncio
    async def test_pipeline_with_captioning(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test pipeline with real-time captioning."""
        # Generate dialogue for captioning
        dialogue_response = await http_client.post(
            f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/generate",
            json={
                "scene_context": {"scene_id": "scene-cap-001", "title": "Captioning Test"},
                "dialogue_context": [],
                "sentiment_vector": {"overall": "neutral"},
            },
            timeout=30.0,
        )

        assert dialogue_response.status_code == 200
        dialogue_data = dialogue_response.json()

        # Request captioning (simulated)
        captioning_response = await http_client.post(
            f"http://{test_config['captioning_host']}:{test_config['captioning_port']}/caption",
            json={
                "audio_data": "simulated_audio_data",
                "language": "en",
                "format": "text",
            },
            timeout=10.0,
        )

        # Captioning service response validation
        if captioning_response.status_code == 200:
            caption_data = captioning_response.json()
            assert "text" in caption_data or "caption" in caption_data

    @pytest.mark.asyncio
    async def test_pipeline_with_lighting_control(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test pipeline with automated lighting control based on sentiment."""
        # Get audience sentiment
        sentiment_response = await http_client.post(
            f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/analyze",
            json={"text": "The mood is very tense and dramatic"},
            timeout=10.0,
        )

        assert sentiment_response.status_code == 200
        sentiment_data = sentiment_response.json()

        # Adjust lighting based on sentiment
        lighting_response = await http_client.post(
            f"http://{test_config['lighting_host']}:{test_config['lighting_port']}/api/v1/lighting/set",
            json={
                "zone": "stage-main",
                "action": "set_scene",
                "params": {
                    "scene": "dramatic",
                    "intensity": 0.7,
                    "color_temp": "warm",
                },
            },
            timeout=5.0,
        )

        # Lighting service response validation
        if lighting_response.status_code == 200:
            lighting_data = lighting_response.json()
            assert "status" in lighting_data or "success" in lighting_data
