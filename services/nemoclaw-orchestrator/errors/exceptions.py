# services/nemoclaw-orchestrator/errors/exceptions.py
"""Custom exception hierarchy for Nemo Claw Orchestrator"""
from typing import Any, Dict, Optional


class ChimeraError(Exception):
    """
    Base exception for all Chimera/Nemo Claw errors

    Attributes:
        message: Human-readable error message
        code: Internal error code for classification
        details: Additional error details (dict)
        http_status: HTTP status code to return
    """

    def __init__(
        self,
        message: str,
        code: str = "CHIMERA_ERROR",
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 500
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class PolicyViolationError(ChimeraError):
    """
    Raised when a policy check fails

    HTTP Status: 403 Forbidden
    """

    def __init__(
        self,
        message: str,
        policy_rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if policy_rule:
            details["policy_rule"] = policy_rule
        super().__init__(
            message=message,
            code="POLICY_VIOLATION",
            details=details,
            http_status=403
        )


class LLMRoutingError(ChimeraError):
    """
    Raised when LLM routing fails

    HTTP Status: 500 Internal Server Error
    """

    def __init__(
        self,
        message: str,
        backend: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if backend:
            details["backend"] = backend
        super().__init__(
            message=message,
            code="LLM_ROUTING_ERROR",
            details=details,
            http_status=500
        )


class AgentUnavailableError(ChimeraError):
    """
    Raised when an agent service is unavailable

    HTTP Status: 503 Service Unavailable
    """

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        agent_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if agent_name:
            details["agent_name"] = agent_name
        if agent_url:
            details["agent_url"] = agent_url
        super().__init__(
            message=message,
            code="AGENT_UNAVAILABLE",
            details=details,
            http_status=503
        )


class StateTransitionError(ChimeraError):
    """
    Raised when a state transition is invalid

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        target_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state
        super().__init__(
            message=message,
            code="STATE_TRANSITION_ERROR",
            details=details,
            http_status=422
        )


class CircuitBreakerOpenError(ChimeraError):
    """
    Raised when circuit breaker is open and blocking requests

    HTTP Status: 503 Service Unavailable
    """

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        failure_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if service:
            details["service"] = service
        if failure_count is not None:
            details["failure_count"] = failure_count
        super().__init__(
            message=message,
            code="CIRCUIT_BREAKER_OPEN",
            details=details,
            http_status=503
        )


class RetryExhaustedError(ChimeraError):
    """
    Raised when all retry attempts are exhausted

    HTTP Status: 503 Service Unavailable
    """

    def __init__(
        self,
        message: str,
        attempts: Optional[int] = None,
        last_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if attempts is not None:
            details["attempts"] = attempts
        if last_error:
            details["last_error"] = last_error
        super().__init__(
            message=message,
            code="RETRY_EXHAUSTED",
            details=details,
            http_status=503
        )
