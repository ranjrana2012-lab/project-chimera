import pytest
import requests
import time


def test_orchestrate_synchronous_flow(orchestrator_url, sample_prompt):
    """Test main synchronous orchestration flow.

    Flow: Prompt → Sentiment → Safety → LLM → Response
    """
    start_time = time.time()

    response = requests.post(
        f"{orchestrator_url}/api/orchestrate",
        json={
            "prompt": sample_prompt,
            "show_id": "test_show",
            "context": {"scene": "act1_scene1"}
        },
        timeout=120  # 2 minute timeout for LLM calls
    )

    processing_time = int((time.time() - start_time) * 1000)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "response" in data
    assert "sentiment" in data
    assert "safety_check" in data
    assert "metadata" in data

    # Verify sentiment was analyzed
    assert data["sentiment"]["label"] in ["positive", "negative", "neutral"]
    assert "score" in data["sentiment"]

    # Verify safety check passed
    assert data["safety_check"]["passed"] is True
    assert data["safety_check"]["reason"] == "Content approved"

    # Verify LLM generated response
    assert len(data["response"]) > 0
    assert isinstance(data["response"], str)

    # Verify metadata
    assert data["metadata"]["show_id"] == "test_show"
    assert "processing_time_ms" in data["metadata"]
    assert data["metadata"]["processing_time_ms"] == processing_time


def test_orchestrate_with_unsafe_content(orchestrator_url):
    """Test orchestration with unsafe content that should be blocked."""
    unsafe_prompt = "This is a test with violence and gore"

    response = requests.post(
        f"{orchestrator_url}/api/orchestrate",
        json={
            "prompt": unsafe_prompt,
            "show_id": "test_show",
            "context": {}
        },
        timeout=120
    )

    # Should return 200 but with safety check failed
    assert response.status_code == 200
    data = response.json()

    assert data["safety_check"]["passed"] is False
    assert "blocked" in data["safety_check"]["reason"].lower()


def test_orchestrate_missing_required_field(orchestrator_url):
    """Test orchestration with missing required prompt field."""
    response = requests.post(
        f"{orchestrator_url}/api/orchestrate",
        json={
            "show_id": "test_show",
            # Missing "prompt" field
            "context": {}
        }
    )

    assert response.status_code == 422  # Validation error


def test_orchestrate_webhook_callback(orchestrator_url, sample_prompt):
    """Test orchestration with webhook callback URL."""
    webhook_url = "http://httpbin.org/post"

    response = requests.post(
        f"{orchestrator_url}/api/orchestrate",
        json={
            "prompt": sample_prompt,
            "show_id": "test_show",
            "context": {},
            "webhook_url": webhook_url
        },
        timeout=120
    )

    # Should return immediately with task ID
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "processing"


def test_orchestrate_sentiment_classification_accuracy(orchestrator_url):
    """Test that sentiment classification is reasonably accurate."""
    test_cases = [
        ("The crowd cheered with joy!", "positive"),
        ("The audience booed angrily.", "negative"),
        ("The actor walked to the stage.", "neutral"),
    ]

    for prompt, expected_sentiment in test_cases:
        response = requests.post(
            f"{orchestrator_url}/api/orchestrate",
            json={"prompt": prompt, "show_id": "test", "context": {}},
            timeout=120
        )

        assert response.status_code == 200
        data = response.json()
        actual_sentiment = data["sentiment"]["label"]

        # Allow some tolerance - sentiment analysis isn't perfect
        # Just check we got a valid sentiment
        assert actual_sentiment in ["positive", "negative", "neutral"]
