"""
Integration tests for Director Agent

Tests show definition loading, execution, and agent coordination.
"""

import pytest
import asyncio
import httpx
from pathlib import Path

# Test configuration
DIRECTOR_URL = "http://localhost:8013"
SHOWS_DIR = Path(__file__).parent.parent / "shows"


class TestDirectorAgent:
    """Test suite for Director Agent."""

    @pytest.fixture
    async def client(self):
        """HTTP client for testing."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get(f"{DIRECTOR_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "shows_loaded" in data

    @pytest.mark.asyncio
    async def test_list_shows(self, client):
        """Test listing available shows."""
        response = await client.get(f"{DIRECTOR_URL}/api/shows")

        assert response.status_code == 200
        data = response.json()
        assert "shows" in data
        assert isinstance(data["shows"], list)

    @pytest.mark.asyncio
    async def test_get_show(self, client):
        """Test getting specific show details."""
        # First list shows to get a valid show_id
        list_response = await client.get(f"{DIRECTOR_URL}/api/shows")
        shows = list_response.json()["shows"]

        if shows:
            show_id = shows[0]["show_id"]
            response = await client.get(f"{DIRECTOR_URL}/api/shows/{show_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["show_id"] == show_id
            assert "metadata" in data
            assert "scenes" in data

    @pytest.mark.asyncio
    async def test_load_show(self, client):
        """Test loading a show from file."""
        show_file = SHOWS_DIR / "welcome_show.yaml"

        if not show_file.exists():
            pytest.skip("Show file not found")

        response = await client.post(
            f"{DIRECTOR_URL}/api/shows/load",
            json={
                "show_id": "test_integration_show",
                "file_path": str(show_file)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["show_id"] == "test_integration_show"
        assert "title" in data

    @pytest.mark.asyncio
    async def test_start_show(self, client):
        """Test starting show execution."""
        # Load show first
        show_file = SHOWS_DIR / "welcome_show.yaml"

        if not show_file.exists():
            pytest.skip("Show file not found")

        load_response = await client.post(
            f"{DIRECTOR_URL}/api/shows/load",
            json={
                "show_id": "test_start_show",
                "file_path": str(show_file)
            }
        )

        if load_response.status_code != 200:
            pytest.skip("Could not load show")

        # Start show
        response = await client.post(
            f"{DIRECTOR_URL}/api/shows/test_start_show/start",
            json={
                "start_scene": 0,
                "require_approval": False  # Auto-run for testing
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["show_id"] == "test_start_show"

        # Wait a bit for execution to start
        await asyncio.sleep(2)

        # Get state
        state_response = await client.get(
            f"{DIRECTOR_URL}/api/shows/test_start_show/state"
        )

        assert state_response.status_code == 200
        state_data = state_response.json()
        assert "state" in state_data

        # Clean up - stop show
        await client.post(f"{DIRECTOR_URL}/api/shows/test_start_show/stop")

    @pytest.mark.asyncio
    async def test_pause_resume_show(self, client):
        """Test pausing and resuming show."""
        # This test requires a show to be running
        # For now, we'll just test the endpoints respond

        # Try to pause (may fail if show not running, that's ok)
        pause_response = await client.post(
            f"{DIRECTOR_URL}/api/shows/nonexistent/pause"
        )

        # Should get 404 for non-existent show
        assert pause_response.status_code in [404, 400]

    @pytest.mark.asyncio
    async def test_emergency_stop(self, client):
        """Test emergency stop functionality."""
        # Try to stop non-existent show
        response = await client.post(
            f"{DIRECTOR_URL}/api/shows/nonexistent/stop"
        )

        # Should handle gracefully
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_show_state(self, client):
        """Test getting show state."""
        response = await client.get(
            f"{DIRECTOR_URL}/api/shows/nonexistent/state"
        )

        # Should return 404 for non-existent show
        assert response.status_code == 404


class TestShowDefinition:
    """Test show definition schema."""

    def test_load_welcome_show(self):
        """Test loading welcome show definition."""
        from show_definition import load_show_definition_from_file

        show_file = SHOWS_DIR / "welcome_show.yaml"

        if not show_file.exists():
            pytest.skip("Show file not found")

        show = load_show_definition_from_file(show_file)

        assert show.metadata.title is not None
        assert len(show.scenes) > 0
        assert all(scene.id for scene in show.scenes)
        assert all(scene.actions for scene in show.scenes)

    def test_load_adaptive_show(self):
        """Test loading adaptive show definition."""
        from show_definition import load_show_definition_from_file

        show_file = SHOWS_DIR / "adaptive_show.yaml"

        if not show_file.exists():
            pytest.skip("Show file not found")

        show = load_show_definition_from_file(show_file)

        assert show.metadata.title is not None
        assert show.metadata.enable_sentiment_adaptation is True
        assert len(show.scenes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
