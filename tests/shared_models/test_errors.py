"""Tests for shared error models."""
import pytest
from datetime import datetime, UTC
from shared.models.errors import StandardErrorResponse, ErrorCode


class TestStandardErrorResponse:
    """Tests for StandardErrorResponse model."""

    def test_create_minimal_error_response(self):
        """Test creating error response with required fields only."""
        response = StandardErrorResponse(
            error="Something went wrong",
            code="TEST_ERROR"
        )
        assert response.error == "Something went wrong"
        assert response.code == "TEST_ERROR"
        assert response.detail is None
        assert response.retryable is False
        assert isinstance(response.timestamp, datetime)
        assert len(response.request_id) == 32  # hex string

    def test_create_full_error_response(self):
        """Test creating error response with all fields."""
        now = datetime.now(UTC)
        response = StandardErrorResponse(
            error="Service unavailable",
            code=ErrorCode.SERVICE_UNAVAILABLE,
            detail="The service is temporarily unavailable",
            timestamp=now,
            request_id="test-request-id",
            retryable=True
        )
        assert response.error == "Service unavailable"
        assert response.code == ErrorCode.SERVICE_UNAVAILABLE
        assert response.detail == "The service is temporarily unavailable"
        assert response.timestamp == now
        assert response.request_id == "test-request-id"
        assert response.retryable is True

    def test_default_retryable_is_false(self):
        """Test default retryable value is False."""
        response = StandardErrorResponse(
            error="Error",
            code="ERROR"
        )
        assert response.retryable is False

    def test_default_values_are_generated(self):
        """Test default values for timestamp and request_id."""
        response = StandardErrorResponse(
            error="Error",
            code="ERROR"
        )
        assert response.timestamp is not None
        assert response.request_id is not None
        assert len(response.request_id) > 0

    def test_json_serialization(self):
        """Test error response can be serialized to JSON."""
        response = StandardErrorResponse(
            error="Test error",
            code="TEST"
        )
        json_dict = response.model_dump()
        assert "error" in json_dict
        assert "code" in json_dict
        assert json_dict["error"] == "Test error"
        assert json_dict["code"] == "TEST"


class TestErrorCode:
    """Tests for ErrorCode constants."""

    def test_error_code_constants(self):
        """Test all error code constants are defined."""
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.SERVICE_UNAVAILABLE == "SERVICE_UNAVAILABLE"
        assert ErrorCode.TIMEOUT == "TIMEOUT"
        assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"
        assert ErrorCode.MODEL_NOT_LOADED == "MODEL_NOT_LOADED"
        assert ErrorCode.SAFETY_REJECTED == "SAFETY_REJECTED"
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"

    def test_use_error_code_in_response(self):
        """Test using ErrorCode constants in error response."""
        response = StandardErrorResponse(
            error="Request timed out",
            code=ErrorCode.TIMEOUT,
            retryable=True
        )
        assert response.code == "TIMEOUT"
        assert response.retryable is True
