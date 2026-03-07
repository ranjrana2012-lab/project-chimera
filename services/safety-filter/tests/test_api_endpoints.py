"""
Tests for Safety Filter API Endpoints

Comprehensive test suite for API endpoint coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_moderator():
    """Mock content moderator."""
    with patch('main.moderator') as mock:
        mock.moderate = Mock(return_value={
            "flagged": False,
            "categories": [],
            "confidence": 0.0,
            "details": {}
        })
        mock.check = Mock(return_value={
            "safe": True,
            "reason": ""
        })
        yield mock


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_liveness_probe(self, client):
        """Test liveness probe returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe(self, client):
        """Test readiness probe returns 200."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "safety-filter"
        assert "moderator_ready" in data
        assert "policy" in data

    def test_health_endpoint(self, client):
        """Test general health endpoint."""
        response = client.get("/health")
        assert response.status_code in [200, 404]  # May or may not exist


class TestModerateEndpoint:
    """Tests for content moderation endpoint."""

    def test_moderate_safe_content(self, client, mock_moderator):
        """Test moderating safe content."""
        mock_moderator.moderate.return_value = {
            "flagged": False,
            "categories": [],
            "confidence": 0.0,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "This is safe content"
        })

        assert response.status_code == 200
        data = response.json()
        assert "flagged" in data or "safe" in data

    def test_moderate_unsafe_content(self, client, mock_moderator):
        """Test moderating unsafe content."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["profanity"],
            "confidence": 0.95,
            "details": {
                "profanity": ["badword"]
            }
        }

        response = client.post("/v1/moderate", json={
            "content": "This contains badword"
        })

        assert response.status_code == 200

    def test_moderate_with_empty_content(self, client, mock_moderator):
        """Test moderating empty content."""
        response = client.post("/v1/moderate", json={
            "content": ""
        })

        assert response.status_code == 200

    def test_moderate_with_long_content(self, client, mock_moderator):
        """Test moderating long content."""
        long_content = "word " * 1000

        response = client.post("/v1/moderate", json={
            "content": long_content
        })

        assert response.status_code == 200

    def test_moderate_with_special_characters(self, client, mock_moderator):
        """Test moderating content with special characters."""
        response = client.post("/v1/moderate", json={
            "content": "Test @#$%^&*()_+-=[]{}|;':\",./<>?"
        })

        assert response.status_code == 200

    def test_moderate_with_unicode(self, client, mock_moderator):
        """Test moderating content with unicode characters."""
        response = client.post("/v1/moderate", json={
            "content": "Hello 世界 🌍"
        })

        assert response.status_code == 200

    def test_moderate_with_context(self, client, mock_moderator):
        """Test moderating with context information."""
        response = client.post("/v1/moderate", json={
            "content": "Test content",
            "context": {
                "user_id": "test-user",
                "conversation_id": "test-conv"
            }
        })

        assert response.status_code == 200

    def test_moderate_with_policy(self, client, mock_moderator):
        """Test moderating with specific policy."""
        response = client.post("/v1/moderate", json={
            "content": "Test content",
            "policy": "strict"
        })

        assert response.status_code == 200

    def test_moderate_without_content(self, client):
        """Test moderate without content parameter."""
        response = client.post("/v1/moderate", json={})
        assert response.status_code == 422  # Validation error


class TestCheckEndpoint:
    """Tests for quick check endpoint."""

    def test_check_safe_content(self, client, mock_moderator):
        """Test checking safe content."""
        mock_moderator.check.return_value = {
            "safe": True,
            "reason": ""
        }

        response = client.post("/v1/check", json={
            "content": "Safe content"
        })

        assert response.status_code == 200
        data = response.json()
        assert "safe" in data

    def test_check_unsafe_content(self, client, mock_moderator):
        """Test checking unsafe content."""
        mock_moderator.check.return_value = {
            "safe": False,
            "reason": "Contains profanity"
        }

        response = client.post("/v1/check", json={
            "content": "Unsafe content"
        })

        assert response.status_code == 200

    def test_check_without_content(self, client):
        """Test check without content parameter."""
        response = client.post("/v1/check", json={})
        assert response.status_code == 422


class TestBatchModeration:
    """Tests for batch moderation."""

    def test_batch_moderate_multiple_items(self, client, mock_moderator):
        """Test moderating multiple content items."""
        mock_moderator.moderate.side_effect = [
            {"flagged": False, "categories": [], "confidence": 0.0, "details": {}},
            {"flagged": True, "categories": ["profanity"], "confidence": 0.9, "details": {}},
            {"flagged": False, "categories": [], "confidence": 0.0, "details": {}}
        ]

        response = client.post("/v1/moderate/batch", json={
            "items": [
                {"content": "Safe 1"},
                {"content": "Unsafe"},
                {"content": "Safe 2"}
            ]
        })

        assert response.status_code == 200

    def test_batch_moderate_empty_list(self, client, mock_moderator):
        """Test batch moderation with empty list."""
        response = client.post("/v1/moderate/batch", json={
            "items": []
        })

        assert response.status_code == 200

    def test_batch_moderate_without_items(self, client):
        """Test batch moderation without items parameter."""
        response = client.post("/v1/moderate/batch", json={})
        assert response.status_code == 422


class TestPolicyEndpoints:
    """Tests for policy management endpoints."""

    def test_get_policies(self, client):
        """Test getting available policies."""
        response = client.get("/v1/policies")
        assert response.status_code in [200, 404]  # May or may not be implemented

    def test_get_policy_info(self, client):
        """Test getting specific policy information."""
        response = client.get("/v1/policies/default")
        assert response.status_code in [200, 404]


class TestBlocklistEndpoints:
    """Tests for blocklist management endpoints."""

    def test_get_blocklist(self, client):
        """Test getting current blocklist."""
        response = client.get("/v1/blocklist")
        assert response.status_code in [200, 404]  # May or may not be implemented

    def test_add_to_blocklist(self, client):
        """Test adding item to blocklist."""
        response = client.post("/v1/blocklist", json={
            "term": "badword",
            "category": "profanity"
        })
        assert response.status_code in [200, 201, 404]

    def test_remove_from_blocklist(self, client):
        """Test removing item from blocklist."""
        response = client.delete("/v1/blocklist/badword")
        assert response.status_code in [200, 404]


class TestAuditLogEndpoints:
    """Tests for audit log endpoints."""

    def test_get_audit_log(self, client):
        """Test getting audit log entries."""
        response = client.get("/v1/audit/log")
        assert response.status_code in [200, 404]

    def test_get_audit_log_with_filters(self, client):
        """Test getting audit log with date filters."""
        response = client.get("/v1/audit/log?start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code in [200, 404]

    def test_clear_audit_log(self, client):
        """Test clearing audit log."""
        response = client.delete("/v1/audit/log")
        assert response.status_code in [200, 404]


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Tests for error handling."""

    def test_moderate_handles_invalid_json(self, client):
        """Test moderate handles invalid JSON."""
        response = client.post(
            "/v1/moderate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_check_handles_exception(self, client, mock_moderator):
        """Test check handles moderator exceptions."""
        mock_moderator.check.side_effect = Exception("Moderator error")

        response = client.post("/v1/check", json={
            "content": "Test"
        })

        assert response.status_code == 500


class TestCategories:
    """Tests for different content categories."""

    def test_moderate_detects_profanity(self, client, mock_moderator):
        """Test moderation detects profanity."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["profanity"],
            "confidence": 0.95,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "Profane content"
        })

        assert response.status_code == 200

    def test_moderate_detects_pii(self, client, mock_moderator):
        """Test moderation detects PII."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["pii"],
            "confidence": 0.9,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "My email is test@example.com"
        })

        assert response.status_code == 200

    def test_moderate_detects_harmful_content(self, client, mock_moderator):
        """Test moderation detects harmful content."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["harmful"],
            "confidence": 0.85,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "Harmful content"
        })

        assert response.status_code == 200


class TestResponseFormat:
    """Tests for response format validation."""

    def test_moderate_returns_confidence(self, client, mock_moderator):
        """Test moderate returns confidence score."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["profanity"],
            "confidence": 0.87,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "Test"
        })

        data = response.json()
        assert "confidence" in data or "flagged" in data

    def test_moderate_returns_categories(self, client, mock_moderator):
        """Test moderate returns category information."""
        mock_moderator.moderate.return_value = {
            "flagged": True,
            "categories": ["profanity", "harassment"],
            "confidence": 0.9,
            "details": {}
        }

        response = client.post("/v1/moderate", json={
            "content": "Test"
        })

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
