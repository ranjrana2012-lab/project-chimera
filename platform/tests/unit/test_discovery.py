"""Test discovery module."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from orchestrator.discovery import TestDiscovery, DAG, TestSpec

@pytest.mark.asyncio
async def test_discover_tests_finds_pytest_tests():
    """Test discovery finds all pytest tests in services directory."""
    discovery = TestDiscovery()
    tests = await discovery.discover_tests("tests/")

    assert len(tests) > 0  # Should find existing tests
    assert all(hasattr(t, "test_id") for t in tests)
    assert all(hasattr(t, "file_path") for t in tests)

@pytest.mark.asyncio
async def test_build_dependency_graph_creates_dag():
    """Test dependency graph is a valid DAG."""
    discovery = TestDiscovery()
    tests = await discovery.discover_tests("tests/")
    dag = await discovery.build_dependency_graph(tests)

    assert isinstance(dag, DAG)
    assert not dag.has_cycles()  # Must be acyclic

def test_dag_detects_cycles():
    """Test DAG can detect cycles."""
    dag = DAG()
    dag.add_node("a", ["b"])
    dag.add_node("b", ["c"])
    dag.add_node("c", ["a"])  # Creates cycle: a -> b -> c -> a

    assert dag.has_cycles() is True

def test_dag_no_cycles():
    """Test DAG validates acyclic graph."""
    dag = DAG()
    dag.add_node("a", ["b"])
    dag.add_node("b", ["c"])
    dag.add_node("c", [])  # No cycle

    assert dag.has_cycles() is False

def test_test_spec_model():
    """Test TestSpec model validation."""
    spec = TestSpec(
        test_id="tests/example.py::test_function",
        file_path="tests/example.py",
        test_function="test_function",
        markers=["unit", "fast"],
        estimated_duration=1.0,
        dependencies=[]
    )

    assert spec.test_id == "tests/example.py::test_function"
    assert spec.file_path == "tests/example.py"
    assert spec.test_function == "test_function"
    assert len(spec.markers) == 2
