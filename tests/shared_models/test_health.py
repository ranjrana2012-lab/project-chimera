"""Tests for shared health models."""
import pytest
from datetime import datetime, UTC
from shared.models.health import ReadinessResponse, ModelInfo, HealthMetrics, DependencyHealth


class TestDependencyHealth:
    """Test DependencyHealth model."""

    def test_dependency_health_minimal(self):
        """Test creating dependency health with minimal fields."""
        health = DependencyHealth(status="healthy")
        assert health.status == "healthy"
        assert health.latency_ms is None

    def test_dependency_health_with_latency(self):
        """Test creating dependency health with latency."""
        health = DependencyHealth(
            status="healthy",
            latency_ms=25.5
        )
        assert health.status == "healthy"
        assert health.latency_ms == 25.5

    def test_dependency_health_statuses(self):
        """Test different dependency health statuses."""
        for status in ["healthy", "unhealthy", "unknown"]:
            health = DependencyHealth(status=status)
            assert health.status == status


class TestModelInfo:
    """Test ModelInfo model."""

    def test_model_info_minimal(self):
        """Test creating model info with required field only."""
        info = ModelInfo(loaded=True)
        assert info.loaded is True
        assert info.name is None
        assert info.last_loaded is None

    def test_model_info_with_name(self):
        """Test creating model info with name."""
        info = ModelInfo(
            loaded=True,
            name="sentiment-model-v1"
        )
        assert info.loaded is True
        assert info.name == "sentiment-model-v1"

    def test_model_info_with_last_loaded(self):
        """Test creating model info with last_loaded timestamp."""
        now = datetime.now(UTC)
        info = ModelInfo(
            loaded=True,
            name="test-model",
            last_loaded=now
        )
        assert info.loaded is True
        assert info.last_loaded == now

    def test_model_info_not_loaded(self):
        """Test model info when model is not loaded."""
        info = ModelInfo(loaded=False)
        assert info.loaded is False
        assert info.name is None
        assert info.last_loaded is None


class TestHealthMetrics:
    """Test HealthMetrics model."""

    def test_health_metrics_default_values(self):
        """Test health metrics with default values."""
        metrics = HealthMetrics()
        assert metrics.requests_total == 0
        assert metrics.errors_total == 0
        assert metrics.avg_latency_ms == 0.0

    def test_health_metrics_with_values(self):
        """Test health metrics with custom values."""
        metrics = HealthMetrics(
            requests_total=1000,
            errors_total=25,
            avg_latency_ms=45.5
        )
        assert metrics.requests_total == 1000
        assert metrics.errors_total == 25
        assert metrics.avg_latency_ms == 45.5

    def test_health_metrics_serialization(self):
        """Test health metrics serialize correctly."""
        metrics = HealthMetrics(
            requests_total=500,
            errors_total=5,
            avg_latency_ms=23.7
        )
        data = metrics.model_dump()
        assert data["requests_total"] == 500
        assert data["errors_total"] == 5
        assert data["avg_latency_ms"] == 23.7


class TestReadinessResponse:
    """Test ReadinessResponse model."""

    def test_readiness_response_minimal(self):
        """Test creating readiness response with minimal fields."""
        response = ReadinessResponse(status="ready")
        assert response.status == "ready"
        assert response.version is None
        assert response.uptime is None
        assert len(response.dependencies) == 0
        assert response.model_info is None
        assert response.metrics is None

    def test_readiness_response_not_ready(self):
        """Test creating readiness response for not ready status."""
        response = ReadinessResponse(status="not_ready")
        assert response.status == "not_ready"

    def test_readiness_response_with_version(self):
        """Test readiness response with version."""
        response = ReadinessResponse(
            status="ready",
            version="1.2.3"
        )
        assert response.status == "ready"
        assert response.version == "1.2.3"

    def test_readiness_response_with_uptime(self):
        """Test readiness response with uptime."""
        response = ReadinessResponse(
            status="ready",
            uptime=3600
        )
        assert response.status == "ready"
        assert response.uptime == 3600

    def test_readiness_response_with_dependencies(self):
        """Test readiness response with dependency health."""
        response = ReadinessResponse(
            status="ready",
            dependencies={
                "database": DependencyHealth(status="healthy", latency_ms=5.2),
                "cache": DependencyHealth(status="healthy"),
                "ml_service": DependencyHealth(status="unhealthy")
            }
        )
        assert response.status == "ready"
        assert len(response.dependencies) == 3
        assert response.dependencies["database"].status == "healthy"
        assert response.dependencies["cache"].latency_ms is None
        assert response.dependencies["ml_service"].status == "unhealthy"

    def test_readiness_response_with_model_info(self):
        """Test readiness response with model information."""
        model_info = ModelInfo(
            loaded=True,
            name="sentiment-analyzer",
            last_loaded=datetime.now(UTC)
        )
        response = ReadinessResponse(
            status="ready",
            model_info=model_info
        )
        assert response.status == "ready"
        assert response.model_info is not None
        assert response.model_info.loaded is True
        assert response.model_info.name == "sentiment-analyzer"

    def test_readiness_response_with_metrics(self):
        """Test readiness response with health metrics."""
        metrics = HealthMetrics(
            requests_total=5000,
            errors_total=10,
            avg_latency_ms=32.1
        )
        response = ReadinessResponse(
            status="ready",
            metrics=metrics
        )
        assert response.status == "ready"
        assert response.metrics is not None
        assert response.metrics.requests_total == 5000
        assert response.metrics.errors_total == 10

    def test_readiness_response_serialization(self):
        """Test readiness response serializes correctly."""
        response = ReadinessResponse(
            status="ready",
            version="2.0.0",
            uptime=7200
        )
        data = response.model_dump()
        assert data["status"] == "ready"
        assert data["version"] == "2.0.0"
        assert data["uptime"] == 7200
        assert "dependencies" in data

    def test_readiness_response_full(self):
        """Test readiness response with all fields."""
        now = datetime.now(UTC)
        response = ReadinessResponse(
            status="ready",
            version="1.0.0",
            uptime=86400,
            dependencies={
                "api": DependencyHealth(status="healthy", latency_ms=10.5)
            },
            model_info=ModelInfo(loaded=True, name="model", last_loaded=now),
            metrics=HealthMetrics(requests_total=1000, errors_total=5, avg_latency_ms=25.0)
        )
        assert response.status == "ready"
        assert response.version == "1.0.0"
        assert response.uptime == 86400
        assert len(response.dependencies) == 1
        assert response.model_info.loaded is True
        assert response.metrics.requests_total == 1000
