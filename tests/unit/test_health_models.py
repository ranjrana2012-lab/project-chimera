# tests/unit/test_health_models.py
import pytest
from datetime import datetime
from shared.models.health import (
    DependencyHealth,
    ModelInfo,
    HealthMetrics,
    ReadinessResponse
)


def test_dependency_health_creation():
    """Test creating a dependency health status."""
    dep = DependencyHealth(
        status="healthy",
        latency_ms=42.5
    )

    assert dep.status == "healthy"
    assert dep.latency_ms == 42.5


def test_dependency_health_without_latency():
    """Test dependency health without latency."""
    dep = DependencyHealth(status="unhealthy")

    assert dep.status == "unhealthy"
    assert dep.latency_ms is None


def test_model_info_creation():
    """Test creating model info."""
    model = ModelInfo(
        loaded=True,
        name="whisper-large-v3",
        last_loaded=datetime.now()
    )

    assert model.loaded is True
    assert model.name == "whisper-large-v3"
    assert model.last_loaded is not None


def test_model_info_minimal():
    """Test model info with minimal fields."""
    model = ModelInfo(loaded=False)

    assert model.loaded is False
    assert model.name is None
    assert model.last_loaded is None


def test_health_metrics_creation():
    """Test creating health metrics."""
    metrics = HealthMetrics(
        requests_total=1000,
        errors_total=5,
        avg_latency_ms=23.4
    )

    assert metrics.requests_total == 1000
    assert metrics.errors_total == 5
    assert metrics.avg_latency_ms == 23.4


def test_health_metrics_defaults():
    """Test health metrics with default values."""
    metrics = HealthMetrics()

    assert metrics.requests_total == 0
    assert metrics.errors_total == 0
    assert metrics.avg_latency_ms == 0.0


def test_readiness_response_creation():
    """Test creating a readiness response."""
    response = ReadinessResponse(
        status="ready",
        version="1.0.0",
        uptime=3600,
        model_info=ModelInfo(
            loaded=True,
            name="test-model"
        ),
        metrics=HealthMetrics(
            requests_total=100,
            errors_total=2
        )
    )

    assert response.status == "ready"
    assert response.version == "1.0.0"
    assert response.uptime == 3600
    assert response.model_info is not None
    assert response.model_info.loaded is True
    assert response.model_info.name == "test-model"
    assert response.metrics is not None
    assert response.metrics.requests_total == 100


def test_readiness_response_with_dependencies():
    """Test readiness response with dependencies."""
    response = ReadinessResponse(
        status="ready",
        dependencies={
            "database": DependencyHealth(status="healthy", latency_ms=5.2),
            "redis": DependencyHealth(status="healthy", latency_ms=1.1),
            "external_api": DependencyHealth(status="unhealthy")
        }
    )

    assert response.status == "ready"
    assert len(response.dependencies) == 3
    assert response.dependencies["database"].status == "healthy"
    assert response.dependencies["database"].latency_ms == 5.2
    assert response.dependencies["external_api"].status == "unhealthy"


def test_readiness_response_minimal():
    """Test readiness response with minimal fields."""
    response = ReadinessResponse(status="not_ready")

    assert response.status == "not_ready"
    assert response.version is None
    assert response.uptime is None
    assert response.dependencies == {}
    assert response.model_info is None
    assert response.metrics is None


def test_readiness_response_serialization():
    """Test that readiness response can be serialized to JSON."""
    response = ReadinessResponse(
        status="ready",
        version="1.0.0",
        uptime=100,
        model_info=ModelInfo(loaded=True, name="test-model"),
        metrics=HealthMetrics(requests_total=50)
    )

    # This should not raise an exception
    data = response.model_dump()

    assert data["status"] == "ready"
    assert data["version"] == "1.0.0"
    assert data["uptime"] == 100
    assert data["model_info"]["loaded"] is True
    assert data["metrics"]["requests_total"] == 50
