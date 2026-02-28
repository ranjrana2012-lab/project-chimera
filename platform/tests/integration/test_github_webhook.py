"""Test GitHub webhook integration."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from ci_gateway.main import ci_gateway_app

@pytest.mark.asyncio
async def test_health_check():
    """Test GET /health returns health status."""
    transport = ASGITransport(app=ci_gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ci-gateway"

@pytest.mark.asyncio
async def test_github_webhook_accepts_post():
    """Test POST /webhooks/github accepts webhook."""
    transport = ASGITransport(app=ci_gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/webhooks/github",
            json={
                "type": "push",
                "after": "abc123",
                "ref": "refs/heads/main",
                "repository": {"full_name": "test/chimera"}
            }
        )

        # Should accept without signature verification in test mode
        assert response.status_code in [200, 202]
