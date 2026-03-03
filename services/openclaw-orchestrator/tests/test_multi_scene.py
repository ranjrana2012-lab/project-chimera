"""
Unit tests for Multi-Scene Orchestrator.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '.')

from core.scene_manager import (
    SceneManager,
    SceneConfig,
    SceneState
)
from core.multi_scene import (
    MultiSceneOrchestrator,
    SceneSlot,
    SceneConflictError,
    SceneLimitError,
    create_orchestrator
)


class TestSceneSlot:
    """Test SceneSlot dataclass."""

    def test_create_slot(self):
        """Create a scene slot."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        slot = SceneSlot(
            scene_id="test",
            manager=manager,
            priority=50,
            created_at=datetime.utcnow()
        )

        assert slot.scene_id == "test"
        assert slot.manager is manager
        assert slot.priority == 50
        assert slot.is_active is False  # IDLE state


class TestMultiSceneOrchestratorInit:
    """Test MultiSceneOrchestrator initialization."""

    def test_init_default(self):
        """Initialize with defaults."""
        orchestrator = MultiSceneOrchestrator()

        assert orchestrator._max_scenes == 5
        assert orchestrator.scene_count == 0
        assert orchestrator.active_scene_count == 0

    def test_init_custom_max(self):
        """Initialize with custom max scenes."""
        orchestrator = MultiSceneOrchestrator(max_scenes=3)

        assert orchestrator._max_scenes == 3

    def test_init_with_store(self):
        """Initialize with scene store."""
        store_mock = Mock()

        orchestrator = MultiSceneOrchestrator(
            max_scenes=5,
            scene_store=store_mock
        )

        assert orchestrator._scene_store is store_mock


class TestAddScene:
    """Test adding scenes to orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator(max_scenes=3)

    @pytest.fixture
    def manager_factory(self):
        """Create scene managers."""
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            return SceneManager(config)
        return create_manager

    def test_add_scene(self, orchestrator, manager_factory):
        """Add a scene successfully."""
        manager = manager_factory("scene-001")

        result = orchestrator.add_scene(manager)

        assert result is True
        assert orchestrator.scene_count == 1

    def test_add_active_scene(self, orchestrator, manager_factory):
        """Add an active scene."""
        manager = manager_factory("scene-001")
        manager.initialize()
        manager.activate()

        result = orchestrator.add_scene(manager, priority=50)

        assert result is True
        assert orchestrator.active_scene_count == 1

    def test_add_duplicate_scene_id(self, orchestrator, manager_factory):
        """Cannot add duplicate scene ID."""
        manager1 = manager_factory("scene-001")
        manager2 = manager_factory("scene-001")

        orchestrator.add_scene(manager1)

        with pytest.raises(SceneConflictError):
            orchestrator.add_scene(manager2)

    def test_add_beyond_limit(self, orchestrator, manager_factory):
        """Cannot add beyond max concurrent scenes."""
        # Add 3 active scenes (max is 3)
        for i in range(3):
            manager = manager_factory(f"scene-{i:03d}")
            manager.initialize()
            manager.activate()
            orchestrator.add_scene(manager, priority=50)

        # Try to add 4th active scene
        manager4 = manager_factory("scene-004")
        manager4.initialize()
        manager4.activate()

        with pytest.raises(SceneLimitError):
            orchestrator.add_scene(manager4, priority=50)

    def test_add_beyond_limit_with_higher_priority(self, orchestrator, manager_factory):
        """Higher priority scene replaces lower priority."""
        # Add 3 active scenes with low priority
        for i in range(3):
            manager = manager_factory(f"scene-{i:03d}")
            manager.initialize()
            manager.activate()
            orchestrator.add_scene(manager, priority=10)

        # Add higher priority scene - should pause one low priority scene
        manager_high = manager_factory("scene-high")
        manager_high.initialize()
        manager_high.activate()

        # This should work if priority-based eviction is implemented
        # For now, it will raise SceneLimitError unless we make room first
        orchestrator.make_room_for_scene(100)
        result = orchestrator.add_scene(manager_high, priority=100)

        assert result is True


class TestRemoveScene:
    """Test removing scenes from orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator()

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            return SceneManager(config)
        return create_manager

    def test_remove_scene(self, orchestrator, manager_factory):
        """Remove a scene."""
        manager = manager_factory("scene-001")
        orchestrator.add_scene(manager)

        result = orchestrator.remove_scene("scene-001")

        assert result is True
        assert orchestrator.scene_count == 0

    def test_remove_nonexistent_scene(self, orchestrator):
        """Remove non-existent scene returns False."""
        result = orchestrator.remove_scene("nonexistent")

        assert result is False

    def test_remove_active_scene(self, orchestrator, manager_factory):
        """Remove active scene."""
        manager = manager_factory("scene-001")
        manager.initialize()
        manager.activate()
        orchestrator.add_scene(manager)

        result = orchestrator.remove_scene("scene-001")

        assert result is True


class TestGetScene:
    """Test retrieving scenes."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator()

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            return manager
        return create_manager

    def test_get_scene(self, orchestrator, manager_factory):
        """Get scene by ID."""
        manager = manager_factory("scene-001")
        orchestrator.add_scene(manager)

        retrieved = orchestrator.get_scene("scene-001")

        assert retrieved is manager

    def test_get_scene_not_found(self, orchestrator):
        """Get non-existent scene returns None."""
        retrieved = orchestrator.get_scene("nonexistent")

        assert retrieved is None

    def test_get_active_scenes(self, orchestrator, manager_factory):
        """Get all active scenes."""
        # Add mixed scenes
        manager1 = manager_factory("scene-001")
        manager1.activate()
        orchestrator.add_scene(manager1)

        manager2 = manager_factory("scene-002")
        orchestrator.add_scene(manager2)

        active = orchestrator.get_active_scenes()

        assert len(active) == 1
        assert active[0].scene_id == "scene-001"

    def test_get_scenes_by_priority(self, orchestrator, manager_factory):
        """Get scenes sorted by priority."""
        manager1 = manager_factory("scene-001")
        orchestrator.add_scene(manager1, priority=10)

        manager2 = manager_factory("scene-002")
        orchestrator.add_scene(manager2, priority=90)

        manager3 = manager_factory("scene-003")
        orchestrator.add_scene(manager3, priority=50)

        scenes = orchestrator.get_scenes_by_priority()

        # Should be ordered: 002 (90), 003 (50), 001 (10)
        assert scenes[0].scene_id == "scene-002"
        assert scenes[1].scene_id == "scene-003"
        assert scenes[2].scene_id == "scene-001"


class TestPauseResumeScene:
    """Test pausing and resuming scenes."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator()

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()
            return manager
        return create_manager

    def test_pause_scene(self, orchestrator, manager_factory):
        """Pause a scene."""
        manager = manager_factory("scene-001")
        orchestrator.add_scene(manager)

        result = orchestrator.pause_scene("scene-001", "Testing pause")

        assert result is True
        assert manager.state == SceneState.PAUSED

    def test_resume_scene(self, orchestrator, manager_factory):
        """Resume a paused scene."""
        manager = manager_factory("scene-001")
        orchestrator.add_scene(manager)
        orchestrator.pause_scene("scene-001")

        result = orchestrator.resume_scene("scene-001")

        assert result is True
        assert manager.state == SceneState.ACTIVE

    def test_pause_nonexistent_scene(self, orchestrator):
        """Pause non-existent scene returns False."""
        result = orchestrator.pause_scene("nonexistent")

        assert result is False


class TestSceneStatus:
    """Test scene status methods."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator(max_scenes=3)

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            return SceneManager(config)
        return create_manager

    def test_get_scene_states(self, orchestrator, manager_factory):
        """Get all scene states."""
        manager1 = manager_factory("scene-001")
        manager1.initialize()
        orchestrator.add_scene(manager1)

        manager2 = manager_factory("scene-002")
        manager2.initialize()
        manager2.activate()
        orchestrator.add_scene(manager2)

        states = orchestrator.get_scene_states()

        assert states["scene-001"] == "loading"
        assert states["scene-002"] == "active"

    def test_get_scene_status(self, orchestrator, manager_factory):
        """Get overall orchestrator status."""
        # Add 2 active scenes
        for i in range(2):
            manager = manager_factory(f"scene-{i:03d}")
            manager.initialize()
            manager.activate()
            orchestrator.add_scene(manager)

        # Add 1 idle scene
        manager_idle = manager_factory("idle-scene")
        orchestrator.add_scene(manager_idle)

        status = orchestrator.get_scene_status()

        assert status["total_scenes"] == 3
        assert status["active_scenes"] == 2
        assert status["max_scenes"] == 3
        assert status["available_slots"] == 1

    def test_can_add_scene(self, orchestrator, manager_factory):
        """Check if scene can be added."""
        # Empty orchestrator
        assert orchestrator.can_add_scene(50) is True

        # Add 3 active scenes (max is 3)
        for i in range(3):
            manager = manager_factory(f"scene-{i:03d}")
            manager.initialize()
            manager.activate()
            orchestrator.add_scene(manager, priority=50)

        # At limit but can make room with higher priority
        assert orchestrator.can_add_scene(60) is True

        # Cannot make room with same/lower priority
        assert orchestrator.can_add_scene(50) is False


class TestMakeRoomForScene:
    """Test making room for new scenes."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator(max_scenes=2)

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()
            return manager
        return create_manager

    def test_make_room_with_higher_priority(self, orchestrator, manager_factory):
        """Higher priority scene pauses lower priority scenes."""
        # Add 2 active scenes with low priority
        manager1 = manager_factory("scene-001")
        orchestrator.add_scene(manager1, priority=10)

        manager2 = manager_factory("scene-002")
        orchestrator.add_scene(manager2, priority=20)

        # Make room for high priority scene
        paused = orchestrator.make_room_for_scene(100)

        # Both lower priority scenes should be paused
        assert len(paused) == 2
        assert "scene-001" in paused  # Lowest priority paused

    def test_make_room_cannot_pause(self, orchestrator, manager_factory):
        """Cannot make room if all scenes have higher priority."""
        # Add 2 active scenes with high priority
        manager1 = manager_factory("scene-001")
        orchestrator.add_scene(manager1, priority=90)

        manager2 = manager_factory("scene-002")
        orchestrator.add_scene(manager2, priority=80)

        # Try to make room for low priority scene
        with pytest.raises(SceneLimitError):
            orchestrator.make_room_for_scene(50)


class TestCleanup:
    """Test cleanup methods."""

    @pytest.fixture
    def orchestrator(self):
        return MultiSceneOrchestrator()

    @pytest.fixture
    def manager_factory(self):
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            return manager
        return create_manager

    def test_cleanup_inactive_scenes(self, orchestrator, manager_factory):
        """Clean up old inactive scenes."""
        # Add an old completed scene
        old_manager = manager_factory("old-scene")
        old_manager.initialize()
        old_manager.activate()  # Must activate before completing
        old_manager.complete()
        orchestrator.add_scene(old_manager)

        # Manually set the slot creation time to be old
        slot = orchestrator._scenes["old-scene"]
        # Create a new slot with old created_at time
        old_slot = SceneSlot(
            scene_id=slot.scene_id,
            manager=slot.manager,
            priority=slot.priority,
            created_at=datetime.utcnow() - timedelta(hours=25)
        )
        orchestrator._scenes["old-scene"] = old_slot

        # Add a recent scene
        recent_manager = manager_factory("recent-scene")
        orchestrator.add_scene(recent_manager)

        # Cleanup with 24 hour threshold
        cleaned = orchestrator.cleanup_inactive_scenes(max_age_hours=24)

        assert cleaned == 1
        assert "old-scene" not in orchestrator._scenes
        assert "recent-scene" in orchestrator._scenes

    def test_enforce_scene_limit(self):
        """Enforce maximum concurrent scene limit."""
        # Create a max-2 orchestrator
        orchestrator = MultiSceneOrchestrator(max_scenes=2)

        # Add 3 scenes to exceed limit
        # First 2 add successfully, 3rd raises SceneLimitError
        for i in range(3):
            config = SceneConfig(
                scene_id=f"scene-{i:03d}",
                name=f"Scene {i}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()

            try:
                orchestrator.add_scene(manager, priority=50-i)
            except SceneLimitError:
                # 3rd scene can't be added
                pass

        # At this point we have 2 active scenes, enforce should do nothing
        paused = orchestrator.enforce_scene_limit()

        # No scenes should be paused (we're exactly at limit)
        assert len(paused) == 0
        assert orchestrator.active_scene_count <= 2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_orchestrator(self):
        """Create orchestrator with convenience function."""
        orchestrator = create_orchestrator(max_scenes=3)

        assert isinstance(orchestrator, MultiSceneOrchestrator)
        assert orchestrator._max_scenes == 3
