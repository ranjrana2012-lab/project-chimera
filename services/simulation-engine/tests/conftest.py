"""Test configuration and fixtures."""
import pytest
import sys
from prometheus_client import CollectorRegistry, REGISTRY


# Clean prometheus registry at import time to avoid duplicate metrics
for collector in list(REGISTRY._collector_to_names.keys()):
    REGISTRY.unregister(collector)


@pytest.fixture(autouse=True)
def clean_prometheus_registry():
    """Clean prometheus registry before each test to avoid duplicate metrics."""
    # Clear the default registry
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)
    yield
    # Clean up after test
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)


@pytest.fixture
def sample_documents():
    """Sample documents for testing graph building."""
    return [
        "Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976.",
        "Steve Jobs was the CEO of Apple until 2011.",
        "Cupertino is located in Santa Clara County, California."
    ]


@pytest.fixture
def sample_simulation_config():
    """Sample simulation configuration for testing."""
    from simulation.models import SimulationConfig

    return SimulationConfig(
        agent_count=10,
        simulation_rounds=3,
        scenario_description="Test scenario for basic simulation",
        scenario_type="test"
    )
