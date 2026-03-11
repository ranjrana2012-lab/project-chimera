"""
Show state manager for Project Chimera.

Manages show lifecycle (start, end, state) and WebSocket connections
for real-time show updates.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ShowState(str, Enum):
    """Show state enumeration."""
    IDLE = "idle"
    ACTIVE = "active"
    ENDED = "ended"
    PAUSED = "paused"


class Show:
    """Represents a Project Chimera show."""

    def __init__(self, show_id: str):
        """Initialize a new show.

        Args:
            show_id: Unique show identifier
        """
        self.show_id = show_id
        self.state = ShowState.IDLE
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.scene = 0
        self.current_scene = "none"  # For E2E test compatibility
        self.audience_metrics = {
            "total_reactions": 0,
            "sentiment_score": 0.5
        }
        self.metadata: Dict[str, Any] = {}

    def start(self) -> None:
        """Start the show."""
        self.state = ShowState.ACTIVE
        self.started_at = datetime.now()

    def end(self) -> None:
        """End the show."""
        self.state = ShowState.ENDED
        self.ended_at = datetime.now()

    def pause(self) -> None:
        """Pause the show."""
        self.state = ShowState.PAUSED

    def resume(self) -> None:
        """Resume the show."""
        self.state = ShowState.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert show to dictionary.

        Returns:
            Dictionary representation of show
        """
        return {
            "show_id": self.show_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "scene": self.scene,
            "metadata": self.metadata
        }


class ShowManager:
    """Manages active shows and WebSocket connections."""

    def __init__(self):
        """Initialize the show manager."""
        # Current show (single show for now)
        self.current_show: Optional[Show] = None

        # WebSocket connections
        self.active_connections: Dict[str, Set[str]] = {}
        # Map: show_id -> set of connection_ids

    def create_show(self, show_id: str) -> Show:
        """Create a new show.

        Args:
            show_id: Unique show identifier

        Returns:
            Created show
        """
        self.current_show = Show(show_id)
        self.active_connections[show_id] = set()
        logger.info(f"Created show: {show_id}")
        return self.current_show

    def get_show(self, show_id: str) -> Optional[Show]:
        """Get a show by ID.

        Args:
            show_id: Show identifier

        Returns:
            Show if found, None otherwise
        """
        if self.current_show and self.current_show.show_id == show_id:
            return self.current_show
        return None

    def get_current_show(self) -> Optional[Show]:
        """Get the current show.

        Returns:
            Current show if exists, None otherwise
        """
        return self.current_show

    def start_show(self, show_id: str) -> Optional[Show]:
        """Start a show.

        Args:
            show_id: Show identifier

        Returns:
            Started show if found, None otherwise
        """
        show = self.get_show(show_id)
        if show:
            show.start()
            logger.info(f"Started show: {show_id}")
        return show

    def end_show(self, show_id: str) -> Optional[Show]:
        """End a show.

        Args:
            show_id: Show identifier

        Returns:
            Ended show if found, None otherwise
        """
        show = self.get_show(show_id)
        if show:
            show.end()
            logger.info(f"Ended show: {show_id}")
        return show

    def add_connection(self, show_id: str, connection_id: str) -> bool:
        """Add a WebSocket connection to a show.

        Args:
            show_id: Show identifier
            connection_id: Connection identifier

        Returns:
            True if added, False if show not found
        """
        if show_id not in self.active_connections:
            return False
        self.active_connections[show_id].add(connection_id)
        logger.debug(f"Added connection {connection_id} to show {show_id}")
        return True

    def remove_connection(self, show_id: str, connection_id: str) -> None:
        """Remove a WebSocket connection from a show.

        Args:
            show_id: Show identifier
            connection_id: Connection identifier
        """
        if show_id in self.active_connections:
            self.active_connections[show_id].discard(connection_id)
            logger.debug(f"Removed connection {connection_id} from show {show_id}")


# Global show manager instance
show_manager = ShowManager()


__all__ = [
    "ShowState",
    "Show",
    "ShowManager",
    "show_manager",
]
