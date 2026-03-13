"""Flow-Next Manager - Fresh context per iteration."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import tempfile


@dataclass
class Session:
    """A fresh session with only external state (no history)."""

    state: str
    plan: str
    requirements: str
    history: list = field(default_factory=list)


class FlowNextManager:
    """Fresh context per iteration to prevent context rot."""

    def __init__(self, state_dir: Path = Path("state")):
        self.state_dir = state_dir
        self.state_file = state_dir / "STATE.md"
        self.plan_file = state_dir / "PLAN.md"
        self.requirements_file = state_dir / "REQUIREMENTS.md"

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def create_fresh_session(self) -> Session:
        """Create new session with only external state (no history)."""
        return Session(
            state=self.read_state(),
            plan=self.read_plan(),
            requirements=self.read_requirements(),
            history=[]  # Empty history - fresh start
        )

    def save_and_reset(self, session: Session) -> None:
        """Save state and destroy session (amnesia)."""
        # Update external state
        self.write_state(session.state)
        self.write_plan(session.plan)
        self.write_requirements(session.requirements)

        # Session is discarded - next iteration starts fresh
        # (Python GC handles cleanup)

    def read_state(self) -> str:
        """Read current state from file."""
        if self.state_file.exists():
            return self.state_file.read_text()
        return "# Current State\n\nNo state yet."

    def read_plan(self) -> str:
        """Read current plan from file."""
        if self.plan_file.exists():
            return self.plan_file.read_text()
        return "# Plan\n\nNo plan yet."

    def read_requirements(self) -> str:
        """Read current requirements from file."""
        if self.requirements_file.exists():
            return self.requirements_file.read_text()
        return "# Requirements\n\nNo requirements yet."

    def write_state(self, content: str) -> None:
        """Write state to file."""
        self.state_file.write_text(content)

    def write_plan(self, content: str) -> None:
        """Write plan to file."""
        self.plan_file.write_text(content)

    def write_requirements(self, content: str) -> None:
        """Write requirements to file."""
        self.requirements_file.write_text(content)
