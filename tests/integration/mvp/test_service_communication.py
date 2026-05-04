"""
Project Chimera - MVP Service Communication Integration Tests

Tests service communication for the Docker Compose MVP stack. When these tests
run on the host they use published localhost ports; when they run from inside a
Compose-attached container they can use Docker DNS service names.
"""

import json
import os
import subprocess
from typing import Dict

import httpx
import pytest
import redis


def _use_internal_docker_dns() -> bool:
    """Docker service names only resolve inside the Compose network."""
    return (
        os.getenv("CHIMERA_MVP_INTERNAL_DNS", "").lower() in {"1", "true", "yes"}
        or os.path.exists("/.dockerenv")
    )


def _service_urls() -> Dict[str, str]:
    if _use_internal_docker_dns():
        return {
            "orchestrator": "http://openclaw-orchestrator:8000",
            "scenespeak": "http://scenespeak-agent:8001",
            "translation": "http://translation-agent:8002",
            "sentiment": "http://sentiment-agent:8004",
            "safety": "http://safety-filter:8006",
            "operator_console": "http://operator-console:8007",
            "hardware_bridge": "http://hardware-bridge:8008",
        }

    return {
        "orchestrator": "http://127.0.0.1:8000",
        "scenespeak": "http://127.0.0.1:8001",
        "translation": "http://127.0.0.1:8002",
        "sentiment": "http://127.0.0.1:8004",
        "safety": "http://127.0.0.1:8006",
        "operator_console": "http://127.0.0.1:8007",
        "hardware_bridge": "http://127.0.0.1:8008",
    }


def _redis_host() -> str:
    return "redis" if _use_internal_docker_dns() else os.getenv("CHIMERA_REDIS_HOST", "127.0.0.1")


class TestServiceCommunication:
    """Test service-to-service communication in MVP."""

    @pytest.fixture(scope="class")
    def docker_network(self) -> str:
        """Get the Docker network name for MVP services."""
        return "chimera-backend"

    @pytest.fixture(scope="class")
    def service_urls(self) -> Dict[str, str]:
        """Get service URLs for the current test runtime."""
        return _service_urls()

    @pytest.fixture(scope="class")
    def redis_client(self) -> redis.Redis:
        """Get Redis client for testing."""
        return redis.Redis(
            host=_redis_host(),
            port=6379,
            decode_responses=True,
            db=0,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    def test_orchestrator_to_scenespeak_agent(self, service_urls: Dict[str, str]):
        """Test orchestrator can reach scenespeak-agent."""
        response = httpx.get(f"{service_urls['scenespeak']}/health", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_orchestrator_to_sentiment_agent(self, service_urls: Dict[str, str]):
        """Test orchestrator can reach sentiment-agent."""
        response = httpx.get(f"{service_urls['sentiment']}/health", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_orchestrator_to_safety_filter(self, service_urls: Dict[str, str]):
        """Test orchestrator can reach safety-filter."""
        response = httpx.get(f"{service_urls['safety']}/health/live", timeout=5.0)
        assert response.status_code == 200

    def test_orchestrator_to_translation_agent(self, service_urls: Dict[str, str]):
        """Test orchestrator can reach translation-agent."""
        response = httpx.get(f"{service_urls['translation']}/health", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_orchestrator_to_redis(self, redis_client: redis.Redis):
        """Test Redis is reachable through the current runtime route."""
        redis_client.set("test_key", "test_value")
        result = redis_client.get("test_key")
        assert result == "test_value"
        redis_client.delete("test_key")

    def test_safety_filter_to_redis(self, redis_client: redis.Redis):
        """Test Redis state operations through the current runtime route."""
        redis_client.set("safety_test", "active")
        result = redis_client.get("safety_test")
        assert result == "active"
        redis_client.delete("safety_test")

    def test_operator_console_to_orchestrator(self, service_urls: Dict[str, str]):
        """Test operator-console can reach orchestrator."""
        response = httpx.get(f"{service_urls['orchestrator']}/health", timeout=5.0)
        assert response.status_code == 200

    def test_all_services_accessible(self, service_urls: Dict[str, str]):
        """Test all services are accessible from the current test runtime."""
        for service_name, url in service_urls.items():
            health_path = "/health/live" if service_name == "safety" else "/health"
            response = httpx.get(f"{url}{health_path}", timeout=5.0)
            assert response.status_code == 200, f"{service_name} is not accessible"

    def test_orchestrator_generate_endpoint(self, service_urls: Dict[str, str]):
        """Test orchestrator /api/generate endpoint is reachable."""
        response = httpx.post(
            f"{service_urls['orchestrator']}/api/generate",
            json={"prompt": "Test communication", "show_id": "test_show"},
            timeout=30.0,
        )
        assert response.status_code in [200, 400, 404, 500, 503]

    def test_service_discovery(self, service_urls: Dict[str, str]):
        """Test Docker DNS resolution when running inside the Compose network."""
        if not _use_internal_docker_dns():
            pytest.skip("Docker service DNS names only resolve from inside the Compose network")

        import socket

        service_hosts = {
            "openclaw-orchestrator": "openclaw-orchestrator",
            "scenespeak-agent": "scenespeak-agent",
            "translation-agent": "translation-agent",
            "sentiment-agent": "sentiment-agent",
            "safety-filter": "safety-filter",
            "operator-console": "operator-console",
            "hardware-bridge": "hardware-bridge",
            "redis": "redis",
        }

        for display_name, hostname in service_hosts.items():
            try:
                ip = socket.gethostbyname(hostname)
                assert ip is not None, f"Could not resolve {display_name}"
            except socket.gaierror as exc:
                pytest.fail(f"DNS resolution failed for {hostname}: {exc}")

    def test_network_isolation(self):
        """Test that services are on the correct Docker network."""
        if os.path.exists("/.dockerenv"):
            pytest.skip("Docker CLI not available inside container")

        candidates = [
            os.getenv("CHIMERA_MVP_NETWORK"),
            "chimera-backend",
            "chimera_chimera-backend",
            "project-chimera_chimera-backend",
        ]

        discovered = subprocess.run(
            [
                "docker",
                "network",
                "ls",
                "--filter",
                "label=com.docker.compose.network=chimera-backend",
                "--format",
                "{{.Name}}",
            ],
            capture_output=True,
            text=True,
        )
        candidates.extend(discovered.stdout.splitlines())

        result = None
        network_info = None
        for network_name in dict.fromkeys(name for name in candidates if name):
            candidate_result = subprocess.run(
                ["docker", "network", "inspect", network_name],
                capture_output=True,
                text=True,
            )
            if candidate_result.returncode != 0:
                continue

            candidate_info = json.loads(candidate_result.stdout)
            containers = candidate_info[0].get("Containers", {}) if candidate_info else {}
            result = candidate_result
            network_info = candidate_info
            if len(containers) >= 8:
                break

        assert result and result.returncode == 0, "chimera-backend network does not exist"
        assert network_info and len(network_info) > 0, "No network info returned"

        containers = network_info[0].get("Containers", {})
        assert len(containers) >= 8, f"Expected at least 8 containers, found {len(containers)}"


class TestServiceHealthEndpoints:
    """Test individual service health endpoints."""

    @pytest.fixture(scope="class")
    def service_urls(self) -> Dict[str, str]:
        """Get service URLs for the current test runtime."""
        return _service_urls()

    def test_orchestrator_health_endpoint(self, service_urls: Dict[str, str]):
        """Test orchestrator health endpoint returns proper structure."""
        response = httpx.get(f"{service_urls['orchestrator']}/health", timeout=5.0)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_scenespeak_health_endpoint(self, service_urls: Dict[str, str]):
        """Test scenespeak-agent health endpoint."""
        response = httpx.get(f"{service_urls['scenespeak']}/health", timeout=5.0)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data

    def test_sentiment_health_endpoint(self, service_urls: Dict[str, str]):
        """Test sentiment-agent health endpoint."""
        response = httpx.get(f"{service_urls['sentiment']}/health", timeout=5.0)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert (
            "model_loaded" in data
            or "mock_mode" in data
            or "model_available" in data
            or ("model_info" in data and data.get("model_info", {}).get("loaded"))
        )
