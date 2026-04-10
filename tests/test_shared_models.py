"""
Tests for shared/models module.

Tests the data models used across Project Chimera services.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from models.errors import StandardErrorResponse, ErrorCode
from models.health import DependencyHealth, ModelInfo, HealthMetrics, ReadinessResponse


class TestStandardErrorResponse:
    """Tests for StandardErrorResponse model."""

    def test_required_fields(self):
        """Verify required fields are enforced."""
        response = StandardErrorResponse(
            error="Invalid input",
            code="VALIDATION_ERROR"
        )
        assert response.error == "Invalid input"
        assert response.code == "VALIDATION_ERROR"

    def test_optional_detail(self):
        """Verify detail field is optional."""
        response = StandardErrorResponse(
            error="Invalid input",
            code="VALIDATION_ERROR",
            detail="Field 'name' is required"
        )
        assert response.detail == "Field 'name' is required"

    def test_default_timestamp(self):
        """Verify timestamp is auto-generated."""
        before = datetime.now(timezone.utc)
        response = StandardErrorResponse(
            error="Error",
            code="INTERNAL_ERROR"
        )
        after = datetime.now(timezone.utc)
        assert before <= response.timestamp <= after

    def test_default_request_id(self):
        """Verify request_id is auto-generated."""
        response1 = StandardErrorResponse(error="E", code="CODE")
        response2 = StandardErrorResponse(error="E", code="CODE")
        assert response1.request_id != response2.request_id
        assert len(response1.request_id) == 32  # hex string

    def test_default_retryable(self):
        """Verify retryable defaults to False."""
        response = StandardErrorResponse(error="E", code="CODE")
        assert response.retryable is False

    def test_retryable_can_be_set(self):
        """Verify retryable can be set to True."""
        response = StandardErrorResponse(
            error="Timeout",
            code="TIMEOUT",
            retryable=True
        )
        assert response.retryable is True

    def test_model_serialization(self):
        """Verify model can be serialized to dict."""
        response = StandardErrorResponse(
            error="Error",
            code="CODE",
            detail="Details"
        )
        data = response.model_dump()
        assert data["error"] == "Error"
        assert data["code"] == "CODE"
        assert data["detail"] == "Details"
        assert "timestamp" in data
        assert "request_id" in data

    def test_model_json(self):
        """Verify model can be serialized to JSON."""
        response = StandardErrorResponse(
            error="Error",
            code="CODE"
        )
        json_str = response.model_dump_json()
        assert "Error" in json_str
        assert "CODE" in json_str


class TestErrorCode:
    """Tests for ErrorCode constants."""

    def test_validation_error(self):
        """Verify VALIDATION_ERROR constant."""
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"

    def test_service_unavailable(self):
        """Verify SERVICE_UNAVAILABLE constant."""
        assert ErrorCode.SERVICE_UNAVAILABLE == "SERVICE_UNAVAILABLE"

    def test_timeout(self):
        """Verify TIMEOUT constant."""
        assert ErrorCode.TIMEOUT == "TIMEOUT"

    def test_rate_limited(self):
        """Verify RATE_LIMITED constant."""
        assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"

    def test_model_not_loaded(self):
        """Verify MODEL_NOT_LOADED constant."""
        assert ErrorCode.MODEL_NOT_LOADED == "MODEL_NOT_LOADED"

    def test_safety_rejected(self):
        """Verify SAFETY_REJECTED constant."""
        assert ErrorCode.SAFETY_REJECTED == "SAFETY_REJECTED"

    def test_internal_error(self):
        """Verify INTERNAL_ERROR constant."""
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


class TestDependencyHealth:
    """Tests for DependencyHealth model."""

    def test_required_status(self):
        """Verify status is required."""
        dep = DependencyHealth(status="healthy")
        assert dep.status == "healthy"

    def test_optional_latency_ms(self):
        """Verify latency_ms is optional."""
        dep = DependencyHealth(status="healthy")
        assert dep.latency_ms is None

    def test_latency_ms_can_be_set(self):
        """Verify latency_ms can be set."""
        dep = DependencyHealth(status="healthy", latency_ms=12.5)
        assert dep.latency_ms == 12.5

    def test_valid_statuses(self):
        """Verify valid status values."""
        for status in ["healthy", "unhealthy", "unknown"]:
            dep = DependencyHealth(status=status)
            assert dep.status == status


class TestModelInfo:
    """Tests for ModelInfo model."""

    def test_required_loaded(self):
        """Verify loaded is required."""
        info = ModelInfo(loaded=True)
        assert info.loaded is True

    def test_optional_name(self):
        """Verify name is optional."""
        info = ModelInfo(loaded=True)
        assert info.name is None

    def test_name_can_be_set(self):
        """Verify name can be set."""
        info = ModelInfo(loaded=True, name="sentiment-v1")
        assert info.name == "sentiment-v1"

    def test_optional_last_loaded(self):
        """Verify last_loaded is optional."""
        info = ModelInfo(loaded=False)
        assert info.last_loaded is None

    def test_last_loaded_can_be_set(self):
        """Verify last_loaded can be set."""
        now = datetime.now(timezone.utc)
        info = ModelInfo(loaded=True, last_loaded=now)
        assert info.last_loaded == now

    def test_not_loaded_model(self):
        """Verify model info for not loaded model."""
        info = ModelInfo(loaded=False)
        assert info.loaded is False
        assert info.name is None
        assert info.last_loaded is None


class TestHealthMetrics:
    """Tests for HealthMetrics model."""

    def test_defaults(self):
        """Verify default values."""
        metrics = HealthMetrics()
        assert metrics.requests_total == 0
        assert metrics.errors_total == 0
        assert metrics.avg_latency_ms == 0.0

    def test_custom_values(self):
        """Verify custom values can be set."""
        metrics = HealthMetrics(
            requests_total=1000,
            errors_total=5,
            avg_latency_ms=23.4
        )
        assert metrics.requests_total == 1000
        assert metrics.errors_total == 5
        assert metrics.avg_latency_ms == 23.4

    def test_error_rate_calculation(self):
        """Verify error rate can be calculated."""
        metrics = HealthMetrics(
            requests_total=100,
            errors_total=5
        )
        error_rate = metrics.errors_total / metrics.requests_total
        assert error_rate == 0.05


class TestReadinessResponse:
    """Tests for ReadinessResponse model."""

    def test_required_status(self):
        """Verify status is required."""
        response = ReadinessResponse(status="ready")
        assert response.status == "ready"

    def test_optional_version(self):
        """Verify version is optional."""
        response = ReadinessResponse(status="ready")
        assert response.version is None

    def test_version_can_be_set(self):
        """Verify version can be set."""
        response = ReadinessResponse(status="ready", version="1.0.0")
        assert response.version == "1.0.0"

    def test_optional_uptime(self):
        """Verify uptime is optional."""
        response = ReadinessResponse(status="ready")
        assert response.uptime is None

    def test_uptime_can_be_set(self):
        """Verify uptime can be set."""
        response = ReadinessResponse(status="ready", uptime=3600)
        assert response.uptime == 3600

    def test_optional_dependencies(self):
        """Verify dependencies is optional."""
        response = ReadinessResponse(status="ready")
        assert response.dependencies == {}

    def test_dependencies_can_be_set(self):
        """Verify dependencies can be set."""
        response = ReadinessResponse(
            status="ready",
            dependencies={
                "database": DependencyHealth(status="healthy", latency_ms=5.2),
                "cache": DependencyHealth(status="healthy")
            }
        )
        assert len(response.dependencies) == 2
        assert response.dependencies["database"].status == "healthy"
        assert response.dependencies["cache"].status == "healthy"

    def test_optional_model_info(self):
        """Verify model_info is optional."""
        response = ReadinessResponse(status="ready")
        assert response.model_info is None

    def test_model_info_can_be_set(self):
        """Verify model_info can be set."""
        response = ReadinessResponse(
            status="ready",
            model_info=ModelInfo(loaded=True, name="model-v1")
        )
        assert response.model_info is not None
        assert response.model_info.loaded is True
        assert response.model_info.name == "model-v1"

    def test_optional_metrics(self):
        """Verify metrics is optional."""
        response = ReadinessResponse(status="ready")
        assert response.metrics is None

    def test_metrics_can_be_set(self):
        """Verify metrics can be set."""
        response = ReadinessResponse(
            status="ready",
            metrics=HealthMetrics(requests_total=100, errors_total=2)
        )
        assert response.metrics is not None
        assert response.metrics.requests_total == 100
        assert response.metrics.errors_total == 2

    def test_full_readiness_response(self):
        """Verify complete readiness response."""
        response = ReadinessResponse(
            status="ready",
            version="2.1.0",
            uptime=86400,
            dependencies={
                "database": DependencyHealth(status="healthy", latency_ms=3.5),
                "api": DependencyHealth(status="unhealthy")
            },
            model_info=ModelInfo(loaded=True, name="sentiment-v2"),
            metrics=HealthMetrics(
                requests_total=5000,
                errors_total=10,
                avg_latency_ms=45.2
            )
        )
        assert response.status == "ready"
        assert response.version == "2.1.0"
        assert response.uptime == 86400
        assert len(response.dependencies) == 2
        assert response.model_info.name == "sentiment-v2"
        assert response.metrics.requests_total == 5000

    def test_not_ready_response(self):
        """Verify not_ready status."""
        response = ReadinessResponse(
            status="not_ready",
            dependencies={
                "database": DependencyHealth(status="unhealthy")
            }
        )
        assert response.status == "not_ready"


class TestModuleExports:
    """Tests for module exports."""

    def test_error_models_exported(self):
        """Verify error models are exported."""
        from models import errors
        assert hasattr(errors, 'StandardErrorResponse')
        assert hasattr(errors, 'ErrorCode')

    def test_health_models_exported(self):
        """Verify health models are exported."""
        from models import health
        assert hasattr(health, 'DependencyHealth')
        assert hasattr(health, 'ModelInfo')
        assert hasattr(health, 'HealthMetrics')
        assert hasattr(health, 'ReadinessResponse')

    def test_models_init_exports(self):
        """Verify models/__init__.py exports all classes."""
        from models import (
            DependencyHealth,
            ModelInfo,
            HealthMetrics,
            ReadinessResponse,
            StandardErrorResponse,
            ErrorCode
        )
        assert DependencyHealth is not None
        assert ModelInfo is not None
        assert HealthMetrics is not None
        assert ReadinessResponse is not None
        assert StandardErrorResponse is not None
        assert ErrorCode is not None
