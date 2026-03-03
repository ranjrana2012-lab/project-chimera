"""
Scene Store - Redis Persistence for Scene State

Provides Redis-based persistence for scene state, enabling:
- State recovery after orchestrator restart
- Multi-instance state sharing
- Scene history tracking
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict

try:
    import redis
except ImportError:
    redis = None
    logging.warning("redis package not installed, persistence unavailable")


from core.scene_manager import (
    SceneManager,
    SceneState,
    SceneConfig,
    StateTransition
)


logger = logging.getLogger(__name__)


# Redis key namespace
REDIS_KEY_PREFIX = "chimera:scene"
REDIS_KEY_SEPARATOR = ":"

# TTL values (seconds)
TTL_ACTIVE_SCENE = None  # No expiration for active scenes
TTL_COMPLETED_SCENE = 7 * 24 * 60 * 60  # 7 days
TTL_ERROR_SCENE = 30 * 24 * 60 * 60  # 30 days


def scene_key(scene_id: str, suffix: str = "") -> str:
    """
    Generate Redis key for scene data.

    Args:
        scene_id: Scene identifier (can be empty for registry keys)
        suffix: Optional key suffix

    Returns:
        Redis key string
    """
    parts = [REDIS_KEY_PREFIX]
    if scene_id:
        parts.append(scene_id)
    if suffix:
        parts.append(suffix)
    return REDIS_KEY_SEPARATOR.join(parts)


class SceneStore:
    """
    Redis-based persistence for scene state.

    Features:
        - Save/load scene state
        - State change tracking
        - TTL management
        - Degraded mode when Redis unavailable

    Usage:
        store = SceneStore(redis_client=redis_client)
        store.save_state(manager)
        manager = store.load_state("scene-001")
    """

    def __init__(self, redis_client=None):
        """
        Initialize scene store.

        Args:
            redis_client: Optional Redis client. If None, operates in degraded mode.
        """
        self._redis = redis_client
        self._degraded_mode = redis_client is None

        if self._degraded_mode:
            logger.warning("SceneStore running in degraded mode (no Redis)")
        else:
            logger.info("SceneStore initialized with Redis")

    @property
    def degraded_mode(self) -> bool:
        """Check if running in degraded mode."""
        return self._degraded_mode

    def save_state(self, manager: SceneManager) -> bool:
        """
        Save scene state to Redis.

        Args:
            manager: SceneManager to save

        Returns:
            True if save successful
        """
        if self._degraded_mode:
            logger.debug(f"Degraded mode: skipping save for {manager.scene_id}")
            return False

        try:
            scene_id = manager.scene_id
            state = manager.state

            # Serialize state_data (convert datetime to ISO format)
            serializable_state_data = {}
            for key, value in manager._state_data.items():
                if isinstance(value, datetime):
                    serializable_state_data[key] = value.isoformat()
                elif isinstance(value, dict) and "timestamp" in value:
                    # Handle error dict with timestamp
                    serializable_state_data[key] = value
                else:
                    serializable_state_data[key] = value

            # Prepare state data
            state_data = {
                "scene_id": scene_id,
                "state": state.value,
                "config": manager.config.config,
                "state_data": serializable_state_data,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Save to Redis
            key = scene_key(scene_id, "state")
            self._redis.setex(
                key,
                self._get_ttl_for_state(state),
                json.dumps(state_data)
            )

            # Save transition history
            history_key = scene_key(scene_id, "history")
            history = [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "trigger": t.trigger,
                    "metadata": t.metadata
                }
                for t in manager.get_transition_history()
            ]
            self._redis.setex(
                history_key,
                self._get_ttl_for_state(state),
                json.dumps(history)
            )

            # Add to scene registry
            registry_key = scene_key("", "registry")
            self._redis.sadd(registry_key, scene_id)

            logger.debug(f"Saved state for scene {scene_id}: {state.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to save state for {manager.scene_id}: {e}")
            return False

    def load_state(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Load scene state from Redis.

        Args:
            scene_id: Scene identifier

        Returns:
            State data dict, or None if not found
        """
        if self._degraded_mode:
            logger.debug(f"Degraded mode: cannot load {scene_id}")
            return None

        try:
            key = scene_key(scene_id, "state")
            data = self._redis.get(key)

            if data is None:
                logger.debug(f"No state found for scene {scene_id}")
                return None

            state_data = json.loads(data)
            logger.debug(f"Loaded state for scene {scene_id}: {state_data['state']}")
            return state_data

        except Exception as e:
            logger.error(f"Failed to load state for {scene_id}: {e}")
            return None

    def load_history(self, scene_id: str) -> List[StateTransition]:
        """
        Load transition history from Redis.

        Args:
            scene_id: Scene identifier

        Returns:
            List of StateTransition objects
        """
        if self._degraded_mode:
            return []

        try:
            key = scene_key(scene_id, "history")
            data = self._redis.get(key)

            if data is None:
                return []

            history_data = json.loads(data)
            transitions = []
            for item in history_data:
                transitions.append(StateTransition(
                    from_state=SceneState(item["from_state"]),
                    to_state=SceneState(item["to_state"]),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    trigger=item["trigger"],
                    metadata=item.get("metadata", {})
                ))
            return transitions

        except Exception as e:
            logger.error(f"Failed to load history for {scene_id}: {e}")
            return []

    def restore_scene(self, scene_id: str) -> Optional[SceneManager]:
        """
        Restore a scene manager from Redis.

        Args:
            scene_id: Scene identifier

        Returns:
            Restored SceneManager, or None if not found
        """
        state_data = self.load_state(scene_id)
        if state_data is None:
            return None

        try:
            # Create scene manager from config
            config = SceneConfig.from_dict(state_data["config"])
            manager = SceneManager(config)

            # Restore state data
            manager._state_data.update(state_data.get("state_data", {}))

            # Set current state directly (bypassing validation for restore)
            manager._state = SceneState(state_data["state"])

            # Restore transition history
            for transition in self.load_history(scene_id):
                manager._transition_history.append(transition)

            logger.info(f"Restored scene {scene_id} in state {state_data['state']}")
            return manager

        except Exception as e:
            logger.error(f"Failed to restore scene {scene_id}: {e}")
            return None

    def delete_scene(self, scene_id: str) -> bool:
        """
        Delete scene data from Redis.

        Args:
            scene_id: Scene identifier

        Returns:
            True if deletion successful
        """
        if self._degraded_mode:
            return False

        try:
            # Delete state and history
            self._redis.delete(scene_key(scene_id, "state"))
            self._redis.delete(scene_key(scene_id, "history"))

            # Remove from registry
            registry_key = scene_key("", "registry")
            self._redis.srem(registry_key, scene_id)

            logger.info(f"Deleted scene data for {scene_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete scene {scene_id}: {e}")
            return False

    def list_scenes(self) -> List[str]:
        """
        List all registered scene IDs.

        Returns:
            List of scene IDs
        """
        if self._degraded_mode:
            return []

        try:
            registry_key = scene_key("", "registry")
            scenes = self._redis.smembers(registry_key)
            return list(scenes) if scenes else []

        except Exception as e:
            logger.error(f"Failed to list scenes: {e}")
            return []

    def get_all_scenes_state(self) -> Dict[str, str]:
        """
        Get state of all registered scenes.

        Returns:
            Dict mapping scene_id -> state
        """
        result = {}
        for scene_id in self.list_scenes():
            state_data = self.load_state(scene_id)
            if state_data:
                result[scene_id] = state_data["state"]
        return result

    def _get_ttl_for_state(self, state: SceneState) -> Optional[int]:
        """
        Get TTL for a scene state.

        Args:
            state: Current scene state

        Returns:
            TTL in seconds, or None for no expiration
        """
        if state == SceneState.COMPLETED:
            return TTL_COMPLETED_SCENE
        elif state == SceneState.ERROR:
            return TTL_ERROR_SCENE
        else:
            return TTL_ACTIVE_SCENE


class SceneStoreMixin:
    """
    Mixin to add Redis persistence to SceneManager.

    Usage:
        class PersistentSceneManager(SceneStoreMixin, SceneManager):
            pass
    """

    def __init__(self, config: SceneConfig, scene_store: SceneStore = None):
        """
        Initialize with scene store.

        Args:
            config: Scene configuration
            scene_store: SceneStore instance
        """
        super().__init__(config)
        self._scene_store = scene_store or SceneStore()

        # Auto-save on state changes
        self.register_transition_callback(self._auto_save)

    def _auto_save(self, transition: StateTransition) -> None:
        """Auto-save state on transition."""
        self._scene_store.save_state(self)

    def save_to_store(self) -> bool:
        """Manually save to store."""
        return self._scene_store.save_state(self)

    def load_from_store(self, scene_id: str) -> bool:
        """
        Load state from store.

        Note: This replaces current scene state.
        """
        restored = self._scene_store.restore_scene(scene_id)
        if restored:
            # Copy restored state to self
            self._state = restored._state
            self._state_data = restored._state_data
            self._transition_history = restored._transition_history
            return True
        return False


# Convenience functions

def get_redis_client(host: str = "localhost", port: int = 6379,
                     db: int = 0, password: str = None) -> Any:
    """
    Get Redis client.

    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Optional Redis password

    Returns:
        Redis client, or None if redis not installed
    """
    if redis is None:
        return None

    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True
    )


def create_scene_store(redis_client: Any = None) -> SceneStore:
    """
    Create a SceneStore.

    Args:
        redis_client: Optional Redis client

    Returns:
        SceneStore instance
    """
    return SceneStore(redis_client)
