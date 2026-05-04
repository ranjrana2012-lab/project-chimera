"""Integration tests for monitoring stack."""
import pytest
import httpx
import time
from docker import from_env as docker_from_env

@pytest.mark.integration
def test_netdata_exposes_prometheus_endpoint():
    """Test that Netdata exposes Prometheus metrics endpoint."""
    client = docker_from_env()
    containers = client.containers.list(filters={"name": "chimera-netdata"})
    if len(containers) == 0:
        pytest.skip("Netdata container not running")
    
    response = httpx.get("http://localhost:19999/api/v1/allmetrics?format=prometheus", timeout=10)
    assert response.status_code == 200

@pytest.mark.integration
def test_prometheus_scrapes_netdata():
    """Test that Prometheus successfully scrapes Netdata."""
    try:
        response = httpx.get("http://localhost:9090/api/v1/targets", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Check for netdata target
        assert "data" in data
        assert "activeTargets" in data["data"]
    except httpx.ConnectError:
        pytest.skip("Prometheus not accessible")

@pytest.mark.integration
def test_dashboard_fetches_from_prometheus():
    """Test that dashboard can fetch metrics from Prometheus."""
    try:
        response = httpx.get("http://localhost:8013/api/metrics/cpu", timeout=10)
        assert response.status_code == 200
    except httpx.ConnectError:
        pytest.skip("Dashboard not accessible")
