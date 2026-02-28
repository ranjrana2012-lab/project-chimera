"""End-to-end integration tests for complete pipeline flows."""
import pytest
import time
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestSentimentToSceneSpeakFlow:
    """Test Sentiment -> SceneSpeak -> Safety -> Console flow."""

    def test_sentiment_sceneSpeak_pipeline(self, base_urls, http_client):
        """Test sentiment analysis feeds into SceneSpeak dialogue."""
        # Step 1: Analyze sentiment
        sentiment_response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json={"text": "Amazing performance!"},
            timeout=10
        )
        assert sentiment_response.status_code == 200
        sentiment_data = sentiment_response.json()

        # Step 2: Use sentiment in SceneSpeak request
        scenespeak_request = TestData.SCENESPEAK_REQUEST.copy()
        scenespeak_request["sentiment"] = sentiment_data["sentiment"]["positive_score"]

        dialogue_response = http_client.post(
            f"{base_urls['scenespeak']}/v1/generate",
            json=scenespeak_request,
            timeout=30
        )
        assert dialogue_response.status_code == 200
        dialogue_data = dialogue_response.json()
        assert "proposed_lines" in dialogue_data or "output" in dialogue_data


@pytest.mark.requires_services
class TestCaptioningToBSLFlow:
    """Test Captioning -> BSL Translation flow."""

    @pytest.mark.skip(reason="Requires mock audio data")
    def test_captioning_bsl_pipeline(self, base_urls, http_client):
        """Test captioning transcribe feeds into BSL translation."""
        # Step 1: Transcribe audio
        captioning_response = http_client.post(
            f"{base_urls['captioning']}/api/v1/transcribe",
            json=TestData.CAPTIONING_REQUEST,
            timeout=30
        )
        assert captioning_response.status_code == 200
        captioning_data = captioning_response.json()
        transcribed_text = captioning_data["text"]

        # Step 2: Translate to BSL gloss
        bsl_response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate",
            json={"text": transcribed_text, "preserve_format": True},
            timeout=10
        )
        assert bsl_response.status_code == 200
        bsl_data = bsl_response.json()
        assert "gloss_text" in bsl_data


@pytest.mark.requires_services
class TestOpenClawOrchestration:
    """Test OpenClaw orchestration through multiple skills."""

    def test_openclaw_coordination(self, base_urls, http_client):
        """Test OpenClaw coordinates SceneSpeak + Sentiment + Safety."""
        response = http_client.post(
            f"{base_urls['openclaw']}/v1/orchestrate",
            json=TestData.OPENCLAW_REQUEST,
            timeout=30
        )
        assert response.status_code in [200, 202]
        data = response.json()
        assert "output" in data or "status" in data


@pytest.mark.requires_services
class TestLightingSafetyIntegration:
    """Test Safety flag triggers lighting changes."""

    @pytest.mark.skip(reason="Requires safety-lighting integration setup")
    def test_safety_triggers_lighting(self, base_urls, http_client):
        """Test flagged safety content triggers lighting warning."""
        # This test would verify that when safety flags content,
        # the lighting system receives a signal to change state

        # Step 1: Submit content for safety check
        safety_response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json={"content": "Test safe content", "context": "test"},
            timeout=10
        )
        assert safety_response.status_code == 200
        safety_data = safety_response.json()

        # Step 2: Verify lighting state
        # (This would require integration between safety and lighting)
        lighting_response = http_client.get(
            f"{base_urls['lighting']}/v1/lighting/state",
            timeout=5
        )
        assert lighting_response.status_code == 200
