"""
Unit tests for Transition Undo/Redo.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import sys
sys.path.insert(0, '.')

from transitions.undo_redo import (
    TransitionRecord,
    TransitionHistory,
    UndoRedoManager,
    UndoRedoResult
)

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.transition_effects import TransitionType, TransitionEffect


class TestTransitionRecord:
    """Test TransitionRecord dataclass."""

    def test_create_record(self):
        """Create transition record."""
        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            metadata={"duration": 3.0}
        )

        assert record.source_scene_id == "scene-001"
        assert record.target_scene_id == "scene-002"
        assert record.transition_type == TransitionType.FADE
        assert record.undone is False

    def test_record_with_timestamp(self):
        """Create record with custom timestamp."""
        timestamp = datetime.now(timezone.utc)
        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            timestamp=timestamp
        )

        assert record.timestamp == timestamp

    def test_mark_undone(self):
        """Mark record as undone."""
        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        assert record.undone is False

        record.mark_undone()

        assert record.undone is True
        assert record.undone_at is not None


class TestTransitionHistory:
    """Test TransitionHistory stack."""

    def test_history_init(self):
        """Initialize history stack."""
        history = TransitionHistory(max_size=10)

        assert len(history._records) == 0
        assert history._max_size == 10

    def test_push_record(self):
        """Push record to history."""
        history = TransitionHistory()

        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        history.push(record)

        assert len(history._records) == 1

    def test_max_size_limit(self):
        """Test max size limit enforcement."""
        history = TransitionHistory(max_size=3)

        # Push 4 records
        for i in range(4):
            record = TransitionRecord(
                source_scene_id=f"scene-{i:03d}",
                target_scene_id=f"scene-{i+1:03d}",
                transition_type=TransitionType.CUT
            )
            history.push(record)

        # Should only have 3 (oldest evicted)
        assert len(history._records) == 3

    def test_peek_latest(self):
        """Peek at latest record without removing."""
        history = TransitionHistory()

        record1 = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        record2 = TransitionRecord(
            source_scene_id="scene-002",
            target_scene_id="scene-003",
            transition_type=TransitionType.CUT
        )

        history.push(record1)
        history.push(record2)

        latest = history.peek()

        assert latest is not None
        assert latest.target_scene_id == "scene-003"
        assert len(history._records) == 2  # Not removed

    def test_pop_latest(self):
        """Pop latest record."""
        history = TransitionHistory()

        record1 = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        record2 = TransitionRecord(
            source_scene_id="scene-002",
            target_scene_id="scene-003",
            transition_type=TransitionType.CUT
        )

        history.push(record1)
        history.push(record2)

        popped = history.pop()

        assert popped is not None
        assert popped.target_scene_id == "scene-003"
        assert len(history._records) == 1  # Removed

    def test_get_history(self):
        """Get all records."""
        history = TransitionHistory()

        for i in range(3):
            record = TransitionRecord(
                source_scene_id=f"scene-{i:03d}",
                target_scene_id=f"scene-{i+1:03d}",
                transition_type=TransitionType.CUT
            )
            history.push(record)

        records = history.get_records()

        assert len(records) == 3

    def test_clear_history(self):
        """Clear all records."""
        history = TransitionHistory()

        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        history.push(record)
        assert len(history._records) == 1

        history.clear()

        assert len(history._records) == 0


class TestUndoRedoManager:
    """Test UndoRedoManager."""

    @pytest.fixture
    def manager(self):
        """Create undo/redo manager."""
        return UndoRedoManager(max_history=10)

    @pytest.fixture
    def scene_manager_factory(self):
        """Create scene managers."""
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

    def test_manager_init(self, manager):
        """Initialize manager."""
        assert len(manager._history._records) == 0
        assert len(manager._redo_stack) == 0

    def test_record_transition(self, manager):
        """Record a transition."""
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            metadata={"duration": 3.0}
        )

        assert len(manager._history._records) == 1
        assert len(manager._redo_stack) == 0  # Redo cleared on new action

    def test_undo_transition(self, manager, scene_manager_factory):
        """Undo a transition."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        # Record transition
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        # Undo: current scene is target, revert to source
        result = manager.undo(target, source)

        assert result.success is True
        assert result.action == "undo"
        assert result.previous_scene == "scene-002"
        assert result.new_scene == "scene-001"

    def test_undo_with_no_history(self, manager, scene_manager_factory):
        """Undo with no history returns failure."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        result = manager.undo(source, target)

        assert result.success is False
        assert "No history" in result.error

    def test_redo_transition(self, manager, scene_manager_factory):
        """Redo an undone transition."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        # Record and undo
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        manager.undo(target, source)

        # Redo: current is source, go to target
        result = manager.redo(source, target)

        assert result.success is True
        assert result.action == "redo"
        assert result.previous_scene == "scene-001"
        assert result.new_scene == "scene-002"

    def test_redo_with_no_redo_stack(self, manager, scene_manager_factory):
        """Redo with nothing to redo returns failure."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        # Don't undo, try to redo
        result = manager.redo(source, target)

        assert result.success is False
        assert "Nothing to redo" in result.error

    def test_new_action_clears_redo(self, manager):
        """New action clears redo stack."""
        # Record and undo first transition
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        # Undo (adds to redo stack)
        # We can't fully undo without scene managers, but let's test the stack
        manager._add_to_redo(manager._history.peek())

        assert len(manager._redo_stack) == 1

        # New action clears redo
        manager.record_transition(
            source_scene_id="scene-002",
            target_scene_id="scene-003",
            transition_type=TransitionType.CUT
        )

        assert len(manager._redo_stack) == 0

    def test_get_history_count(self, manager):
        """Get history count."""
        assert manager.get_history_count() == 0

        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        assert manager.get_history_count() == 1

    def test_get_redo_count(self, manager):
        """Get redo count."""
        assert manager.get_redo_count() == 0

        # Add to redo stack manually
        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )
        manager._add_to_redo(record)

        assert manager.get_redo_count() == 1

    def test_can_undo(self, manager):
        """Check if undo is possible."""
        assert manager.can_undo() is False

        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        assert manager.can_undo() is True

    def test_can_redo(self, manager):
        """Check if redo is possible."""
        assert manager.can_redo() is False

        # Add to redo stack manually
        record = TransitionRecord(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )
        manager._add_to_redo(record)

        assert manager.can_redo() is True

    def test_clear_history(self, manager):
        """Clear all history."""
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        assert manager.get_history_count() == 1

        manager.clear_history()

        assert manager.get_history_count() == 0
        assert manager.get_redo_count() == 0

    def test_get_history_records(self, manager):
        """Get all history records."""
        for i in range(3):
            manager.record_transition(
                source_scene_id=f"scene-{i:03d}",
                target_scene_id=f"scene-{i+1:03d}",
                transition_type=TransitionType.CUT
            )

        records = manager.get_history()

        assert len(records) == 3
        assert records[0].source_scene_id == "scene-000"
