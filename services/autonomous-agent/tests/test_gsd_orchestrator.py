"""Tests for GSD Orchestrator."""

import pytest
from datetime import datetime
from gsd_orchestrator import (
    GSDOrchestrator,
    Requirements,
    Task,
    Plan,
    Result,
    Results,
    PlanRejectedError,
    SpecViolationError,
    QualityViolationError,
)


@pytest.fixture
def orchestrator():
    """Create a GSD Orchestrator instance."""
    return GSDOrchestrator()


def test_gsd_orchestrator_initialization(orchestrator):
    """Test that GSD Orchestrator initializes correctly."""
    assert orchestrator is not None
    assert hasattr(orchestrator, 'discuss_phase')
    assert hasattr(orchestrator, 'plan_phase')
    assert hasattr(orchestrator, 'execute_phase')


def test_requirements_creation(orchestrator):
    """Test requirements creation dataclass."""
    requirements = Requirements(
        goal="Build a REST API",
        constraints=["Python", "FastAPI"],
        acceptance_criteria=["API must respond within 100ms"]
    )

    assert requirements.goal == "Build a REST API"
    assert len(requirements.constraints) == 2
    assert len(requirements.acceptance_criteria) == 1


def test_plan_creation(orchestrator):
    """Test plan creation dataclass."""
    task1 = Task(
        id="1",
        description="Set up project structure",
        dependencies=[]
    )
    task2 = Task(
        id="2",
        description="Implement endpoints",
        dependencies=["1"]
    )

    plan = Plan(
        tasks=[task1, task2],
        estimated_hours=4
    )

    assert len(plan.tasks) == 2
    assert plan.estimated_hours == 4
    assert plan.tasks[1].dependencies == ["1"]


def test_write_and_read_requirements(orchestrator, tmp_path):
    """Test writing and reading requirements to file."""
    requirements = Requirements(
        goal="Build a REST API",
        constraints=["Python", "FastAPI"],
        acceptance_criteria=["API must respond within 100ms"]
    )

    # Write requirements
    req_file = tmp_path / "REQUIREMENTS.md"
    orchestrator.write_requirements(requirements, str(req_file))

    # Verify file exists
    assert req_file.exists()

    # Read and verify content
    content = req_file.read_text()
    assert "Build a REST API" in content
    assert "Python" in content
    assert "FastAPI" in content
    assert "API must respond within 100ms" in content


def test_write_and_read_plan(orchestrator, tmp_path):
    """Test writing and reading plan to file."""
    task1 = Task(
        id="1",
        description="Set up project structure",
        dependencies=[]
    )
    task2 = Task(
        id="2",
        description="Implement endpoints",
        dependencies=["1"]
    )

    plan = Plan(
        tasks=[task1, task2],
        estimated_hours=4
    )

    # Write plan
    plan_file = tmp_path / "PLAN.md"
    orchestrator.write_plan(plan, str(plan_file))

    # Verify file exists
    assert plan_file.exists()

    # Read and verify content
    content = plan_file.read_text()
    assert "Set up project structure" in content
    assert "Implement endpoints" in content
    assert "4" in content  # estimated hours
