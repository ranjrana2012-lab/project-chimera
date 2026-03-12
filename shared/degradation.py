# shared/degradation.py
"""Graceful degradation modes for Project Chimera.

This module provides degradation levels and management to allow services
to continue operating at reduced capacity when dependencies are failing.
"""

import logging
import threading
from enum import Enum
from typing import Any, Callable, TypeVar, cast, ParamSpec
from functools import wraps
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = ParamSpec('P')


class DegradationLevel(Enum):
    """Service degradation levels."""
    FULL = "full"  # All features available
    REDUCED = "reduced"  # Some features disabled, core functionality available
    BASIC = "basic"  # Only basic functionality available
    OFFLINE = "offline"  # Service unavailable, minimal or no functionality


class ServiceCapability(Enum):
    """Service capabilities that can be degraded."""
    ML_INFERENCE = "ml_inference"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    CACHE = "cache"
    WEBSOCKET = "websocket"
    AUTH = "auth"
    REALTIME = "realtime"
    ANALYTICS = "analytics"


@dataclass
class DegradationState:
    """Current degradation state of a service."""

    level: DegradationLevel = DegradationLevel.FULL
    disabled_capabilities: set[ServiceCapability] = field(default_factory=set)
    reason: str | None = None
    since: datetime | None = None
    auto_recover: bool = True


class DegradationManager:
    """Manages service degradation levels and capabilities."""

    def __init__(self, service_name: str, auto_recovery: bool = True):
        """Initialize degradation manager.

        Args:
            service_name: Name of the service being managed
            auto_recovery: Whether to automatically attempt recovery
        """
        self.service_name = service_name
        self.auto_recovery = auto_recovery

        self._state = DegradationState()
        self._lock = threading.RLock()

        # Capability handlers
        self._capability_handlers: dict[ServiceCapability, Callable[[], bool]] = {}

        # Fallback implementations
        self._fallbacks: dict[ServiceCapability, Callable[..., Any]] = {}

        # Statistics
        self._degradation_count = 0
        self._recovery_count = 0
        self._last_degraded_at: datetime | None = None
        self._last_recovered_at: datetime | None = None

    def register_capability_check(
        self,
        capability: ServiceCapability,
        check_func: Callable[[], bool],
    ) -> None:
        """Register a health check function for a capability.

        Args:
            capability: Capability to check
            check_func: Function that returns True if capability is available
        """
        with self._lock:
            self._capability_handlers[capability] = check_func

    def register_fallback(
        self,
        capability: ServiceCapability,
        fallback_func: Callable[..., Any],
    ) -> None:
        """Register a fallback implementation for a capability.

        Args:
            capability: Capability to provide fallback for
            fallback_func: Fallback function to use when capability is degraded
        """
        with self._lock:
            self._fallbacks[capability] = fallback_func

    def check_capability(self, capability: ServiceCapability) -> bool:
        """Check if a capability is available.

        Args:
            capability: Capability to check

        Returns:
            True if capability is available
        """
        with self._lock:
            if capability in self._state.disabled_capabilities:
                return False

            if capability in self._capability_handlers:
                try:
                    return self._capability_handlers[capability]()
                except Exception as e:
                    logger.warning(
                        f"Capability check failed for {capability.value}: {e}"
                    )
                    return False

            return True

    def check_all_capabilities(self) -> dict[ServiceCapability, bool]:
        """Check all registered capabilities.

        Returns:
            Dictionary mapping capabilities to their availability
        """
        with self._lock:
            return {
                cap: self.check_capability(cap)
                for cap in ServiceCapability
                if cap in self._capability_handlers or cap in self._state.disabled_capabilities
            }

    def degrade(
        self,
        level: DegradationLevel,
        capabilities: list[ServiceCapability] | None = None,
        reason: str | None = None,
    ) -> None:
        """Degrade service to specified level.

        Args:
            level: Degradation level
            capabilities: Specific capabilities to disable (optional)
            reason: Reason for degradation
        """
        with self._lock:
            old_level = self._state.level

            self._state.level = level
            if capabilities:
                self._state.disabled_capabilities.update(capabilities)
            self._state.reason = reason
            self._state.since = datetime.now()
            self._state.auto_recover = self.auto_recovery

            if old_level == DegradationLevel.FULL and level != DegradationLevel.FULL:
                self._degradation_count += 1
                self._last_degraded_at = datetime.now()

            logger.warning(
                f"Service {self.service_name} degraded to {level.value} level. "
                f"Reason: {reason or 'Not specified'}. "
                f"Disabled capabilities: {[c.value for c in self._state.disabled_capabilities]}"
            )

    def recover(self, capabilities: list[ServiceCapability] | None = None) -> None:
        """Recover service capabilities.

        Args:
            capabilities: Specific capabilities to recover (None = all)
        """
        with self._lock:
            if capabilities is None:
                # Full recovery
                self._state.level = DegradationLevel.FULL
                self._state.disabled_capabilities.clear()
                self._state.reason = None
                self._state.since = None

                logger.info(f"Service {self.service_name} fully recovered")
            else:
                # Partial recovery
                for cap in capabilities:
                    self._state.disabled_capabilities.discard(cap)

                logger.info(
                    f"Service {self.service_name} partially recovered. "
                    f"Still disabled: {[c.value for c in self._state.disabled_capabilities]}"
                )

            self._recovery_count += 1
            self._last_recovered_at = datetime.now()

    def get_state(self) -> DegradationState:
        """Get current degradation state.

        Returns:
            Copy of current degradation state
        """
        with self._lock:
            import copy
            return copy.deepcopy(self._state)

    def get_stats(self) -> dict[str, Any]:
        """Get degradation statistics.

        Returns:
            Dictionary with degradation statistics
        """
        with self._lock:
            return {
                "service_name": self.service_name,
                "current_level": self._state.level.value,
                "disabled_capabilities": [c.value for c in self._state.disabled_capabilities],
                "degradation_count": self._degradation_count,
                "recovery_count": self._recovery_count,
                "last_degraded_at": self._last_degraded_at.isoformat() if self._last_degraded_at else None,
                "last_recovered_at": self._last_recovered_at.isoformat() if self._last_recovered_at else None,
                "reason": self._state.reason,
                "since": self._state.since.isoformat() if self._state.since else None,
            }

    def execute_with_fallback(
        self,
        capability: ServiceCapability,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Execute function with fallback if capability is degraded.

        Args:
            capability: Required capability
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback result

        Raises:
            RuntimeError: If capability is unavailable and no fallback exists
        """
        if self.check_capability(capability):
            return func(*args, **kwargs)

        # Capability is degraded, try fallback
        if capability in self._fallbacks:
            logger.warning(
                f"Capability {capability.value} degraded, using fallback"
            )
            return cast(T, self._fallbacks[capability](*args, **kwargs))

        raise RuntimeError(
            f"Capability {capability.value} is not available and no fallback registered"
        )


def with_degradation_fallback(
    capability: ServiceCapability,
    manager: DegradationManager | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add degradation fallback to a function.

    Args:
        capability: Required capability
        manager: Degradation manager (creates default if None)

    Returns:
        Decorated function with degradation fallback

    Example:
        manager = DegradationManager("my_service")
        manager.register_fallback(
            ServiceCapability.ML_INFERENCE,
            lambda text: {"sentiment": "neutral", "confidence": 0.5}
        )

        @with_degradation_fallback(ServiceCapability.ML_INFERENCE, manager)
        def analyze_sentiment(text: str) -> dict:
            return ml_model.predict(text)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if manager is None:
                raise RuntimeError("Degradation manager not provided")

            return manager.execute_with_fallback(capability, func, *args, **kwargs)

        return wrapper

    return decorator


# Service-level degradation presets
DEGRADATION_PRESETS = {
    "database_failover": {
        "level": DegradationLevel.REDUCED,
        "capabilities": [ServiceCapability.DATABASE],
        "reason": "Database unavailable, using cache fallback",
    },
    "ml_service_down": {
        "level": DegradationLevel.BASIC,
        "capabilities": [ServiceCapability.ML_INFERENCE],
        "reason": "ML service unavailable, using rule-based fallback",
    },
    "external_api_timeout": {
        "level": DegradationLevel.REDUCED,
        "capabilities": [ServiceCapability.EXTERNAL_API],
        "reason": "External API timing out, using cached data",
    },
    "cache_disabled": {
        "level": DegradationLevel.FULL,
        "capabilities": [ServiceCapability.CACHE],
        "reason": "Cache disabled, using direct queries",
    },
    "maintenance_mode": {
        "level": DegradationLevel.OFFLINE,
        "capabilities": list(ServiceCapability),
        "reason": "Service under maintenance",
    },
}


class ServiceHealthMonitor:
    """Monitor service health and trigger degradation automatically."""

    def __init__(
        self,
        manager: DegradationManager,
        check_interval: float = 30.0,
        failure_threshold: int = 3,
    ):
        """Initialize health monitor.

        Args:
            manager: Degradation manager to control
            check_interval: Seconds between health checks
            failure_threshold: Failures before triggering degradation
        """
        self.manager = manager
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold

        self._failure_counts: dict[ServiceCapability, int] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start health monitoring in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Health monitor started for {self.manager.service_name}")

    def stop(self) -> None:
        """Stop health monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info(f"Health monitor stopped for {self.manager.service_name}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        import time

        while self._running:
            try:
                self._check_capabilities()
            except Exception as e:
                logger.error(f"Health check error: {e}")

            time.sleep(self.check_interval)

    def _check_capabilities(self) -> None:
        """Check all capabilities and trigger degradation if needed."""
        capabilities = self.manager.check_all_capabilities()

        for capability, is_available in capabilities.items():
            if is_available:
                self._failure_counts[capability] = 0
                # Attempt recovery
                if capability in self.manager._state.disabled_capabilities:
                    self.manager.recover([capability])
            else:
                self._failure_counts[capability] = (
                    self._failure_counts.get(capability, 0) + 1
                )

                if self._failure_counts[capability] >= self.failure_threshold:
                    self.manager.degrade(
                        level=DegradationLevel.REDUCED,
                        capabilities=[capability],
                        reason=f"Health check failed {self._failure_counts[capability]} times",
                    )


# Global degradation managers registry
_managers: dict[str, DegradationManager] = {}
_managers_lock = threading.RLock()


def get_degradation_manager(service_name: str) -> DegradationManager:
    """Get or create a degradation manager for a service.

    Args:
        service_name: Name of the service

    Returns:
        DegradationManager instance
    """
    with _managers_lock:
        if service_name not in _managers:
            _managers[service_name] = DegradationManager(service_name)
        return _managers[service_name]


def get_all_degradation_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all degradation managers.

    Returns:
        Dictionary mapping service names to their stats
    """
    with _managers_lock:
        return {name: mgr.get_stats() for name, mgr in _managers.items()}
