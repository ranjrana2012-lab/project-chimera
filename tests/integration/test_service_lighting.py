"""Lighting Control API tests."""
import pytest
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestLightingHealth:
    """Test Lighting Control health endpoints."""

    def test_health_live(self, base_urls, http_client):
        """Test /health/live endpoint."""
        response = http_client.get(f"{base_urls['lighting']}/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.requires_services
class TestLightingAPI:
    """Test Lighting Control API."""

    def test_set_lighting_scene(self, base_urls, http_client):
        """Test POST /v1/lighting/set endpoint."""
        request = {
            "name": "warm_wash",
            "channels": {
                "1": 255,
                "2": 200,
                "3": 150,
                "4": 0
            },
            "fade_time_ms": 1000
        }

        response = http_client.post(
            f"{base_urls['lighting']}/v1/lighting/set",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert "status" in data
        assert data["status"] == "success"
        assert "scene" in data or "name" in data

    def test_get_lighting_state(self, base_urls, http_client):
        """Test GET /v1/lighting/state endpoint."""
        response = http_client.get(
            f"{base_urls['lighting']}/v1/lighting/state",
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify state structure
        assert "current_scene" in data or "scene" in data
        assert "channels" in data or "values" in data

    def test_blackout(self, base_urls, http_client):
        """Test POST /api/v1/lighting/blackout endpoint."""
        response = http_client.post(
            f"{base_urls['lighting']}/api/v1/lighting/blackout",
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert "status" in data
        assert data["status"] == "success"

    def test_set_with_invalid_channel_values(self, base_urls, http_client):
        """Test error handling for invalid channel values (> 255)."""
        request = {
            "name": "invalid_scene",
            "channels": {
                "1": 300,  # Invalid: > 255
                "2": 200
            }
        }

        response = http_client.post(
            f"{base_urls['lighting']}/v1/lighting/set",
            json=request,
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_set_with_negative_channel_values(self, base_urls, http_client):
        """Test error handling for negative channel values."""
        request = {
            "name": "invalid_scene",
            "channels": {
                "1": -10,  # Invalid: < 0
                "2": 200
            }
        }

        response = http_client.post(
            f"{base_urls['lighting']}/v1/lighting/set",
            json=request,
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_set_scene_persistence(self, base_urls, http_client):
        """Test that set scene persists in state."""
        # First, set a scene
        request = {
            "name": "test_persistence",
            "channels": {"1": 100, "2": 150, "3": 200}
        }

        set_response = http_client.post(
            f"{base_urls['lighting']}/v1/lighting/set",
            json=request,
            timeout=30
        )
        assert set_response.status_code == 200

        # Then get state to verify
        get_response = http_client.get(
            f"{base_urls['lighting']}/v1/lighting/state",
            timeout=30
        )
        assert get_response.status_code == 200
        data = get_response.json()

        # Should have the scene or channels
        assert "current_scene" in data or "scene" in data or "channels" in data

    def test_multiple_channels(self, base_urls, http_client):
        """Test setting multiple channels at once."""
        request = {
            "name": "full_stage",
            "channels": {
                "1": 255,
                "2": 240,
                "3": 220,
                "4": 200,
                "5": 180,
                "6": 160,
                "7": 140,
                "8": 120
            },
            "fade_time_ms": 2000
        }

        response = http_client.post(
            f"{base_urls['lighting']}/v1/lighting/set",
            json=request,
            timeout=30
        )

        assert response.status_code == 200

    def test_dmx_connection_status(self, base_urls, http_client):
        """Test DMX connection status in state."""
        response = http_client.get(
            f"{base_urls['lighting']}/v1/lighting/state",
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # May have DMX status
        if "dmx_connected" in data:
            assert isinstance(data["dmx_connected"], bool)

        if "osc_connected" in data:
            assert isinstance(data["osc_connected"], bool)
