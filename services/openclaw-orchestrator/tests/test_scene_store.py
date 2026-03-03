"""
Unit tests for Scene Store - Redis persistence.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, '.')

from core.scene_manager import (
    SceneManager,
    SceneConfig,
    SceneState
)
from persistence.scene_store import (
    SceneStore,
    SceneStoreMixin,
    scene_key,
    get_redis_client,
    TTL_ACTIVE_SCENE,
    TTL_COMPLETED_SCENE,
    TTL_ERROR_SCENE
)


class TestSceneKey:
    """Test Redis key generation."""

    def test_key_without_suffix(self):
        """Generate key without suffix."""
        key = scene_key("scene-001")
        assert key == "chimera:scene:scene-001"

    def test_key_with_suffix(self):
        """Generate key with suffix."""
        key = scene_key("scene-001", "state")
        assert key == "chimera:scene:scene-001:state"

    def test_key_with_empty_scene_id(self):
        """Generate registry key."""
        key = scene_key("", "registry")
        assert key == "chimera:scene:registry"


class TestSceneStoreInit:
    """Test SceneStore initialization."""

    def test_init_with_redis(self):
        """Initialize with Redis client."""
        redis_mock = Mock()
        store = SceneStore(redis_client=redis_mock)

        assert store._redis is redis_mock
        assert store.degraded_mode is False

    def test_init_without_redis(self):
        """Initialize without Redis (degraded mode)."""
        store = SceneStore(redis_client=None)

        assert store._redis is None
        assert store.degraded_mode is True


class TestSceneStoreDegradedMode:
    """Test SceneStore in degraded mode."""

    @pytest.fixture
    def store(self):
        """Create degraded mode store."""
        return SceneStore(redis_client=None)

    def test_save_state_returns_false(self, store):
        """Save returns False in degraded mode."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        result = store.save_state(manager)
        assert result is False

    def test_load_state_returns_none(self, store):
        """Load returns None in degraded mode."""
        result = store.load_state("scene-001")
        assert result is None

    def test_delete_scene_returns_false(self, store):
        """Delete returns False in degraded mode."""
        result = store.delete_scene("scene-001")
        assert result is False

    def test_list_scenes_returns_empty(self, store):
        """List returns empty list in degraded mode."""
        result = store.list_scenes()
        assert result == []


class TestSceneStoreSave:
    """Test saving state to Redis."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    @pytest.fixture
    def manager(self):
        """Create test scene manager."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)
        manager.initialize()
        manager.activate()
        return manager

    def test_save_state_calls_redis_setex(self, store, redis_mock, manager):
        """Save calls Redis setex."""
        store.save_state(manager)

        assert redis_mock.setex.called
        call_args = redis_mock.setex.call_args_list[0]
        key = call_args[0][0]
        assert "test-scene" in key
        assert "state" in key

    def test_save_state_serializes_data(self, store, redis_mock, manager):
        """Save serializes state data correctly."""
        store.save_state(manager)

        call_args = redis_mock.setex.call_args_list[0]
        # setex takes (key, ttl, value)
        data = json.loads(call_args[0][2])

        assert data["scene_id"] == "test-scene"
        assert data["state"] == "active"
        assert "config" in data
        assert "state_data" in data

    def test_save_state_saves_history(self, store, redis_mock, manager):
        """Save saves transition history."""
        manager.pause("test")
        manager.resume()

        store.save_state(manager)

        # Check that history key was used
        call_args = redis_mock.setex.call_args_list
        history_call = [c for c in call_args if "history" in str(c)]
        assert len(history_call) > 0

    def test_save_state_adds_to_registry(self, store, redis_mock, manager):
        """Save adds scene to registry."""
        store.save_state(manager)

        assert redis_mock.sadd.called
        call_args = redis_mock.sadd.call_args
        assert "registry" in str(call_args)

    def test_save_state_sets_correct_ttl(self, store, redis_mock, manager):
        """Save sets correct TTL based on state."""
        store.save_state(manager)

        # Active scene has no TTL
        call_args = redis_mock.setex.call_args_list[0]
        ttl = call_args[0][1]
        assert ttl is None

    def test_save_completed_scene_has_ttl(self, store, redis_mock):
        """Completed scene gets TTL."""
        config = SceneConfig(
            scene_id="completed",
            name="Completed",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)
        manager.initialize()
        manager.activate()
        manager.complete()

        store.save_state(manager)

        call_args = redis_mock.setex.call_args_list[0]
        ttl = call_args[0][1]
        assert ttl == TTL_COMPLETED_SCENE

    def test_save_error_scene_has_ttl(self, store, redis_mock):
        """Error scene gets TTL."""
        config = SceneConfig(
            scene_id="error",
            name="Error",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)
        manager.initialize()
        manager.error("E001", "Test error", recoverable=False)

        store.save_state(manager)

        call_args = redis_mock.setex.call_args_list[0]
        ttl = call_args[0][1]
        assert ttl == TTL_ERROR_SCENE

    def test_save_error_returns_false(self, store, redis_mock, manager):
        """Redis error returns False."""
        redis_mock.setex.side_effect = Exception("Redis error")

        result = store.save_state(manager)
        assert result is False


class TestSceneStoreLoad:
    """Test loading state from Redis."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    def test_load_state_returns_data(self, store, redis_mock):
        """Load returns state data."""
        redis_mock.get.return_value = json.dumps({
            "scene_id": "test",
            "state": "active",
            "config": {
                "scene_id": "test",
                "name": "Test",
                "scene_type": "dialogue",
                "version": "1.0.0"
            },
            "state_data": {},
            "updated_at": "2026-03-04T00:00:00"
        })

        result = store.load_state("test")

        assert result is not None
        assert result["scene_id"] == "test"
        assert result["state"] == "active"

    def test_load_state_not_found(self, store, redis_mock):
        """Load returns None when scene not found."""
        redis_mock.get.return_value = None

        result = store.load_state("missing")

        assert result is None

    def test_load_history_returns_transitions(self, store, redis_mock):
        """Load returns transition history."""
        redis_mock.get.return_value = json.dumps([
            {
                "from_state": "idle",
                "to_state": "loading",
                "timestamp": "2026-03-04T00:00:00",
                "trigger": "initialize",
                "metadata": {}
            }
        ])

        history = store.load_history("test")

        assert len(history) == 1
        assert history[0].from_state == SceneState.IDLE
        assert history[0].to_state == SceneState.LOADING

    def test_load_history_empty(self, store, redis_mock):
        """Load returns empty list when no history."""
        redis_mock.get.return_value = None

        history = store.load_history("test")

        assert history == []


class TestSceneStoreRestore:
    """Test restoring scene from Redis."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        mock = Mock()
        # State data
        mock.get.side_effect = [
            json.dumps({
                "scene_id": "restored",
                "state": "active",
                "config": {
                    "scene_id": "restored",
                    "name": "Restored Scene",
                    "scene_type": "dialogue",
                    "version": "1.0.0"
                },
                "state_data": {
                    "created_at": "2026-03-04T00:00:00",
                    "activated_at": "2026-03-04T00:01:00"
                },
                "updated_at": "2026-03-04T00:01:00"
            }),
            json.dumps([
                {
                    "from_state": "idle",
                    "to_state": "loading",
                    "timestamp": "2026-03-04T00:00:00",
                    "trigger": "initialize",
                    "metadata": {}
                },
                {
                    "from_state": "loading",
                    "to_state": "active",
                    "timestamp": "2026-03-04T00:01:00",
                    "trigger": "activate",
                    "metadata": {}
                }
            ])
        ]
        return mock

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    def test_restore_scene_returns_manager(self, store):
        """Restore returns SceneManager."""
        manager = store.restore_scene("restored")

        assert manager is not None
        assert manager.scene_id == "restored"
        assert manager.state == SceneState.ACTIVE

    def test_restore_scene_restores_state_data(self, store):
        """Restore restores state data."""
        manager = store.restore_scene("restored")

        assert manager._state_data["created_at"] is not None
        assert manager._state_data["activated_at"] is not None

    def test_restore_scene_restores_history(self, store):
        """Restore restores transition history."""
        manager = store.restore_scene("restored")

        history = manager.get_transition_history()
        assert len(history) == 2

    def test_restore_scene_not_found(self, store):
        """Restore returns None when scene not found."""
        # Return None for both get calls
        store._redis.get.side_effect = [None, None]

        manager = store.restore_scene("missing")

        assert manager is None


class TestSceneStoreDelete:
    """Test deleting scene from Redis."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    def test_delete_scene_calls_redis_delete(self, store, redis_mock):
        """Delete calls Redis delete."""
        store.delete_scene("test-scene")

        assert redis_mock.delete.called

    def test_delete_scene_removes_from_registry(self, store, redis_mock):
        """Delete removes scene from registry."""
        store.delete_scene("test-scene")

        assert redis_mock.srem.called

    def test_delete_scene_returns_true_on_success(self, store, redis_mock):
        """Delete returns True on success."""
        result = store.delete_scene("test-scene")
        assert result is True

    def test_delete_scene_returns_false_on_error(self, store, redis_mock):
        """Delete returns False on Redis error."""
        redis_mock.delete.side_effect = Exception("Redis error")

        result = store.delete_scene("test-scene")
        assert result is False


class TestSceneStoreList:
    """Test listing scenes."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    def test_list_scenes_returns_scene_ids(self, store, redis_mock):
        """List returns all scene IDs."""
        redis_mock.smembers.return_value = {"scene-001", "scene-002"}

        result = store.list_scenes()

        assert len(result) == 2
        assert "scene-001" in result
        assert "scene-002" in result

    def test_list_scenes_empty(self, store, redis_mock):
        """List returns empty list when no scenes."""
        redis_mock.smembers.return_value = set()

        result = store.list_scenes()

        assert result == []

    def test_get_all_scenes_state(self, store, redis_mock):
        """Get state of all scenes."""
        redis_mock.smembers.return_value = {"scene-001", "scene-002"}
        redis_mock.get.side_effect = [
            json.dumps({"scene_id": "scene-001", "state": "active"}),
            json.dumps({"scene_id": "scene-002", "state": "paused"})
        ]

        result = store.get_all_scenes_state()

        assert result["scene-001"] == "active"
        assert result["scene-002"] == "paused"


class TestSceneStoreMixin:
    """Test SceneStoreMixin."""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def store(self, redis_mock):
        """Create store with mock Redis."""
        return SceneStore(redis_client=redis_mock)

    def test_mixin_auto_saves_on_transition(self, store):
        """Mixin auto-saves on state transition."""
        # Create persistent manager using mixin
        class PersistentManager(SceneStoreMixin, SceneManager):
            pass

        config = SceneConfig(
            scene_id="auto-save",
            name="Auto Save",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = PersistentManager(config, scene_store=store)

        manager.initialize()

        # Should have called save
        assert store._redis.setex.called

    def test_mixin_manual_save(self, store):
        """Mixin supports manual save."""
        class PersistentManager(SceneStoreMixin, SceneManager):
            pass

        config = SceneConfig(
            scene_id="manual-save",
            name="Manual Save",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = PersistentManager(config, scene_store=store)

        result = manager.save_to_store()
        assert result is True


class TestGetRedisClient:
    """Test Redis client creation."""

    def test_get_redis_client_returns_client(self):
        """Get Redis client with default settings."""
        client = get_redis_client()

        # If redis is installed, should return a client
        # If not, should return None
        assert client is None or hasattr(client, 'get')

    def test_get_redis_client_with_params(self):
        """Get Redis client with custom parameters."""
        # This test just verifies the function is callable
        # Actual connection testing would require running Redis
        client = get_redis_client(host="localhost", port=6379, db=1)
        assert client is None or hasattr(client, 'get')
