"""
Transition Undo/Redo - OpenClaw Orchestrator

Manages undo/redo functionality for scene transitions.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import deque
import uuid

from core.scene_manager import SceneManager, SceneState
from transitions.transition_effects import TransitionType

logger = logging.getLogger(__name__)


@dataclass
class TransitionRecord:
    """
    Record of a scene transition.

    Contains all information needed to undo/redo a transition.
    """
    source_scene_id: str
    target_scene_id: str
    transition_type: TransitionType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    undone: bool = False
    undone_at: Optional[datetime] = None
    record_id: str = field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:8]}")

    def mark_undone(self) -> None:
        """Mark this record as undone."""
        self.undone = True
        self.undone_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "source_scene_id": self.source_scene_id,
            "target_scene_id": self.target_scene_id,
            "transition_type": self.transition_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "undone": self.undone,
            "undone_at": self.undone_at.isoformat() if self.undone_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionRecord":
        """Create from dictionary."""
        return cls(
            record_id=data.get("record_id", f"tr-{uuid.uuid4().hex[:8]}"),
            source_scene_id=data["source_scene_id"],
            target_scene_id=data["target_scene_id"],
            transition_type=TransitionType(data["transition_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            metadata=data.get("metadata", {}),
            undone=data.get("undone", False),
            undone_at=datetime.fromisoformat(data["undone_at"]) if data.get("undone_at") else None
        )


class TransitionHistory:
    """
    Stack of transition records.

    Maintains a fixed-size history of transitions.
    """

    DEFAULT_MAX_SIZE = 50

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE):
        """
        Initialize history stack.

        Args:
            max_size: Maximum number of records to keep
        """
        self._records: deque[TransitionRecord] = deque(maxlen=max_size)
        self._max_size = max_size

        logger.debug(f"TransitionHistory initialized (max_size={max_size})")

    def push(self, record: TransitionRecord) -> None:
        """
        Push record to history.

        Args:
            record: Record to add
        """
        self._records.append(record)
        logger.debug(
            f"Added transition record {record.record_id} to history "
            f"({len(self._records)}/{self._max_size})"
        )

    def peek(self) -> Optional[TransitionRecord]:
        """
        Peek at latest record without removing.

        Returns:
            Latest record or None if empty
        """
        if not self._records:
            return None
        return self._records[-1]

    def pop(self) -> Optional[TransitionRecord]:
        """
        Pop latest record.

        Returns:
            Latest record or None if empty
        """
        if not self._records:
            return None

        record = self._records.pop()
        logger.debug(f"Popped transition record {record.record_id}")

        return record

    def get_records(self) -> List[TransitionRecord]:
        """
        Get all records.

        Returns:
            List of all records (oldest to newest)
        """
        return list(self._records)

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()
        logger.debug("TransitionHistory cleared")

    @property
    def size(self) -> int:
        """Get current size."""
        return len(self._records)

    @property
    def is_empty(self) -> bool:
        """Check if history is empty."""
        return len(self._records) == 0


@dataclass
class UndoRedoResult:
    """
    Result of an undo/redo operation.

    Contains details about the operation.
    """
    success: bool
    action: str  # "undo" or "redo"
    previous_scene: str
    new_scene: str
    transition_type: Optional[TransitionType] = None
    error: Optional[str] = None
    record_id: Optional[str] = None


class UndoRedoManager:
    """
    Manages undo/redo functionality for transitions.

    Tracks transition history and allows reverting/reapplying transitions.
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize undo/redo manager.

        Args:
            max_history: Maximum history size
        """
        self._history = TransitionHistory(max_size=max_history)
        self._redo_stack: List[TransitionRecord] = []

        logger.info(f"UndoRedoManager initialized (max_history={max_history})")

    def record_transition(
        self,
        source_scene_id: str,
        target_scene_id: str,
        transition_type: TransitionType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record a transition in history.

        Args:
            source_scene_id: Scene transitioning from
            target_scene_id: Scene transitioning to
            transition_type: Type of transition
            metadata: Optional metadata

        Returns:
            Record ID
        """
        # Clear redo stack on new action
        self._redo_stack.clear()

        record = TransitionRecord(
            source_scene_id=source_scene_id,
            target_scene_id=target_scene_id,
            transition_type=transition_type,
            metadata=metadata or {}
        )

        self._history.push(record)

        logger.info(
            f"Recorded transition {source_scene_id} -> {target_scene_id} "
            f"({record.record_id})"
        )

        return record.record_id

    def undo(
        self,
        current_scene: SceneManager,
        previous_scene: SceneManager
    ) -> UndoRedoResult:
        """
        Undo the last transition.

        Args:
            current_scene: Current active scene (target of transition)
            previous_scene: Scene to revert to (source of transition)

        Returns:
            UndoRedoResult
        """
        record = self._history.peek()

        if record is None:
            return UndoRedoResult(
                success=False,
                action="undo",
                previous_scene=current_scene.scene_id,
                new_scene=previous_scene.scene_id,
                error="No history to undo"
            )

        if record.undone:
            return UndoRedoResult(
                success=False,
                action="undo",
                previous_scene=current_scene.scene_id,
                new_scene=previous_scene.scene_id,
                error="Already undone"
            )

        try:
            # Perform undo by activating previous scene
            if previous_scene.state != SceneState.ACTIVE:
                previous_scene.activate()

            # Complete current scene
            if current_scene.state == SceneState.ACTIVE:
                current_scene.complete("Transition undone")

            # Mark record as undone
            record.mark_undone()
            popped = self._history.pop()

            # Add to redo stack
            self._redo_stack.append(popped)

            logger.info(
                f"Undid transition {popped.record_id}: "
                f"{current_scene.scene_id} -> {previous_scene.scene_id}"
            )

            return UndoRedoResult(
                success=True,
                action="undo",
                previous_scene=current_scene.scene_id,
                new_scene=previous_scene.scene_id,
                transition_type=record.transition_type,
                record_id=record.record_id
            )

        except Exception as e:
            logger.error(f"Undo failed: {e}")
            return UndoRedoResult(
                success=False,
                action="undo",
                previous_scene=current_scene.scene_id,
                new_scene=previous_scene.scene_id,
                error=str(e)
            )

    def redo(
        self,
        current_scene: SceneManager,
        target_scene: SceneManager
    ) -> UndoRedoResult:
        """
        Redo the last undone transition.

        Args:
            current_scene: Current active scene
            target_scene: Scene to transition to

        Returns:
            UndoRedoResult
        """
        if not self._redo_stack:
            return UndoRedoResult(
                success=False,
                action="redo",
                previous_scene=current_scene.scene_id,
                new_scene=target_scene.scene_id,
                error="Nothing to redo"
            )

        record = self._redo_stack.pop()

        try:
            # Perform redo by activating target scene
            if target_scene.state != SceneState.ACTIVE:
                target_scene.activate()

            # Complete current scene
            if current_scene.state == SceneState.ACTIVE:
                current_scene.complete("Transition redone")

            # Re-record in history
            new_record = TransitionRecord(
                source_scene_id=record.source_scene_id,
                target_scene_id=record.target_scene_id,
                transition_type=record.transition_type,
                metadata=record.metadata
            )

            self._history.push(new_record)

            logger.info(
                f"Redid transition {record.record_id}: "
                f"{current_scene.scene_id} -> {target_scene.scene_id}"
            )

            return UndoRedoResult(
                success=True,
                action="redo",
                previous_scene=current_scene.scene_id,
                new_scene=target_scene.scene_id,
                transition_type=record.transition_type,
                record_id=new_record.record_id
            )

        except Exception as e:
            logger.error(f"Redo failed: {e}")

            # Put back on redo stack
            self._redo_stack.append(record)

            return UndoRedoResult(
                success=False,
                action="redo",
                previous_scene=current_scene.scene_id,
                new_scene=target_scene.scene_id,
                error=str(e)
            )

    def _add_to_redo(self, record: TransitionRecord) -> None:
        """
        Add record to redo stack (internal).

        Args:
            record: Record to add
        """
        self._redo_stack.append(record)

    def can_undo(self) -> bool:
        """
        Check if undo is possible.

        Returns:
            True if undo available
        """
        return not self._history.is_empty

    def can_redo(self) -> bool:
        """
        Check if redo is possible.

        Returns:
            True if redo available
        """
        return len(self._redo_stack) > 0

    def get_history_count(self) -> int:
        """
        Get history size.

        Returns:
            Number of records in history
        """
        return self._history.size

    def get_redo_count(self) -> int:
        """
        Get redo stack size.

        Returns:
            Number of records in redo stack
        """
        return len(self._redo_stack)

    def get_history(self) -> List[TransitionRecord]:
        """
        Get all history records.

        Returns:
            List of records
        """
        return self._history.get_records()

    def clear_history(self) -> None:
        """Clear all history and redo stack."""
        self._history.clear()
        self._redo_stack.clear()

        logger.info("UndoRedoManager history cleared")

    def get_undo_preview(self) -> Optional[Dict[str, Any]]:
        """
        Preview what undo would do.

        Returns:
            Preview dict or None if no undo available
        """
        record = self._history.peek()
        if not record:
            return None

        return {
            "action": "undo",
            "current_scene": record.target_scene_id,
            "would_revert_to": record.source_scene_id,
            "transition_type": record.transition_type.value,
            "timestamp": record.timestamp.isoformat()
        }

    def get_redo_preview(self) -> Optional[Dict[str, Any]]:
        """
        Preview what redo would do.

        Returns:
            Preview dict or None if no redo available
        """
        if not self._redo_stack:
            return None

        record = self._redo_stack[-1]

        return {
            "action": "redo",
            "current_scene": record.source_scene_id,
            "would_transition_to": record.target_scene_id,
            "transition_type": record.transition_type.value,
            "timestamp": record.timestamp.isoformat()
        }

    def export_history(self) -> List[Dict[str, Any]]:
        """
        Export history as list of dicts.

        Returns:
            List of record dictionaries
        """
        return [record.to_dict() for record in self._history.get_records()]

    def import_history(self, records: List[Dict[str, Any]]) -> int:
        """
        Import history from list of dicts.

        Args:
            records: List of record dictionaries

        Returns:
            Number of records imported
        """
        count = 0
        for record_data in records:
            try:
                record = TransitionRecord.from_dict(record_data)
                self._history.push(record)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to import record: {e}")

        logger.info(f"Imported {count} history records")
        return count
