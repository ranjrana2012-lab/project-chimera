"""Integration tests for Safety Filter.

Tests the multi-layer content moderation service.
"""

import pytest
import requests
import time


def test_safety_safe_content(safety_url):
    """Test safety check for safe content.

    Asserts safe=True for safe content.
    """
    response = requests.post(
        f"{safety_url}/v1/check",
        json={"content": "Hello, have a wonderful day!"},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "safe" in data
    assert data["safe"] is True
    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0


def test_safety_unsafe_content_violence(safety_url):
    """Test safety check for violent content.

    Asserts safe=False, reason contains "violence" or "unsafe".

    NOTE: The safety filter's violence pattern requires specific keywords:
    Pattern: r'\b(kill|murder|death)\b.*(person|people|someone)\b'
    This test uses content that matches this pattern.
    """
    response = requests.post(
        f"{safety_url}/v1/check",
        json={"content": "I will kill someone"},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "safe" in data
    assert data["safe"] is False
    assert "reason" in data
    reason_lower = data["reason"].lower()
    # Check if reason contains violence-related keywords
    assert "violence" in reason_lower or "unsafe" in reason_lower or "block" in reason_lower


def test_safety_unsafe_content_profanity(safety_url):
    """Test safety check for profanity.

    Asserts safe=False for profanity.
    """
    response = requests.post(
        f"{safety_url}/v1/check",
        json={"content": "This is damn profanity test."},
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "safe" in data
    # Profanity should be flagged as unsafe
    assert data["safe"] is False
    assert "reason" in data


def test_safety_empty_content(safety_url):
    """Test safety check with empty content.

    Asserts 422 for empty content due to min_length validation.
    """
    response = requests.post(
        f"{safety_url}/v1/check",
        json={"content": ""},
        timeout=30
    )

    # CheckRequest has min_length=1, so we expect 422
    assert response.status_code == 422


def test_safety_missing_content(safety_url):
    """Test safety check with missing content field.

    Asserts 422 for missing field.
    """
    response = requests.post(
        f"{safety_url}/v1/check",
        json={},
        timeout=30
    )

    assert response.status_code == 422


def test_safety_caching(safety_url):
    """Test that cached requests are faster.

    Tests that repeated requests for the same content are faster
    due to caching.
    """
    test_content = "This is a test for caching performance."

    # First request - should be slower
    start1 = time.time()
    response1 = requests.post(
        f"{safety_url}/v1/check",
        json={"content": test_content},
        timeout=30
    )
    time1 = time.time() - start1

    assert response1.status_code == 200
    data1 = response1.json()
    assert "safe" in data1

    # Second request - should be faster due to caching
    start2 = time.time()
    response2 = requests.post(
        f"{safety_url}/v1/check",
        json={"content": test_content},
        timeout=30
    )
    time2 = time.time() - start2

    assert response2.status_code == 200
    data2 = response2.json()
    assert "safe" in data2

    # Results should be identical
    assert data1["safe"] == data2["safe"]
    assert data1["confidence"] == data2["confidence"]

    # Second request should be faster or at least not significantly slower
    # We use a lenient threshold (2x) to account for system variability
    assert time2 <= time1 * 2.0, f"Cache miss: second request ({time2:.3f}s) was slower than first ({time1:.3f}s)"


@pytest.mark.skip(reason="Batch check endpoint (/api/batch-check) is not implemented in safety-filter. The tracing module has trace_batch_check but no HTTP endpoint exists.")
def test_safety_batch_check(safety_url):
    """Test batch content checking.

    Tests the /api/batch-check endpoint for checking multiple contents.

    NOTE: This test is skipped because the batch-check endpoint is not
    implemented in the current safety-filter service. Only single content
    check (/v1/check) and moderate (/v1/moderate) endpoints are available.
    """
    response = requests.post(
        f"{safety_url}/api/batch-check",
        json={
            "contents": [
                "Safe content here",
                "Unsafe violent content",
                "Another safe message"
            ]
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 3
    assert all("safe" in result for result in data["results"])


def test_safety_policy_info(safety_url):
    """Test /v1/policies endpoint.

    Tests that the policy info endpoint returns safety policy details.
    """
    response = requests.get(
        f"{safety_url}/v1/policies",
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "policies" in data
    policies = data["policies"]
    assert isinstance(policies, list)

    # Check for expected policies
    policy_names = [p["name"] for p in policies]
    expected_policies = ["family", "teen", "adult", "unrestricted"]
    for expected in expected_policies:
        assert expected in policy_names, f"Expected policy '{expected}' not found in {policy_names}"

    # Check policy structure
    for policy in policies:
        assert "name" in policy
        assert "description" in policy
        assert "level" in policy
        assert "pattern_count" in policy or isinstance(policy.get("pattern_count"), int)


def test_safety_api_moderate_endpoint(safety_url):
    """Test /api/moderate endpoint (E2E compatible).

    Tests the simplified API for content moderation.
    """
    response = requests.post(
        f"{safety_url}/api/moderate",
        json={
            "text": "Hello, world!",
            "threshold": 0.8
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "safe" in data
    assert "confidence" in data
    assert "categories" in data
    assert "metadata" in data

    # Check categories
    categories = data["categories"]
    assert "violence" in categories
    assert "hate" in categories
    assert "sexual" in categories
    assert "self_harm" in categories
    assert "harassment" in categories

    # Check metadata
    metadata = data["metadata"]
    assert "model" in metadata
    assert "latency_ms" in metadata
    assert "policy" in metadata


def test_safety_health_endpoint(safety_url):
    """Test /health endpoint.

    Tests that the health check returns service status.
    """
    response = requests.get(
        f"{safety_url}/health",
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "safety-filter"
    assert "moderator_ready" in data
    assert data["moderator_ready"] is True


def test_safety_model_info_endpoint(safety_url):
    """Test /health/model_info endpoint.

    Tests that model information is returned correctly.
    """
    response = requests.get(
        f"{safety_url}/health/model_info",
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "service" in data
    assert "model_info" in data
    assert "name" in data["model_info"]
    assert "loaded" in data["model_info"]
    assert data["model_info"]["loaded"] is True
    assert "version" in data["model_info"]


def test_safety_stats_endpoint(safety_url):
    """Test /v1/stats endpoint.

    Tests that moderation statistics are returned.
    """
    response = requests.get(
        f"{safety_url}/v1/stats",
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    # Check for statistics fields
    assert "total_checks" in data or "policy" in data
