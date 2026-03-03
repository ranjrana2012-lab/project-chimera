"""
Audience Context Preservation - OpenClaw Orchestrator

Manages audience context (preferences, sentiment, interactions) across scene transitions.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Priority levels for context resolution."""
    CRITICAL = 0
    HIGH = 25
    MEDIUM = 50
    LOW = 75
    BACKGROUND = 100


class ContextMergeStrategy(Enum):
    """Strategies for merging conflicting contexts."""
    PRIORITY = "priority"  # Higher priority wins
    NEWEST = "newest"  # Most recently updated wins
    MERGE = "merge"  # Combine all values
    INTERACTIVE = "interactive"  # Require manual resolution


@dataclass
class AudienceContext:
    """
    Audience context data.

    Contains preferences, sentiment history, and interaction tracking.
    """
    audience_id: str
    preferences: Dict[str, Any]
    sentiment_history: List[float]
    interaction_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Set last updated timestamp."""
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


@dataclass
class AudienceContextSnapshot:
    """
    Snapshot of audience contexts for a scene.

    Captures all active audience contexts at a point in time.
    """
    scene_id: str
    contexts: Dict[str, AudienceContext]
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_id: str = field(default_factory=lambda: f"acs-{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "snapshot_id": self.snapshot_id,
            "scene_id": self.scene_id,
            "contexts": {
                aud_id: {
                    "audience_id": ctx.audience_id,
                    "preferences": ctx.preferences,
                    "sentiment_history": ctx.sentiment_history,
                    "interaction_count": ctx.interaction_count,
                    "metadata": ctx.metadata,
                    "last_updated": ctx.last_updated.isoformat() if ctx.last_updated else None
                }
                for aud_id, ctx in self.contexts.items()
            },
            "captured_at": self.captured_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudienceContextSnapshot":
        """
        Create snapshot from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AudienceContextSnapshot
        """
        contexts = {}
        for aud_id, ctx_data in data.get("contexts", {}).items():
            contexts[aud_id] = AudienceContext(
                audience_id=ctx_data["audience_id"],
                preferences=ctx_data["preferences"],
                sentiment_history=ctx_data["sentiment_history"],
                interaction_count=ctx_data["interaction_count"],
                metadata=ctx_data.get("metadata", {}),
                last_updated=datetime.fromisoformat(ctx_data["last_updated"]) if ctx_data.get("last_updated") else None
            )

        return cls(
            snapshot_id=data.get("snapshot_id", f"acs-{uuid.uuid4().hex[:8]}"),
            scene_id=data["scene_id"],
            contexts=contexts,
            captured_at=datetime.fromisoformat(data["captured_at"]) if data.get("captured_at") else datetime.now(timezone.utc)
        )


@dataclass
class ContextDiff:
    """
    Difference between two audience contexts.

    Tracks changes in preferences, sentiment, and interactions.
    """
    audience_id: str
    added_preferences: Dict[str, Any] = field(default_factory=dict)
    modified_preferences: Dict[str, Any] = field(default_factory=dict)
    removed_preferences: List[str] = field(default_factory=list)
    sentiment_added: int = 0
    interaction_delta: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(old_context: AudienceContext, new_context: AudienceContext) -> "ContextDiff":
        """
        Create diff between two contexts.

        Args:
            old_context: Original context
            new_context: New context

        Returns:
            ContextDiff
        """
        if old_context.audience_id != new_context.audience_id:
            raise ValueError("Cannot diff contexts with different audience IDs")

        diff = ContextDiff(audience_id=old_context.audience_id)

        # Check for added/modified preferences
        all_keys = set(old_context.preferences.keys()) | set(new_context.preferences.keys())

        for key in all_keys:
            old_val = old_context.preferences.get(key)
            new_val = new_context.preferences.get(key)

            if old_val is None and new_val is not None:
                diff.added_preferences[key] = new_val
            elif old_val != new_val:
                diff.modified_preferences[key] = new_val
            elif new_val is None and old_val is not None:
                diff.removed_preferences.append(key)

        # Sentiment history changes
        diff.sentiment_added = len(new_context.sentiment_history) - len(old_context.sentiment_history)

        # Interaction count delta
        diff.interaction_delta = new_context.interaction_count - old_context.interaction_count

        return diff


@dataclass
class ContextMergeResult:
    """
    Result of merging contexts.

    Contains merged context or error information.
    """
    success: bool
    merged_context: Optional[AudienceContext] = None
    error: Optional[str] = None
    conflicts_resolved: int = 0


class AudienceContextManager:
    """
    Manages audience context across scenes.

    Handles capturing, restoring, and merging audience contexts.
    """

    def __init__(self):
        """Initialize context manager."""
        self._snapshots: Dict[str, AudienceContextSnapshot] = {}
        self._active_contexts: Dict[str, AudienceContext] = {}
        self._scene_audiences: Dict[str, List[str]] = {}

        logger.info("AudienceContextManager initialized")

    def register_context(self, scene_id: str, context: AudienceContext) -> None:
        """
        Register an audience context for a scene.

        Args:
            scene_id: Scene identifier
            context: Audience context
        """
        self._active_contexts[context.audience_id] = context

        if scene_id not in self._scene_audiences:
            self._scene_audiences[scene_id] = []

        if context.audience_id not in self._scene_audiences[scene_id]:
            self._scene_audiences[scene_id].append(context.audience_id)

        logger.debug(
            f"Registered context for {context.audience_id} in scene {scene_id}"
        )

    def get_context(self, audience_id: str) -> Optional[AudienceContext]:
        """
        Get active context for audience.

        Args:
            audience_id: Audience identifier

        Returns:
            AudienceContext or None
        """
        return self._active_contexts.get(audience_id)

    def capture_context(self, scene_id: str) -> str:
        """
        Capture all contexts for a scene.

        Args:
            scene_id: Scene to capture

        Returns:
            Snapshot ID
        """
        # Get all audience IDs for this scene
        audience_ids = self._scene_audiences.get(scene_id, [])

        contexts = {}
        for aud_id in audience_ids:
            if aud_id in self._active_contexts:
                contexts[aud_id] = self._active_contexts[aud_id]

        snapshot = AudienceContextSnapshot(
            scene_id=scene_id,
            contexts=contexts
        )

        self._snapshots[snapshot.snapshot_id] = snapshot

        logger.info(
            f"Captured context snapshot {snapshot.snapshot_id} "
            f"for scene {scene_id} ({len(contexts)} audiences)"
        )

        return snapshot.snapshot_id

    def restore_context(
        self,
        snapshot_id: str,
        target_scene_id: str,
        strategy: ContextMergeStrategy = ContextMergeStrategy.PRIORITY
    ) -> Optional[Dict[str, AudienceContext]]:
        """
        Restore contexts from snapshot to scene.

        Args:
            snapshot_id: Snapshot to restore
            target_scene_id: Scene to restore to
            strategy: Merge strategy for conflicts

        Returns:
            Dictionary of audience_id -> AudienceContext
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None

        restored_contexts = {}

        for aud_id, context in snapshot.contexts.items():
            # Check if active context exists
            active_context = self._active_contexts.get(aud_id)

            if active_context is None:
                # No active context, just restore
                restored_contexts[aud_id] = context
                self.register_context(target_scene_id, context)
            else:
                # Merge with active context (snapshot takes priority for "restore")
                merge_result = self.merge_contexts(
                    [context, active_context],  # snapshot first
                    strategy=strategy
                )

                if merge_result.success and merge_result.merged_context:
                    restored_contexts[aud_id] = merge_result.merged_context
                    self.register_context(target_scene_id, merge_result.merged_context)

        logger.info(
            f"Restored {len(restored_contexts)} contexts from snapshot {snapshot_id} "
            f"to scene {target_scene_id}"
        )

        return restored_contexts

    def merge_contexts(
        self,
        contexts: List[AudienceContext],
        strategy: ContextMergeStrategy = ContextMergeStrategy.PRIORITY,
        priority_map: Optional[Dict[str, ContextPriority]] = None
    ) -> ContextMergeResult:
        """
        Merge multiple contexts for the same audience.

        Args:
            contexts: List of contexts to merge
            strategy: Merge strategy
            priority_map: Optional priority mapping

        Returns:
            ContextMergeResult
        """
        if not contexts:
            return ContextMergeResult(
                success=False,
                error="No contexts to merge"
            )

        # Verify all contexts are for same audience
        audience_id = contexts[0].audience_id
        if not all(ctx.audience_id == audience_id for ctx in contexts):
            return ContextMergeResult(
                success=False,
                error="Cannot merge contexts for different audiences"
            )

        try:
            if strategy == ContextMergeStrategy.PRIORITY:
                return self._merge_by_priority(contexts, priority_map)
            elif strategy == ContextMergeStrategy.NEWEST:
                return self._merge_by_newest(contexts)
            elif strategy == ContextMergeStrategy.MERGE:
                return self._merge_all(contexts)
            else:
                return ContextMergeResult(
                    success=False,
                    error=f"Strategy {strategy.value} not implemented"
                )

        except Exception as e:
            return ContextMergeResult(
                success=False,
                error=f"Merge failed: {str(e)}"
            )

    def _merge_by_priority(
        self,
        contexts: List[AudienceContext],
        priority_map: Optional[Dict[str, ContextPriority]]
    ) -> ContextMergeResult:
        """Merge by priority (first context wins if no priority map)."""
        # If no priority map, use order (first wins)
        if priority_map is None:
            merged = contexts[0]
            return ContextMergeResult(
                success=True,
                merged_context=merged,
                conflicts_resolved=len(contexts) - 1
            )

        # Find highest priority context
        # Note: Lower priority value = higher priority
        best_context = None
        best_priority = None

        for context in contexts:
            # Find priority for this context's scene
            # For simplicity, use first matching priority or default to MEDIUM
            priority = priority_map.get(context.audience_id, ContextPriority.MEDIUM)

            if best_priority is None or priority.value < best_priority.value:
                best_context = context
                best_priority = priority

        return ContextMergeResult(
            success=True,
            merged_context=best_context,
            conflicts_resolved=len(contexts) - 1
        )

    def _merge_by_newest(self, contexts: List[AudienceContext]) -> ContextMergeResult:
        """Merge by newest timestamp."""
        best_context = max(contexts, key=lambda c: c.last_updated or datetime.min)

        return ContextMergeResult(
            success=True,
            merged_context=best_context,
            conflicts_resolved=len(contexts) - 1
        )

    def _merge_all(self, contexts: List[AudienceContext]) -> ContextMergeResult:
        """Merge all contexts together."""
        merged_preferences = {}
        merged_sentiment = []
        max_interactions = 0
        merged_metadata = {}

        for context in contexts:
            # Merge preferences (later values overwrite)
            merged_preferences.update(context.preferences)

            # Combine sentiment history
            merged_sentiment.extend(context.sentiment_history)

            # Max interaction count
            max_interactions = max(max_interactions, context.interaction_count)

            # Merge metadata
            merged_metadata.update(context.metadata)

        # Create merged context
        merged = AudienceContext(
            audience_id=contexts[0].audience_id,
            preferences=merged_preferences,
            sentiment_history=merged_sentiment,
            interaction_count=max_interactions,
            metadata=merged_metadata
        )

        return ContextMergeResult(
            success=True,
            merged_context=merged,
            conflicts_resolved=len(contexts) - 1
        )

    def get_context_diff(
        self,
        old_context: AudienceContext,
        new_context: AudienceContext
    ) -> ContextDiff:
        """
        Get difference between two contexts.

        Args:
            old_context: Original context
            new_context: New context

        Returns:
            ContextDiff
        """
        return ContextDiff.create(old_context, new_context)

    def get_snapshot(self, snapshot_id: str) -> Optional[AudienceContextSnapshot]:
        """
        Get snapshot by ID.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            AudienceContextSnapshot or None
        """
        return self._snapshots.get(snapshot_id)

    def get_snapshot_status(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get snapshot status.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Status dict or None
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return None

        return {
            "snapshot_id": snapshot.snapshot_id,
            "scene_id": snapshot.scene_id,
            "audience_count": len(snapshot.contexts),
            "captured_at": snapshot.captured_at.isoformat()
        }

    def persist_snapshot(self, snapshot_id: str) -> bool:
        """
        Persist snapshot to storage.

        Note: In production, this would persist to Redis or database.
        For now, snapshots are already in memory.

        Args:
            snapshot_id: Snapshot to persist

        Returns:
            True if successful
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        # In production: persist to Redis/file
        # For now, just log
        logger.info(f"Snapshot {snapshot_id} persisted (in-memory)")

        return True

    def cleanup_old_snapshots(self, max_age_seconds: float = 3600) -> int:
        """
        Remove old snapshots.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of snapshots cleaned up
        """
        now = datetime.now(timezone.utc)
        cleaned = 0

        to_remove = []

        for snapshot_id, snapshot in self._snapshots.items():
            age = (now - snapshot.captured_at).total_seconds()
            if age > max_age_seconds:
                to_remove.append(snapshot_id)

        for snapshot_id in to_remove:
            del self._snapshots[snapshot_id]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old snapshots")

        return cleaned

    def update_sentiment(self, audience_id: str, sentiment: float) -> bool:
        """
        Update sentiment history for audience.

        Args:
            audience_id: Audience identifier
            sentiment: Sentiment value (0-1)

        Returns:
            True if updated
        """
        context = self._active_contexts.get(audience_id)
        if not context:
            return False

        context.sentiment_history.append(sentiment)
        context.last_updated = datetime.now(timezone.utc)

        return True

    def increment_interactions(self, audience_id: str, count: int = 1) -> bool:
        """
        Increment interaction count for audience.

        Args:
            audience_id: Audience identifier
            count: Number to add

        Returns:
            True if updated
        """
        context = self._active_contexts.get(audience_id)
        if not context:
            return False

        context.interaction_count += count
        context.last_updated = datetime.now(timezone.utc)

        return True

    def get_all_contexts_for_scene(self, scene_id: str) -> List[AudienceContext]:
        """
        Get all contexts for a scene.

        Args:
            scene_id: Scene identifier

        Returns:
            List of AudienceContext
        """
        audience_ids = self._scene_audiences.get(scene_id, [])

        contexts = []
        for aud_id in audience_ids:
            if aud_id in self._active_contexts:
                contexts.append(self._active_contexts[aud_id])

        return contexts
