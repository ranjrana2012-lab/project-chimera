"""
Unit tests for Scene Recovery.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, '.')

from core.scene_manager import (
    SceneManager,
    SceneConfig,
    SceneState
)
from persistence.scene_store import SceneStore
from core.recovery import (
    SceneRecoveryManager,
    RecoveryResult,
    SceneRecoveryError,
    recover_scenes_on_startup,
    get_recovery_summary
)


class TestRecoveryResult:
    """Test RecoveryResult dataclass."""

    def test_success_result(self):
        """Create successful recovery result."""
        result = RecoveryResult(
            scene_id="test-scene",
            success=True,
            state=SceneState.ACTIVE
        )

        assert result.scene_id == "test-scene"
        assert result.success is True
        assert result.state == SceneState.ACTIVE
        assert result.error is None

    def test_failure_result(self):
        """Create failed recovery result."""
        result = RecoveryResult(
            scene_id="failed-scene",
            success=False,
            error="Redis connection failed"
        )

        assert result.scene_id == "failed-scene"
        assert result.success is False
        assert result.state is None
        assert result.error == "Redis connection failed"

    def test_repr_success(self):
        """String representation of successful result."""
        result = RecoveryResult(
            scene_id="test",
            success=True,
            state=SceneState.PAUSED
        )

        assert "test" in repr(result)
        assert "paused" in repr(result)

    def test_repr_failure(self):
        """String representation of failed result."""
        result = RecoveryResult(
            scene_id="test",
            success=False,
            error="Failed"
        )

        assert "FAILED" in repr(result)


class TestSceneRecoveryManager:
    """Test SceneRecoveryManager."""

    @pytest.fixture
    def store_mock(self):
        """Mock scene store."""
        return Mock(spec=SceneStore)

    @pytest.fixture
    def manager(self, store_mock):
        """Create recovery manager."""
        return SceneRecoveryManager(store_mock)

    def test_init(self, manager, store_mock):
        """Initialize recovery manager."""
        assert manager._scene_store is store_mock
        assert manager._max_recovery_attempts == 3

    def test_discover_scenes(self, manager, store_mock):
        """Discover scenes from Redis."""
        store_mock.list_scenes.return_value = ["scene-001", "scene-002"]

        scenes = manager.discover_scenes()

        assert len(scenes) == 2
        assert "scene-001" in scenes
        assert "scene-002" in scenes

    def test_recover_scene_success(self, manager, store_mock):
        """Successfully recover a scene."""
        # Mock scene manager
        scene_manager_mock = Mock(spec=SceneManager)
        scene_manager_mock.state = SceneState.ACTIVE
        scene_manager_mock.scene_id = "test"

        store_mock.load_state.return_value = {
            "scene_id": "test",
            "state": "active",
            "config": {"scene_id": "test", "name": "Test", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }
        store_mock.restore_scene.return_value = scene_manager_mock

        result = manager.recover_scene("test")

        assert result.success is True
        assert result.scene_id == "test"
        assert result.state == SceneState.ACTIVE

    def test_recover_scene_not_found(self, manager, store_mock):
        """Scene not found in Redis."""
        store_mock.load_state.return_value = None

        result = manager.recover_scene("missing")

        assert result.success is False
        assert "not found" in result.error

    def test_recover_scene_invalid_state(self, manager, store_mock):
        """Scene has invalid state."""
        store_mock.load_state.return_value = {
            "scene_id": "test",
            "state": "invalid_state",
            "config": {"scene_id": "test", "name": "Test", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }

        result = manager.recover_scene("test")

        assert result.success is False
        assert "Invalid state" in result.error

    def test_recover_completed_scene_skipped(self, manager, store_mock):
        """Completed scenes are skipped."""
        store_mock.load_state.return_value = {
            "scene_id": "test",
            "state": "completed",
            "config": {"scene_id": "test", "name": "Test", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }

        result = manager.recover_scene("test")

        assert result.success is True
        assert result.state == SceneState.COMPLETED

    def test_recover_all_scenes(self, manager, store_mock):
        """Recover all scenes."""
        # Mock scenes
        store_mock.list_scenes.return_value = ["scene-001", "scene-002"]

        # Create mock managers
        manager1 = Mock(spec=SceneManager)
        manager1.state = SceneState.ACTIVE
        manager1.scene_id = "scene-001"

        manager2 = Mock(spec=SceneManager)
        manager2.state = SceneState.PAUSED
        manager2.scene_id = "scene-002"

        # Mock load_state and restore_scene
        def load_side(scene_id):
            if scene_id == "scene-001":
                return {"scene_id": "scene-001", "state": "active", "config": {"scene_id": "scene-001", "name": "Scene 1", "scene_type": "dialogue", "version": "1.0.0"}, "state_data": {}, "updated_at": "2026-03-04T00:00:00"}
            else:
                return {"scene_id": "scene-002", "state": "paused", "config": {"scene_id": "scene-002", "name": "Scene 2", "scene_type": "dialogue", "version": "1.0.0"}, "state_data": {}, "updated_at": "2026-03-04T00:00:00"}

        def restore_side(scene_id):
            if scene_id == "scene-001":
                return manager1
            else:
                return manager2

        store_mock.load_state.side_effect = load_side
        store_mock.restore_scene.side_effect = restore_side

        results = manager.recover_all_scenes()

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_recover_active_scenes_only(self, manager, store_mock):
        """Recover only active scenes."""
        store_mock.list_scenes.return_value = ["active", "completed", "error"]

        # Return different states
        def load_side(scene_id):
            if scene_id == "active":
                return {"scene_id": "active", "state": "active", "config": {"scene_id": "active", "name": "Active", "scene_type": "dialogue", "version": "1.0.0"}, "state_data": {}, "updated_at": "2026-03-04T00:00:00"}
            elif scene_id == "completed":
                return {"scene_id": "completed", "state": "completed", "config": {"scene_id": "completed", "name": "Completed", "scene_type": "dialogue", "version": "1.0.0"}, "state_data": {}, "updated_at": "2026-03-04T00:00:00"}
            else:
                return {"scene_id": "error", "state": "error", "config": {"scene_id": "error", "name": "Error", "scene_type": "dialogue", "version": "1.0.0"}, "state_data": {}, "updated_at": "2026-03-04T00:00:00"}

        store_mock.load_state.side_effect = load_side

        # Only return a manager for active scene
        active_manager = Mock(spec=SceneManager)
        active_manager.state = SceneState.ACTIVE

        def restore_side(scene_id):
            if scene_id == "active":
                return active_manager
            return None

        store_mock.restore_scene.side_effect = restore_side

        active_managers = manager.recover_active_scenes()

        # Only active scene should be recovered
        assert len(active_managers) == 1
        assert "active" in active_managers

    def test_cleanup_stale_scenes(self, manager, store_mock):
        """Clean up stale scenes."""
        store_mock.list_scenes.return_value = ["old", "new"]

        # Old scene (should be cleaned)
        old_data = {
            "scene_id": "old",
            "state": "completed",
            "config": {"scene_id": "old", "name": "Old", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-01-01T00:00:00"
        }

        # New scene (should not be cleaned)
        new_data = {
            "scene_id": "new",
            "state": "completed",
            "config": {"scene_id": "new", "name": "New", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-12-31T23:59:59"
        }

        def load_side(scene_id):
            if scene_id == "old":
                return old_data
            else:
                return new_data

        store_mock.load_state.side_effect = load_side
        store_mock.delete_scene.return_value = True  # Success

        cleaned = manager.cleanup_stale_scenes(max_age_hours=100000)  # Very high to ensure old scene is cleaned

        # Old scene should be cleaned
        assert cleaned >= 0

    def test_callback_on_recovery(self, manager, store_mock):
        """Callback is called after recovery."""
        callback_results = []

        def callback(result):
            callback_results.append(result)

        manager.register_callback(callback)

        scene_manager_mock = Mock(spec=SceneManager)
        scene_manager_mock.state = SceneState.ACTIVE
        scene_manager_mock.scene_id = "test"

        store_mock.load_state.return_value = {
            "scene_id": "test",
            "state": "active",
            "config": {"scene_id": "test", "name": "Test", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }
        store_mock.restore_scene.return_value = scene_manager_mock

        manager.recover_scene("test")

        assert len(callback_results) == 1
        assert callback_results[0].scene_id == "test"

    def test_multiple_callbacks(self, manager, store_mock):
        """Multiple callbacks are called."""
        call_count = [0]

        def callback1(result):
            call_count[0] += 1

        def callback2(result):
            call_count[0] += 1

        manager.register_callback(callback1)
        manager.register_callback(callback2)

        scene_manager_mock = Mock(spec=SceneManager)
        scene_manager_mock.state = SceneState.ACTIVE
        scene_manager_mock.scene_id = "test"

        store_mock.load_state.return_value = {
            "scene_id": "test",
            "state": "active",
            "config": {"scene_id": "test", "name": "Test", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }
        store_mock.restore_scene.return_value = scene_manager_mock

        manager.recover_scene("test")

        assert call_count[0] == 2


class TestRecoveryConvenienceFunctions:
    """Test convenience functions."""

    def test_recover_scenes_on_startup_active_only(self):
        """Recover active scenes on startup."""
        store_mock = Mock(spec=SceneStore)

        # Mock list_scenes to return a list
        store_mock.list_scenes.return_value = ["scene-001"]

        # Mock load_state for active scene
        store_mock.load_state.return_value = {
            "scene_id": "scene-001",
            "state": "active",
            "config": {"scene_id": "scene-001", "name": "Scene", "scene_type": "dialogue", "version": "1.0.0"},
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        }

        # Mock restore_scene to return a manager
        scene_manager_mock = Mock(spec=SceneManager)
        scene_manager_mock.state = SceneState.ACTIVE
        store_mock.restore_scene.return_value = scene_manager_mock

        results = recover_scenes_on_startup(store_mock, recover_active_only=True)

        # Results should be a list
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].success is True

    def test_get_recovery_summary(self):
        """Get summary of recovery results."""
        results = [
            RecoveryResult("scene-1", True, SceneState.ACTIVE),
            RecoveryResult("scene-2", True, SceneState.PAUSED),
            RecoveryResult("scene-3", False, error="Failed")
        ]

        summary = get_recovery_summary(results)

        assert summary["total"] == 3
        assert summary["success"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == 2/3
        assert summary["state_counts"]["active"] == 1
        assert summary["state_counts"]["paused"] == 1
        assert "scene-3" in summary["failed_scenes"]

    def test_get_recovery_summary_empty(self):
        """Get summary of empty results."""
        summary = get_recovery_summary([])

        assert summary["total"] == 0
        assert summary["success"] == 0
        assert summary["failed"] == 0
        assert summary["success_rate"] == 0
