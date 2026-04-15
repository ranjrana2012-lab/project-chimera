"""Service health check tests for all MVP services."""

import pytest
import subprocess
import json


@pytest.mark.integration
def test_all_services_healthy_via_docker():
    """Verify all 8 services pass Docker health check.

    This test runs 'docker compose ps' and checks that all services
    show the '(healthy)' status in their output.
    """
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.mvp.yml", "ps"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "docker compose ps command failed"

    output = result.stdout
    unhealthy_services = []

    # Service names we expect to see
    expected_services = [
        "openclaw-orchestrator",
        "scenespeak-agent",
        "sentiment-agent",
        "safety-filter",
        "operator-console",
        "redis",
        "hardware-bridge"
    ]

    for service in expected_services:
        if service not in output:
            unhealthy_services.append(f"{service}: NOT RUNNING")
        else:
            # Extract the line for this service and check if healthy
            for line in output.split('\n'):
                if service in line and "(healthy)" not in line:
                    unhealthy_services.append(f"{service}: {line.strip()}")
                    break

    if unhealthy_services:
        pytest.fail(f"Unhealthy services found:\n" + "\n".join(unhealthy_services))
