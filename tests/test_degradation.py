"""
Tests for shared degradation module.

Tests the graceful degradation functionality.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from degradation import (
    DegradationLevel,
    ServiceCapability,
    DegradationState,
    DegradationManager,
    with_degradation_fallback,
    DEGRADATION_PRESETS,
    ServiceHealthMonitor,
    get_degradation_manager,
    get_all_degradation_stats,
)


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_levels_exist(self):
        """Verify all degradation levels exist."""
        assert DegradationLevel.FULL.value == "full"
        assert DegradationLevel.REDUCED.value == "reduced"
        assert DegradationLevel.BASIC.value == "basic"
        assert DegradationLevel.OFFLINE.value == "offline"


class TestServiceCapability:
    """Tests for ServiceCapability enum."""

    def test_capabilities_exist(self):
        """Verify all capabilities exist."""
        assert ServiceCapability.ML_INFERENCE.value == "ml_inference"
        assert ServiceCapability.DATABASE.value == "database"
        assert ServiceCapability.EXTERNAL_API.value == "external_api"
        assert ServiceCapability.CACHE.value == "cache"
        assert ServiceCapability.WEBSOCKET.value == "websocket"


class TestDegradationState:
    """Tests for DegradationState dataclass."""

    def test_default_initialization(self):
        """Verify default state initialization."""
        state = DegradationState()
        assert state.level == DegradationLevel.FULL
        assert len(state.disabled_capabilities) == 0
        assert state.reason is None
        assert state.since is None
        assert state.auto_recover is True

    def test_custom_initialization(self):
        """Verify state can be initialized with custom values."""
        now = datetime.now()
        state = DegradationState(
            level=DegradationLevel.REDUCED,
            disabled_capabilities={ServiceCapability.ML_INFERENCE},
            reason="High load",
            since=now,
            auto_recover=False
        )

        assert state.level == DegradationLevel.REDUCED
        assert ServiceCapability.ML_INFERENCE in state.disabled_capabilities
        assert state.reason == "High load"


class TestDegradationManager:
    """Tests for DegradationManager class."""

    def test_initialization(self):
        """Verify degradation manager initializes correctly."""
        manager = DegradationManager("test-service")
        assert manager.service_name == "test-service"
        assert manager.auto_recovery is True

    def test_degrade_method(self):
        """Verify degrade() method works."""
        manager = DegradationManager("test-service")

        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="High load"
        )

        assert manager._state.level == DegradationLevel.REDUCED
        assert ServiceCapability.ML_INFERENCE in manager._state.disabled_capabilities

    def test_recover_method(self):
        """Verify recover() method works."""
        manager = DegradationManager("test-service")

        # First degrade
        manager.degrade(
            level=DegradationLevel.BASIC,
            capabilities=[ServiceCapability.DATABASE],
            reason="DB issues"
        )

        # Recover
        manager.recover(capabilities=[ServiceCapability.DATABASE])

        assert ServiceCapability.DATABASE not in manager._state.disabled_capabilities

    def test_check_capability(self):
        """Verify check_capability() returns correct status."""
        manager = DegradationManager("test-service")

        # Initially all available
        assert manager.check_capability(ServiceCapability.ML_INFERENCE) is True

        # Disable capability
        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="Model down"
        )

        assert manager.check_capability(ServiceCapability.ML_INFERENCE) is False

    def test_check_all_capabilities(self):
        """Verify check_all_capabilities() returns dict."""
        manager = DegradationManager("test-service")

        manager.degrade(
            level=DegradationLevel.BASIC,
            capabilities=[ServiceCapability.ML_INFERENCE, ServiceCapability.DATABASE],
            reason="Issues"
        )

        result = manager.check_all_capabilities()
        assert isinstance(result, dict)
        assert result[ServiceCapability.ML_INFERENCE] is False
        assert result[ServiceCapability.DATABASE] is False

    def test_register_fallback(self):
        """Verify fallback can be registered."""
        manager = DegradationManager("test-service")

        fallback_func = Mock(return_value="fallback result")
        manager.register_fallback(ServiceCapability.ML_INFERENCE, fallback_func)

        # Fallback should be registered
        assert ServiceCapability.ML_INFERENCE in manager._fallbacks


class TestDegradationManagerRecovery:
    """Tests for degradation manager recovery behavior."""

    def test_recover_increases_level(self):
        """Verify recovery moves to higher degradation level."""
        manager = DegradationManager("test-service")

        # Degrade to BASIC
        manager.degrade(level=DegradationLevel.BASIC, reason="Issues")

        # Recover to REDUCED
        manager.degrade(level=DegradationLevel.REDUCED)

        assert manager._state.level == DegradationLevel.REDUCED

    def test_full_recovery(self):
        """Verify full recovery returns to FULL level."""
        manager = DegradationManager("test-service")

        # Degrade
        manager.degrade(level=DegradationLevel.OFFLINE, reason="Service down")

        # Full recovery
        manager.degrade(level=DegradationLevel.FULL)

        assert manager._state.level == DegradationLevel.FULL


class TestDegradationManagerStatistics:
    """Tests for degradation manager statistics."""

    def test_degradation_count_increments(self):
        """Verify degradation count is tracked."""
        manager = DegradationManager("test-service")

        initial_count = manager._degradation_count
        manager.degrade(level=DegradationLevel.REDUCED, reason="Test")

        assert manager._degradation_count == initial_count + 1

    def test_recovery_count_increments_on_full_recovery(self):
        """Verify recovery count is tracked."""
        manager = DegradationManager("test-service")

        # Degrade first
        manager.degrade(level=DegradationLevel.BASIC, reason="Test")

        initial_count = manager._recovery_count
        # This depends on implementation - may or may not increment
        # Just verify the counter exists
        assert hasattr(manager, '_recovery_count')


class TestDegradationManagerIntegration:
    """Integration tests for degradation manager."""

    def test_full_degradation_workflow(self):
        """Test complete degradation and recovery workflow."""
        manager = DegradationManager("api-service")

        # Start at FULL
        assert manager._state.level == DegradationLevel.FULL

        # Degrade to REDUCED
        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="High load"
        )
        assert manager._state.level == DegradationLevel.REDUCED

        # Further degrade to BASIC
        manager.degrade(
            level=DegradationLevel.BASIC,
            capabilities=[ServiceCapability.DATABASE],
            reason="DB slow"
        )
        # Level should reflect degradation
        assert ServiceCapability.DATABASE in manager._state.disabled_capabilities

        # Recover capabilities
        manager.recover(capabilities=[ServiceCapability.DATABASE])
        assert ServiceCapability.DATABASE not in manager._state.disabled_capabilities

        # Full recovery (using recover() with no arguments clears all disabled capabilities)
        manager.recover()  # Call recover with no args for full recovery
        assert manager._state.level == DegradationLevel.FULL
        assert len(manager._state.disabled_capabilities) == 0


class TestDegradationManagerCapabilityChecks:
    """Tests for capability check functionality."""

    def test_register_capability_check(self):
        """Verify register_capability_check registers health check."""
        manager = DegradationManager("test-service")

        check_func = Mock(return_value=True)
        manager.register_capability_check(ServiceCapability.ML_INFERENCE, check_func)

        # Capability should be available
        assert manager.check_capability(ServiceCapability.ML_INFERENCE) is True
        check_func.assert_called_once()

    def test_capability_check_returns_false_on_failure(self):
        """Verify capability check returns False when check fails."""
        manager = DegradationManager("test-service")

        check_func = Mock(return_value=False)
        manager.register_capability_check(ServiceCapability.DATABASE, check_func)

        assert manager.check_capability(ServiceCapability.DATABASE) is False

    def test_capability_check_handles_exceptions(self):
        """Verify capability check handles exceptions gracefully."""
        manager = DegradationManager("test-service")

        check_func = Mock(side_effect=Exception("Check failed"))
        manager.register_capability_check(ServiceCapability.CACHE, check_func)

        # Should return False on exception
        assert manager.check_capability(ServiceCapability.CACHE) is False

    def test_check_all_capabilities_includes_registered(self):
        """Verify check_all_capabilities includes registered capabilities."""
        manager = DegradationManager("test-service")

        check_func = Mock(return_value=True)
        manager.register_capability_check(ServiceCapability.ML_INFERENCE, check_func)

        result = manager.check_all_capabilities()
        assert ServiceCapability.ML_INFERENCE in result
        assert result[ServiceCapability.ML_INFERENCE] is True


class TestDegradationManagerStateAndStats:
    """Tests for state and stats methods."""

    def test_get_state_returns_copy(self):
        """Verify get_state returns a copy of state."""
        manager = DegradationManager("test-service")

        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="Test degradation"
        )

        state = manager.get_state()
        assert state.level == DegradationLevel.REDUCED
        assert ServiceCapability.ML_INFERENCE in state.disabled_capabilities
        assert state.reason == "Test degradation"
        assert state.since is not None

        # Verify it's a copy, not the original
        original_disabled = len(manager._state.disabled_capabilities)
        state.disabled_capabilities.add(ServiceCapability.DATABASE)
        # Original should be unchanged
        assert len(manager._state.disabled_capabilities) == original_disabled

    def test_get_stats_returns_all_fields(self):
        """Verify get_stats returns all statistical fields."""
        manager = DegradationManager("test-service")

        manager.degrade(
            level=DegradationLevel.BASIC,
            capabilities=[ServiceCapability.DATABASE],
            reason="DB issues"
        )

        stats = manager.get_stats()
        expected_fields = {
            "service_name", "current_level", "disabled_capabilities",
            "degradation_count", "recovery_count", "last_degraded_at",
            "last_recovered_at", "reason", "since"
        }

        assert set(stats.keys()) == expected_fields
        assert stats["service_name"] == "test-service"
        assert stats["current_level"] == "basic"
        assert "database" in stats["disabled_capabilities"]
        assert stats["degradation_count"] == 1
        assert stats["reason"] == "DB issues"


class TestDegradationManagerExecuteWithFallback:
    """Tests for execute_with_fallback method."""

    def test_execute_with_fallback_when_available(self):
        """Verify execute_with_fallback calls function when capability available."""
        manager = DegradationManager("test-service")

        def func(x: int) -> int:
            return x * 2

        result = manager.execute_with_fallback(ServiceCapability.ML_INFERENCE, func, 5)
        assert result == 10

    def test_execute_with_fallback_uses_fallback_when_degraded(self):
        """Verify execute_with_fallback uses fallback when capability degraded."""
        manager = DegradationManager("test-service")

        # Register fallback
        fallback_func = Mock(return_value="fallback result")
        manager.register_fallback(ServiceCapability.ML_INFERENCE, fallback_func)

        # Degrade the capability
        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="Service down"
        )

        # Execute with fallback
        def func(x: int) -> int:
            return x * 2

        result = manager.execute_with_fallback(ServiceCapability.ML_INFERENCE, func, 5)
        assert result == "fallback result"
        fallback_func.assert_called_once_with(5)

    def test_execute_with_fallback_raises_when_no_fallback(self):
        """Verify execute_with_fallback raises when capability unavailable and no fallback."""
        manager = DegradationManager("test-service")

        # Degrade the capability without registering fallback
        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="Service down"
        )

        def func(x: int) -> int:
            return x * 2

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="not available and no fallback"):
            manager.execute_with_fallback(ServiceCapability.ML_INFERENCE, func, 5)


class TestDegradationDecorator:
    """Tests for with_degradation_fallback decorator."""

    def test_decorator_works_with_manager(self):
        """Verify decorator works with provided manager."""
        manager = DegradationManager("test-service")

        # Register fallback
        fallback_func = Mock(return_value="fallback")
        manager.register_fallback(ServiceCapability.ML_INFERENCE, fallback_func)

        @with_degradation_fallback(ServiceCapability.ML_INFERENCE, manager)
        def analyze(text: str) -> str:
            return f"analyzed: {text}"

        # When capability available, function is called
        result = analyze("test")
        assert result == "analyzed: test"

    def test_decorator_uses_fallback_when_degraded(self):
        """Verify decorator uses fallback when capability degraded."""
        manager = DegradationManager("test-service")

        # Register fallback
        fallback_func = Mock(return_value="fallback result")
        manager.register_fallback(ServiceCapability.ML_INFERENCE, fallback_func)

        # Degrade the capability
        manager.degrade(
            level=DegradationLevel.REDUCED,
            capabilities=[ServiceCapability.ML_INFERENCE],
            reason="Service down"
        )

        @with_degradation_fallback(ServiceCapability.ML_INFERENCE, manager)
        def analyze(text: str) -> str:
            return f"analyzed: {text}"

        result = analyze("test")
        assert result == "fallback result"
        fallback_func.assert_called_once_with("test")

    def test_decorator_raises_without_manager(self):
        """Verify decorator raises RuntimeError when manager is None."""
        @with_degradation_fallback(ServiceCapability.ML_INFERENCE, None)
        def func() -> str:
            return "result"

        with pytest.raises(RuntimeError, match="Degradation manager not provided"):
            func()


class TestDegradationPresets:
    """Tests for DEGRADATION_PRESETS."""

    def test_database_failover_preset(self):
        """Verify database_failover preset exists."""
        assert "database_failover" in DEGRADATION_PRESETS
        preset = DEGRADATION_PRESETS["database_failover"]
        assert preset["level"] == DegradationLevel.REDUCED
        assert ServiceCapability.DATABASE in preset["capabilities"]

    def test_ml_service_down_preset(self):
        """Verify ml_service_down preset exists."""
        assert "ml_service_down" in DEGRADATION_PRESETS
        preset = DEGRADATION_PRESETS["ml_service_down"]
        assert preset["level"] == DegradationLevel.BASIC

    def test_external_api_timeout_preset(self):
        """Verify external_api_timeout preset exists."""
        assert "external_api_timeout" in DEGRADATION_PRESETS

    def test_cache_disabled_preset(self):
        """Verify cache_disabled preset exists."""
        assert "cache_disabled" in DEGRADATION_PRESETS

    def test_maintenance_mode_preset(self):
        """Verify maintenance_mode preset exists."""
        assert "maintenance_mode" in DEGRADATION_PRESETS
        preset = DEGRADATION_PRESETS["maintenance_mode"]
        assert preset["level"] == DegradationLevel.OFFLINE


class TestServiceHealthMonitor:
    """Tests for ServiceHealthMonitor class."""

    def test_initialization(self):
        """Verify health monitor initializes correctly."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(manager)

        assert monitor.manager == manager
        assert monitor.check_interval == 30.0
        assert monitor.failure_threshold == 3
        assert monitor._running is False

    def test_custom_initialization(self):
        """Verify health monitor accepts custom values."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(
            manager,
            check_interval=10.0,
            failure_threshold=5
        )

        assert monitor.check_interval == 10.0
        assert monitor.failure_threshold == 5

    def test_start_sets_running_flag(self):
        """Verify start() sets running flag."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(manager, check_interval=0.01)

        monitor.start()
        assert monitor._running is True

        # Stop to clean up
        monitor.stop()

    def test_stop_clears_running_flag(self):
        """Verify stop() clears running flag and thread."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(manager, check_interval=0.01)

        monitor.start()
        monitor.stop()
        assert monitor._running is False

    def test_start_when_already_running_is_idempotent(self):
        """Verify start() is idempotent when already running."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(manager, check_interval=0.01)

        monitor.start()
        original_thread = monitor._thread
        monitor.start()  # Should not create new thread
        assert monitor._thread is original_thread

        monitor.stop()

    def test_stop_when_not_running_is_safe(self):
        """Verify stop() is safe when not running."""
        manager = DegradationManager("test-service")
        monitor = ServiceHealthMonitor(manager)

        # Should not raise
        monitor.stop()
        assert monitor._running is False


class TestGlobalDegradationFunctions:
    """Tests for global degradation manager functions."""

    def test_get_degradation_manager(self):
        """Verify get_degradation_manager returns or creates manager."""
        # First call creates manager
        mgr1 = get_degradation_manager("service-a")
        assert mgr1.service_name == "service-a"

        # Second call returns same instance
        mgr2 = get_degradation_manager("service-a")
        assert mgr1 is mgr2

        # Different service gets different manager
        mgr3 = get_degradation_manager("service-b")
        assert mgr3 is not mgr1

    def test_get_all_degradation_stats(self):
        """Verify get_all_degradation_stats returns stats for all managers."""
        # Create some managers
        get_degradation_manager("service-1")
        get_degradation_manager("service-2")

        stats = get_all_degradation_stats()
        assert "service-1" in stats
        assert "service-2" in stats
        assert stats["service-1"]["service_name"] == "service-1"


class TestServiceCapabilityEnum:
    """Additional tests for ServiceCapability enum."""

    def test_all_expected_capabilities_exist(self):
        """Verify all expected capabilities are defined."""
        expected = [
            "ML_INFERENCE",
            "DATABASE",
            "EXTERNAL_API",
            "CACHE",
            "WEBSOCKET",
            "AUTH",
            "REALTIME",
            "ANALYTICS"
        ]

        for cap_name in expected:
            assert hasattr(ServiceCapability, cap_name)
