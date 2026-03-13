"""Tests for Flow-Next Manager."""

import pytest
from flow_next import FlowNextManager, Session


@pytest.fixture
def manager(tmp_path):
    """Create a FlowNextManager instance for testing."""
    return FlowNextManager(state_dir=tmp_path)


def test_flow_next_manager_initialization(manager, tmp_path):
    """Test FlowNextManager initializes correctly."""
    assert manager.state_dir == tmp_path
    assert manager.state_file.name == "STATE.md"
    assert manager.plan_file.name == "PLAN.md"
    assert manager.requirements_file.name == "REQUIREMENTS.md"


def test_create_fresh_session(manager):
    """Test creating a fresh session with no history."""
    session = manager.create_fresh_session()

    assert session.history == []
    assert session.state is not None
    assert session.plan is not None
    assert session.requirements is not None


def test_save_and_reset(manager, tmp_path):
    """Test saving state and resetting session."""
    import tempfile
    import os

    # Create session with modified state
    session = Session(
        state="Updated state",
        plan="Updated plan",
        requirements="Updated requirements",
        history=[]
    )

    # Save state
    manager.save_and_reset(session)

    # Verify files were created
    assert (tmp_path / "STATE.md").exists()
    assert (tmp_path / "PLAN.md").exists()
    assert (tmp_path / "REQUIREMENTS.md").exists()

    # Verify content
    assert (tmp_path / "STATE.md").read_text() == "Updated state"
    assert (tmp_path / "PLAN.md").read_text() == "Updated plan"
    assert (tmp_path / "REQUIREMENTS.md").read_text() == "Updated requirements"


def test_read_state_files(manager, tmp_path):
    """Test reading state files."""
    # Create test state files
    (tmp_path / "STATE.md").write_text("# State\n\nCurrent progress")
    (tmp_path / "PLAN.md").write_text("# Plan\n\nImplementation plan")
    (tmp_path / "REQUIREMENTS.md").write_text("# Requirements\n\nRequirements list")

    # Read state
    state = manager.read_state()
    plan = manager.read_plan()
    requirements = manager.read_requirements()

    assert "Current progress" in state
    assert "Implementation plan" in plan
    assert "Requirements list" in requirements
