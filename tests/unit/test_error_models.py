# tests/unit/test_error_models.py
import pytest
from shared.models.errors import StandardErrorResponse, ErrorCode


def test_standard_error_response_creation():
    """Test creating a standard error response."""
    error = StandardErrorResponse(
        error="Invalid input",
        code=ErrorCode.VALIDATION_ERROR,
        detail="Field 'text' is required"
    )

    assert error.error == "Invalid input"
    assert error.code == "VALIDATION_ERROR"
    assert error.detail == "Field 'text' is required"
    assert error.retryable is False
    assert error.request_id is not None
    assert error.timestamp is not None


def test_standard_error_response_with_retryable():
    """Test error response with retryable flag."""
    error = StandardErrorResponse(
        error="Service temporarily unavailable",
        code=ErrorCode.SERVICE_UNAVAILABLE,
        retryable=True
    )

    assert error.retryable is True


def test_error_code_constants():
    """Test that all error codes are defined."""
    assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
    assert ErrorCode.SERVICE_UNAVAILABLE == "SERVICE_UNAVAILABLE"
    assert ErrorCode.TIMEOUT == "TIMEOUT"
    assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"
    assert ErrorCode.MODEL_NOT_LOADED == "MODEL_NOT_LOADED"
    assert ErrorCode.SAFETY_REJECTED == "SAFETY_REJECTED"
    assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
