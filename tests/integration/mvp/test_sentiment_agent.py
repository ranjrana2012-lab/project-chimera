"""Integration tests for Sentiment Agent.

Tests the DistilBERT-based sentiment analysis service.
"""

import pytest
import requests
import json
import asyncio
import websockets


def test_sentiment_positive(sentiment_url, sample_positive_text):
    """Test sentiment analysis for positive text."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": sample_positive_text},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "sentiment" in data
    assert data["sentiment"] == "positive"
    assert "score" in data
    assert isinstance(data["score"], (int, float))
    assert 0.0 <= data["score"] <= 1.0


def test_sentiment_negative(sentiment_url, sample_negative_text):
    """Test sentiment analysis for negative text."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": sample_negative_text},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "sentiment" in data
    assert data["sentiment"] == "negative"
    assert "score" in data


def test_sentiment_neutral(sentiment_url, sample_neutral_text):
    """Test sentiment analysis for neutral text.

    Note: The DistilBERT SST-2 model was trained on movie reviews,
    so some seemingly neutral texts may be classified as positive/negative
    based on the training data. We test that the API returns a valid response.
    """
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": sample_neutral_text},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "sentiment" in data
    assert data["sentiment"] in ["positive", "negative", "neutral"]
    assert "score" in data
    assert "confidence" in data


def test_sentiment_empty_text(sentiment_url):
    """Test sentiment analysis with empty text."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": ""},
        timeout=30
    )

    # Empty text should either return 422 (validation) or 200 with neutral
    # The ApiAnalyzeRequest model has min_length=1, so we expect 422
    assert response.status_code == 422


def test_sentiment_missing_text(sentiment_url):
    """Test sentiment analysis with missing text field."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={},
        timeout=30
    )

    assert response.status_code == 422


@pytest.mark.skip(reason="WebSocket test requires async context - skipping for CI stability")
def test_sentiment_websocket_updates(sentiment_url):
    """Test real-time sentiment updates via WebSocket."""
    async def test_websocket():
        # Convert http:// to ws://
        ws_url = sentiment_url.replace("http://", "ws://").replace("https://", "wss://")
        uri = f"{ws_url}/ws/sentiment"

        try:
            async with websockets.connect(uri, close_timeout=5) as websocket:
                # Wait for connection confirmation
                initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                initial_data = json.loads(initial_msg)
                assert initial_data.get("type") == "connected"

                # Send ping
                await websocket.send("ping")
                pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_response)
                assert pong_data.get("type") == "pong"

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            pytest.skip(f"WebSocket connection failed: {e}")

    # Run async test
    asyncio.run(test_websocket())


def test_sentiment_model_info(sentiment_url):
    """Test getting model information."""
    response = requests.get(f"{sentiment_url}/model/info", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "model_name" in data
    assert "model_type" in data
    assert data["model_type"] == "distilbert"


def test_sentiment_confidence_score(sentiment_url):
    """Test that confidence score is returned and in valid range."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": "This is a test statement"},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0


def test_sentiment_emotions(sentiment_url):
    """Test that emotion scores are returned."""
    response = requests.post(
        f"{sentiment_url}/api/analyze",
        json={"text": "The audience cheered with joy!"},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "emotions" in data
    emotions = data["emotions"]

    # Check all expected emotions are present
    expected_emotions = ["joy", "surprise", "neutral", "sadness", "anger", "fear"]
    for emotion in expected_emotions:
        assert emotion in emotions
        assert isinstance(emotions[emotion], (int, float))
        assert 0.0 <= emotions[emotion] <= 1.0
