"""
Service health check integration tests.

Verifies all 8 services are healthy and ready to handle requests.
"""

import pytest
import asyncio
from httpx import AsyncClient, TimeoutException
from typing import Dict, List


@pytest.mark.integration
class TestServiceHealth:
    """Test health endpoints for all services."""

    @pytest.mark.asyncio
    async def test_openclaw_orchestrator_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test OpenClaw Orchestrator health endpoints."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        assert response.text == "OK" or response.json().get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        readiness_data = response.json()
        assert "ready" in readiness_data or "status" in readiness_data

        # Check dependencies
        if "dependencies" in readiness_data:
            deps = readiness_data["dependencies"]
            # Redis and Kafka should be OK
            assert deps.get("redis", "ok") in ["ok", "healthy"]
            assert deps.get("kafka", "ok") in ["ok", "healthy"]

    @pytest.mark.asyncio
    async def test_sentiment_agent_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test Sentiment Agent health endpoints."""
        base_url = f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]
        assert data.get("model_loaded") == True

    @pytest.mark.asyncio
    async def test_scenespeak_agent_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test SceneSpeak Agent health endpoints."""
        base_url = f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]

        # Check model status
        if "model_loaded" in data:
            assert data["model_loaded"] == True
        if "dependencies" in data:
            # Should have Redis cache check
            assert "redis" in data["dependencies"]

    @pytest.mark.asyncio
    async def test_safety_filter_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test Safety Filter health endpoints."""
        base_url = f"http://{test_config['safety_host']}:{test_config['safety_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]

    @pytest.mark.asyncio
    async def test_captioning_agent_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test Captioning Agent health endpoints."""
        base_url = f"http://{test_config['captioning_host']}:{test_config['captioning_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]

    @pytest.mark.asyncio
    async def test_bsl_text2gloss_agent_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test BSL Text2Gloss Agent health endpoints."""
        base_url = f"http://{test_config['bsl_host']}:{test_config['bsl_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness with model check
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]
        assert data.get("model_loaded") == True

    @pytest.mark.asyncio
    async def test_lighting_control_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test Lighting Control service health endpoints."""
        base_url = f"http://{test_config['lighting_host']}:{test_config['lighting_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]

    @pytest.mark.asyncio
    async def test_operator_console_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test Operator Console health endpoints."""
        base_url = f"http://{test_config['console_host']}:{test_config['console_port']}"

        # Test liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        # Test readiness
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]

        # Check detailed health if available
        response = await http_client.get(f"{base_url}/health/detailed", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            assert "components" in data or "status" in data

    @pytest.mark.asyncio
    async def test_all_services_concurrent_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test all services health checks concurrently."""
        service_urls = {
            "openclaw": f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}/health/live",
            "sentiment": f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/health/live",
            "scenespeak": f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/health/live",
            "safety": f"http://{test_config['safety_host']}:{test_config['safety_port']}/health/live",
            "captioning": f"http://{test_config['captioning_host']}:{test_config['captioning_port']}/health/live",
            "bsl": f"http://{test_config['bsl_host']}:{test_config['bsl_port']}/health/live",
            "lighting": f"http://{test_config['lighting_host']}:{test_config['lighting_port']}/health/live",
            "console": f"http://{test_config['console_host']}:{test_config['console_port']}/health/live",
        }

        # Run all health checks concurrently
        tasks = [
            http_client.get(url, timeout=5.0) for url in service_urls.values()
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all services responded
        healthy_services = []
        unhealthy_services = []

        for (service, url), response in zip(service_urls.items(), responses):
            if isinstance(response, Exception):
                unhealthy_services.append(service)
            elif response.status_code == 200:
                healthy_services.append(service)
            else:
                unhealthy_services.append(service)

        # At minimum, core services should be healthy
        assert "openclaw" in healthy_services
        assert "sentiment" in healthy_services
        assert "scenespeak" in healthy_services
        assert "safety" in healthy_services

        # Return report
        return {
            "healthy": healthy_services,
            "unhealthy": unhealthy_services,
            "total_healthy": len(healthy_services),
            "total_unhealthy": len(unhealthy_services),
        }

    @pytest.mark.asyncio
    async def test_service_startup_times(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test services have reasonable startup/uptime metrics."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            # Check for uptime metric
            if "uptime" in data:
                assert data["uptime"] >= 0

    @pytest.mark.asyncio
    async def test_service_dependency_checks(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test services properly report their dependency status."""
        # Test OpenClaw dependency checks
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if "dependencies" in data:
                deps = data["dependencies"]
                # Should check critical dependencies
                assert isinstance(deps, dict)
                # May contain: redis, kafka, gpu, etc.

        # Test SceneSpeak cache dependency
        base_url = f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}"
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if "dependencies" in data:
                assert "redis" in data["dependencies"]

    @pytest.mark.asyncio
    async def test_service_versioning(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test services report version information."""
        services = {
            "openclaw": f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}",
            "sentiment": f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}",
            "scenespeak": f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}",
        }

        for service, base_url in services.items():
            response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                # Version info is optional but recommended
                if "version" in data:
                    assert isinstance(data["version"], str)

    @pytest.mark.asyncio
    async def test_service_graceful_degradation(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test services handle degraded state appropriately."""
        # This test verifies that when a dependency is unhealthy,
        # the service reports correctly but may still function

        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            # Service may be in degraded state if dependencies are down
            # but should still respond
            assert "status" in data or "ready" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test health endpoints respond quickly."""
        services = {
            "openclaw": f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}/health/live",
            "sentiment": f"http://{test_config['sentiment_host']}:{test_config['sentiment_port']}/health/live",
            "scenespeak": f"http://{test_config['scenespeak_host']}:{test_config['scenespeak_port']}/health/live",
        }

        for service, url in services.items():
            start = asyncio.get_event_loop().time()
            try:
                response = await http_client.get(url, timeout=1.0)
                elapsed = asyncio.get_event_loop().time() - start

                # Health endpoints should be very fast (< 500ms)
                assert elapsed < 0.5, f"{service} health check took {elapsed}s"
            except TimeoutException:
                pytest.fail(f"{service} health check timed out")

    @pytest.mark.asyncio
    async def test_service_memory_and_cpu_metrics(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test services provide resource usage metrics."""
        # This is an optional check - not all services expose these
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Try to get metrics endpoint
        response = await http_client.get(f"{base_url}/metrics", timeout=5.0)

        if response.status_code == 200:
            # Should contain Prometheus-style metrics
            metrics_text = response.text
            # Check for common metric patterns
            assert any(
                pattern in metrics_text
                for pattern in ["process_", "go_", "python_", "http_"]
            )

    @pytest.mark.asyncio
    async def test_infrastructure_health(
        self, http_client: AsyncClient, test_config: dict, redis_client
    ):
        """Test infrastructure components (Redis, Kafka) health."""
        # Test Redis
        try:
            await redis_client.ping()
            redis_healthy = True
        except Exception:
            redis_healthy = False

        assert redis_healthy, "Redis is not healthy"

        # Test Redis info
        info = await redis_client.info()
        assert "redis_version" in info
        assert "used_memory_human" in info

        # Note: Kafka health check would require aiokafka client
        # Skipping for now as it requires additional setup
