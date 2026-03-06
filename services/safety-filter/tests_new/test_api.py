"""
Unit tests for Safety Filter API.

Tests FastAPI endpoints including:
- Health checks
- Content moderation
- Quick safety check
- Statistics and audit log
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_liveness_probe(self, client):
        """Liveness probe returns alive status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness_probe(self, client):
        """Readiness probe returns ready status."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "safety-filter"
        assert data["moderator_ready"] is True
        assert "policy" in data


class TestModerateEndpoint:
    """Test /v1/moderate endpoint."""

    def test_moderate_safe_content(self, client):
        """Safe content passes moderation."""
        response = client.post("/v1/moderate", json={
            "content": "Hello, how are you today?",
            "content_id": "msg-123"
        })

        assert response.status_code == 200

        data = response.json()
        assert data["safe"] is True
        assert data["result"]["is_safe"] is True
        assert data["result"]["action"] == "allow"
        assert data["result"]["level"] == "safe"

    def test_moderate_unsafe_content(self, client):
        """Unsafe content is blocked."""
        response = client.post("/v1/moderate", json={
            "content": "damn this content",
            "content_id": "msg-456"
        })

        assert response.status_code == 200

        data = response.json()
        assert data["safe"] is False
        assert data["result"]["is_safe"] is False
        assert data["result"]["action"] == "block"
        assert len(data["result"]["matched_patterns"]) > 0

    def test_moderate_with_user_context(self, client):
        """User and session context is accepted."""
        response = client.post("/v1/moderate", json={
            "content": "Hello world",
            "user_id": "user-123",
            "session_id": "session-456"
        })

        assert response.status_code == 200
        assert response.json()["safe"] is True

    def test_moderate_with_policy(self, client):
        """Policy can be specified."""
        response = client.post("/v1/moderate", json={
            "content": "Hello world",
            "policy": "teen"
        })

        assert response.status_code == 200

    def test_moderate_with_context(self, client):
        """Additional context can be provided."""
        response = client.post("/v1/moderate", json={
            "content": "Hello world",
            "context": {"show_id": "test-show", "scene": 1}
        })

        assert response.status_code == 200

    def test_moderate_empty_content(self, client):
        """Empty content is rejected."""
        response = client.post("/v1/moderate", json={
            "content": ""
        })

        assert response.status_code == 422  # Validation error

    def test_moderate_missing_content(self, client):
        """Missing content field is rejected."""
        response = client.post("/v1/moderate", json={})

        assert response.status_code == 422  # Validation error


class TestCheckEndpoint:
    """Test /v1/check endpoint."""

    def test_check_safe_content(self, client):
        """Safe content returns true."""
        response = client.post("/v1/check", json={
            "content": "Hello world",
            "policy": "family"
        })

        assert response.status_code == 200

        data = response.json()
        assert data["safe"] is True
        assert data["confidence"] == 1.0

    def test_check_unsafe_content(self, client):
        """Unsafe content returns false."""
        response = client.post("/v1/check", json={
            "content": "damn this",
            "policy": "family"
        })

        assert response.status_code == 200

        data = response.json()
        assert data["safe"] is False
        assert "reason" in data

    def test_check_default_policy(self, client):
        """Default policy is used when not specified."""
        response = client.post("/v1/check", json={
            "content": "Hello world"
        })

        assert response.status_code == 200


class TestStatsEndpoint:
    """Test /v1/stats endpoint."""

    def test_get_statistics(self, client):
        """Statistics endpoint returns data."""
        # First moderate some content
        client.post("/v1/moderate", json={"content": "Hello world"})
        client.post("/v1/moderate", json={"content": "damn this"})

        # Get stats
        response = client.get("/v1/stats")

        assert response.status_code == 200

        data = response.json()
        assert "total_checks" in data
        assert data["total_checks"] >= 2
        assert "allowed" in data
        assert "blocked" in data
        assert "allow_rate" in data
        assert "block_rate" in data
        assert "current_policy" in data


class TestAuditEndpoint:
    """Test /v1/audit endpoint."""

    def test_get_audit_log(self, client):
        """Audit log returns entries."""
        # First moderate some content
        client.post("/v1/moderate", json={
            "content": "Hello world",
            "user_id": "user-123"
        })

        # Get audit log
        response = client.get("/v1/audit")

        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "entries" in data
        assert len(data["entries"]) >= 1

    def test_audit_log_limit(self, client):
        """Audit log respects limit parameter."""
        # Moderate multiple items
        for i in range(5):
            client.post("/v1/moderate", json={"content": f"content {i}"})

        # Get with limit
        response = client.get("/v1/audit?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) <= 3

    def test_audit_log_user_filter(self, client):
        """Audit log can be filtered by user."""
        # Moderate for different users
        client.post("/v1/moderate", json={
            "content": "content 1",
            "user_id": "user-a"
        })
        client.post("/v1/moderate", json={
            "content": "content 2",
            "user_id": "user-b"
        })

        # Get audit log for user-a
        response = client.get("/v1/audit?user_id=user-a")

        assert response.status_code == 200
        data = response.json()
        # All entries should be for user-a
        for entry in data["entries"]:
            assert entry.get("user_id") == "user-a"


class TestPoliciesEndpoint:
    """Test /v1/policies endpoint."""

    def test_list_policies(self, client):
        """Policies endpoint returns available policies."""
        response = client.get("/v1/policies")

        assert response.status_code == 200

        data = response.json()
        assert "policies" in data
        assert len(data["policies"]) > 0

        # Check for expected policies
        policy_names = [p["name"] for p in data["policies"]]
        assert "family" in policy_names
        assert "teen" in policy_names
        assert "adult" in policy_names
        assert "unrestricted" in policy_names

    def test_policy_structure(self, client):
        """Policy objects have correct structure."""
        response = client.get("/v1/policies")

        data = response.json()
        policy = data["policies"][0]

        assert "name" in policy
        assert "description" in policy
        assert "level" in policy


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

        # Check for Prometheus metrics format
        content = response.text
        assert "# HELP" in content or "safety_" in content


class TestIntegration:
    """Integration tests for the API."""

    def test_full_moderation_workflow(self, client):
        """Test complete moderation workflow."""
        # 1. Moderate safe content
        response1 = client.post("/v1/moderate", json={
            "content": "Hello, welcome to the show!"
        })
        assert response1.json()["safe"] is True

        # 2. Moderate unsafe content
        response2 = client.post("/v1/moderate", json={
            "content": "damn this is bad"
        })
        assert response2.json()["safe"] is False

        # 3. Check statistics
        response3 = client.get("/v1/stats")
        stats = response3.json()
        assert stats["total_checks"] >= 2

        # 4. Get audit log
        response4 = client.get("/v1/audit")
        audit = response4.json()
        assert len(audit["entries"]) >= 2

    def test_quick_check_workflow(self, client):
        """Test quick check workflow."""
        # Safe content
        response1 = client.post("/v1/check", json={
            "content": "Hello world"
        })
        assert response1.json()["safe"] is True

        # Unsafe content
        response2 = client.post("/v1/check", json={
            "content": "damn this"
        })
        assert response2.json()["safe"] is False
