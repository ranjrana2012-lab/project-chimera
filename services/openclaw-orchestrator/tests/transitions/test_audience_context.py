"""
Unit tests for Audience Context Preservation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import json

import sys
sys.path.insert(0, '.')

from transitions.audience_context import (
    AudienceContext,
    AudienceContextSnapshot,
    ContextDiff,
    ContextMergeStrategy,
    ContextMergeResult,
    AudienceContextManager,
    ContextPriority
)


class TestAudienceContext:
    """Test AudienceContext dataclass."""

    def test_create_context(self):
        """Create audience context."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "accessibility": "captions"},
            sentiment_history=[0.5, 0.6, 0.7],
            interaction_count=42
        )

        assert context.audience_id == "aud-001"
        assert context.preferences["language"] == "en"
        assert len(context.sentiment_history) == 3
        assert context.interaction_count == 42

    def test_context_with_metadata(self):
        """Create context with metadata."""
        context = AudienceContext(
            audience_id="aud-002",
            preferences={},
            sentiment_history=[],
            interaction_count=0,
            metadata={"region": "US", "timezone": "EST"}
        )

        assert context.metadata["region"] == "US"


class TestAudienceContextSnapshot:
    """Test AudienceContextSnapshot."""

    def test_create_snapshot(self):
        """Create context snapshot."""
        snapshot = AudienceContextSnapshot(
            scene_id="scene-001",
            contexts={
                "aud-001": AudienceContext(
                    audience_id="aud-001",
                    preferences={"language": "en"},
                    sentiment_history=[0.5],
                    interaction_count=10
                )
            },
            captured_at=datetime.now(timezone.utc)
        )

        assert snapshot.scene_id == "scene-001"
        assert "aud-001" in snapshot.contexts
        assert snapshot.captured_at is not None

    def test_snapshot_serialization(self):
        """Test snapshot to dict conversion."""
        snapshot = AudienceContextSnapshot(
            scene_id="scene-001",
            contexts={
                "aud-001": AudienceContext(
                    audience_id="aud-001",
                    preferences={"language": "en"},
                    sentiment_history=[0.5],
                    interaction_count=10
                )
            }
        )

        data_dict = snapshot.to_dict()

        assert data_dict["scene_id"] == "scene-001"
        assert "contexts" in data_dict
        assert "captured_at" in data_dict

    def test_snapshot_deserialization(self):
        """Test dict to snapshot conversion."""
        data_dict = {
            "scene_id": "scene-002",
            "contexts": {
                "aud-001": {
                    "audience_id": "aud-001",
                    "preferences": {"language": "es"},
                    "sentiment_history": [0.3, 0.4],
                    "interaction_count": 5,
                    "metadata": {}
                }
            },
            "captured_at": "2026-03-04T05:00:00Z"
        }

        snapshot = AudienceContextSnapshot.from_dict(data_dict)

        assert snapshot.scene_id == "scene-002"
        assert "aud-001" in snapshot.contexts
        assert snapshot.contexts["aud-001"].preferences["language"] == "es"


class TestContextDiff:
    """Test ContextDiff."""

    def test_create_diff(self):
        """Create context diff."""
        old_context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=10
        )

        new_context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "theme": "dark"},
            sentiment_history=[0.5, 0.6],
            interaction_count=15
        )

        diff = ContextDiff.create(old_context, new_context)

        assert diff.audience_id == "aud-001"
        assert len(diff.added_preferences) > 0
        assert "theme" in diff.added_preferences
        assert diff.interaction_delta == 5

    def test_empty_diff(self):
        """Empty diff for identical contexts."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=10
        )

        diff = ContextDiff.create(context, context)

        assert len(diff.added_preferences) == 0
        assert len(diff.modified_preferences) == 0
        assert diff.interaction_delta == 0


class TestContextMergeResult:
    """Test ContextMergeResult."""

    def test_successful_merge(self):
        """Create successful merge result."""
        result = ContextMergeResult(
            success=True,
            merged_context=AudienceContext(
                audience_id="aud-001",
                preferences={"language": "en"},
                sentiment_history=[],
                interaction_count=0
            )
        )

        assert result.success is True
        assert result.merged_context is not None
        assert result.error is None

    def test_failed_merge(self):
        """Create failed merge result."""
        result = ContextMergeResult(
            success=False,
            merged_context=None,
            error="Conflicting preferences"
        )

        assert result.success is False
        assert result.merged_context is None
        assert result.error == "Conflicting preferences"


class TestAudienceContextManager:
    """Test AudienceContextManager."""

    @pytest.fixture
    def manager(self):
        """Create context manager."""
        return AudienceContextManager()

    def test_manager_init(self, manager):
        """Initialize manager."""
        assert len(manager._snapshots) == 0
        assert len(manager._active_contexts) == 0

    def test_register_context(self, manager):
        """Register audience context."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[],
            interaction_count=0
        )

        manager.register_context("scene-001", context)

        assert "aud-001" in manager._active_contexts
        assert manager._active_contexts["aud-001"].audience_id == "aud-001"

    def test_capture_context(self, manager):
        """Capture context for scene."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[],
            interaction_count=0
        )

        manager.register_context("scene-001", context)

        snapshot_id = manager.capture_context("scene-001")

        assert snapshot_id is not None
        assert snapshot_id.startswith("acs-")

    def test_restore_context(self, manager):
        """Restore context from snapshot."""
        original = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[],
            interaction_count=10
        )

        manager.register_context("scene-001", original)
        snapshot_id = manager.capture_context("scene-001")

        # Modify context
        modified = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "es"},
            sentiment_history=[],
            interaction_count=0
        )

        manager.register_context("scene-002", modified)

        # Restore
        restored_dict = manager.restore_context(snapshot_id, "scene-002")

        assert restored_dict is not None
        assert "aud-001" in restored_dict
        restored = restored_dict["aud-001"]
        assert restored.preferences["language"] == "en"
        assert restored.interaction_count == 10

    def test_merge_contexts(self, manager):
        """Merge multiple contexts."""
        context1 = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=10
        )

        context2 = AudienceContext(
            audience_id="aud-001",
            preferences={"theme": "dark"},
            sentiment_history=[0.6],
            interaction_count=5
        )

        result = manager.merge_contexts(
            [context1, context2],
            strategy=ContextMergeStrategy.MERGE
        )

        assert result.success is True
        assert "language" in result.merged_context.preferences
        assert "theme" in result.merged_context.preferences

    def test_merge_with_conflict(self, manager):
        """Merge with conflicting preferences."""
        context1 = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[],
            interaction_count=10
        )

        context2 = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "es"},
            sentiment_history=[],
            interaction_count=5
        )

        result = manager.merge_contexts(
            [context1, context2],
            strategy=ContextMergeStrategy.PRIORITY,
            priority_map={"scene-001": ContextPriority.HIGH, "scene-002": ContextPriority.LOW}
        )

        assert result.success is True
        # Higher priority (scene-001) should win
        assert result.merged_context.preferences["language"] == "en"

    def test_get_context_diff(self, manager):
        """Get diff between contexts."""
        old_context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=10
        )

        new_context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "theme": "dark"},
            sentiment_history=[0.5, 0.6],
            interaction_count=15
        )

        diff = manager.get_context_diff(old_context, new_context)

        assert diff.audience_id == "aud-001"
        assert "theme" in diff.added_preferences
        assert diff.interaction_delta == 5

    def test_cleanup_old_snapshots(self, manager):
        """Cleanup old snapshots."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={},
            sentiment_history=[],
            interaction_count=0
        )

        manager.register_context("scene-001", context)
        manager.capture_context("scene-001")

        # Cleanup immediately (max_age=0)
        cleaned = manager.cleanup_old_snapshots(max_age_seconds=0)

        assert cleaned >= 1

    def test_get_snapshot_status(self, manager):
        """Get snapshot status."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={},
            sentiment_history=[],
            interaction_count=0
        )

        manager.register_context("scene-001", context)
        snapshot_id = manager.capture_context("scene-001")

        status = manager.get_snapshot_status(snapshot_id)

        assert status["snapshot_id"] == snapshot_id
        assert status["scene_id"] == "scene-001"

    def test_persist_and_load_snapshot(self, manager):
        """Persist and load snapshot."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=10
        )

        manager.register_context("scene-001", context)
        snapshot_id = manager.capture_context("scene-001")

        # Persist
        persisted = manager.persist_snapshot(snapshot_id)

        assert persisted is True

        # Load (simulated - in real implementation would use Redis/file)
        loaded = manager.get_snapshot(snapshot_id)

        assert loaded is not None
        assert loaded.scene_id == "scene-001"

    def test_update_sentiment_history(self, manager):
        """Update sentiment history for audience."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={},
            sentiment_history=[0.5, 0.6],
            interaction_count=0
        )

        manager.register_context("scene-001", context)

        # Update with new sentiment
        manager.update_sentiment("aud-001", 0.7)

        updated = manager.get_context("aud-001")

        assert updated is not None
        assert len(updated.sentiment_history) == 3
        assert updated.sentiment_history[-1] == 0.7

    def test_increment_interaction_count(self, manager):
        """Increment interaction count."""
        context = AudienceContext(
            audience_id="aud-001",
            preferences={},
            sentiment_history=[],
            interaction_count=10
        )

        manager.register_context("scene-001", context)

        manager.increment_interactions("aud-001", 5)

        updated = manager.get_context("aud-001")

        assert updated is not None
        assert updated.interaction_count == 15
