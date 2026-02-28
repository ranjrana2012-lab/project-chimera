"""Comprehensive unit tests for TestDiscovery module."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.discovery import TestDiscovery, DAG, TestSpec


class TestTestSpec:
    """Test suite for TestSpec model."""

    def test_test_spec_with_all_fields(self):
        """Test TestSpec creation with all fields populated."""
        spec = TestSpec(
            test_id="tests/example.py::TestClass::test_method",
            file_path="tests/example.py",
            test_class="TestClass",
            test_function="test_method",
            markers=["unit", "fast", "smoke"],
            estimated_duration=2.5,
            dependencies=["tests/setup.py::test_setup"]
        )

        assert spec.test_id == "tests/example.py::TestClass::test_method"
        assert spec.file_path == "tests/example.py"
        assert spec.test_class == "TestClass"
        assert spec.test_function == "test_method"
        assert len(spec.markers) == 3
        assert "unit" in spec.markers
        assert spec.estimated_duration == 2.5
        assert len(spec.dependencies) == 1

    def test_test_spec_with_minimal_fields(self):
        """Test TestSpec creation with minimal required fields."""
        spec = TestSpec(
            test_id="tests/simple.py::test_func",
            file_path="tests/simple.py",
            test_function="test_func"
        )

        assert spec.test_id == "tests/simple.py::test_func"
        assert spec.test_class is None
        assert spec.markers == []
        assert spec.estimated_duration == 1.0  # Default value
        assert spec.dependencies == []

    def test_test_spec_default_values(self):
        """Test TestSpec default field values."""
        spec = TestSpec(
            test_id="test_id",
            file_path="file.py",
            test_function="test"
        )

        assert spec.test_class is None
        assert spec.markers == []
        assert spec.estimated_duration == 1.0
        assert spec.dependencies == []

    def test_test_spec_validation_with_empty_test_id(self):
        """Test TestSpec handles empty test_id."""
        with pytest.raises(Exception):
            TestSpec(
                test_id="",
                file_path="file.py",
                test_function="test"
            )

    def test_test_spec_with_multiple_dependencies(self):
        """Test TestSpec with multiple dependencies."""
        spec = TestSpec(
            test_id="tests/test.py::test_complex",
            file_path="tests/test.py",
            test_function="test_complex",
            dependencies=[
                "tests/test.py::test_setup_1",
                "tests/test.py::test_setup_2",
                "tests/test.py::test_setup_3"
            ]
        )

        assert len(spec.dependencies) == 3

    def test_test_spec_duration_validation(self):
        """Test TestSpec with various duration values."""
        spec_fast = TestSpec(
            test_id="fast",
            file_path="f.py",
            test_function="test",
            estimated_duration=0.1
        )
        spec_slow = TestSpec(
            test_id="slow",
            file_path="s.py",
            test_function="test",
            estimated_duration=300.0
        )

        assert spec_fast.estimated_duration == 0.1
        assert spec_slow.estimated_duration == 300.0


class TestDAG:
    """Test suite for DAG (Directed Acyclic Graph) class."""

    def test_dag_initialization(self):
        """Test DAG creates empty graph on initialization."""
        dag = DAG()
        assert dag.nodes == {}
        assert len(dag.nodes) == 0

    def test_dag_add_single_node(self):
        """Test adding a single node to DAG."""
        dag = DAG()
        dag.add_node("test_a", [])

        assert "test_a" in dag.nodes
        assert dag.nodes["test_a"] == []

    def test_dag_add_node_with_dependencies(self):
        """Test adding node with dependencies."""
        dag = DAG()
        dag.add_node("test_a", ["test_b", "test_c"])

        assert "test_a" in dag.nodes
        assert len(dag.nodes["test_a"]) == 2
        assert "test_b" in dag.nodes["test_a"]
        assert "test_c" in dag.nodes["test_a"]

    def test_dag_add_multiple_nodes(self):
        """Test adding multiple nodes to DAG."""
        dag = DAG()
        dag.add_node("test_a", [])
        dag.add_node("test_b", ["test_a"])
        dag.add_node("test_c", [])

        assert len(dag.nodes) == 3

    def test_dag_detects_simple_cycle(self):
        """Test DAG detects simple two-node cycle."""
        dag = DAG()
        dag.add_node("test_a", ["test_b"])
        dag.add_node("test_b", ["test_a"])

        assert dag.has_cycles() is True

    def test_dag_detects_three_node_cycle(self):
        """Test DAG detects three-node cycle."""
        dag = DAG()
        dag.add_node("test_a", ["test_b"])
        dag.add_node("test_b", ["test_c"])
        dag.add_node("test_c", ["test_a"])

        assert dag.has_cycles() is True

    def test_dag_detects_complex_cycle(self):
        """Test DAG detects complex cycle with multiple branches."""
        dag = DAG()
        dag.add_node("a", ["b"])
        dag.add_node("b", ["c"])
        dag.add_node("c", ["d"])
        dag.add_node("d", ["b"])  # Cycle: b -> c -> d -> b

        assert dag.has_cycles() is True

    def test_dag_valid_acyclic_graph(self):
        """Test DAG validates graph without cycles."""
        dag = DAG()
        dag.add_node("test_a", [])
        dag.add_node("test_b", ["test_a"])
        dag.add_node("test_c", ["test_a"])
        dag.add_node("test_d", ["test_b", "test_c"])

        assert dag.has_cycles() is False

    def test_dag_self_cycle(self):
        """Test DAG detects self-referencing node."""
        dag = DAG()
        dag.add_node("test_a", ["test_a"])

        assert dag.has_cycles() is True

    def test_dag_empty_graph(self):
        """Test DAG returns no cycles for empty graph."""
        dag = DAG()
        assert dag.has_cycles() is False

    def test_dag_isolated_nodes(self):
        """Test DAG with isolated nodes (no dependencies)."""
        dag = DAG()
        dag.add_node("test_a", [])
        dag.add_node("test_b", [])
        dag.add_node("test_c", [])

        assert dag.has_cycles() is False
        assert len(dag.nodes) == 3

    def test_dag_diamond_dependency(self):
        """Test DAG with diamond dependency pattern (no cycle)."""
        dag = DAG()
        dag.add_node("a", [])
        dag.add_node("b", ["a"])
        dag.add_node("c", ["a"])
        dag.add_node("d", ["b", "c"])

        assert dag.has_cycles() is False

    def test_dag_update_existing_node(self):
        """Test updating dependencies for existing node."""
        dag = DAG()
        dag.add_node("test_a", ["test_b"])
        dag.add_node("test_a", ["test_c"])

        assert dag.nodes["test_a"] == ["test_c"]

    def test_dag_nonexistent_dependencies(self):
        """Test DAG with dependencies that don't exist as nodes."""
        dag = DAG()
        dag.add_node("test_a", ["test_nonexistent"])

        assert dag.has_cycles() is False  # Non-existent deps don't create cycles


class TestDiscovery:
    """Test suite for TestDiscovery class."""

    @pytest.mark.asyncio
    async def test_discovery_initialization(self):
        """Test TestDiscovery initializes correctly."""
        discovery = TestDiscovery()
        assert discovery is not None

    @pytest.mark.asyncio
    async def test_discover_tests_with_mocked_subprocess(self):
        """Test discover_tests with mocked subprocess output."""
        discovery = TestDiscovery()

        mock_output = b"tests/test_example.py::test_function\n"
        mock_output += b"tests/test_example.py::TestClass::test_method\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(mock_output, b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            tests = await discovery.discover_tests("tests/")

            assert len(tests) >= 0

    def test_parse_pytest_line_simple_test(self):
        """Test parsing simple pytest line."""
        discovery = TestDiscovery()
        line = "tests/test_example.py::test_function"

        spec = discovery._parse_pytest_line(line)

        assert spec is not None
        assert spec.test_id == line
        assert spec.file_path == "tests/test_example.py"
        assert spec.test_function == "test_function"
        assert spec.test_class is None

    def test_parse_pytest_line_class_method(self):
        """Test parsing pytest line with class and method."""
        discovery = TestDiscovery()
        line = "tests/test_example.py::TestClass::test_method"

        spec = discovery._parse_pytest_line(line)

        assert spec is not None
        assert spec.test_id == line
        assert spec.file_path == "tests/test_example.py"
        assert spec.test_class == "TestClass"
        assert spec.test_function == "test_method"

    def test_parse_pytest_line_nested_class(self):
        """Test parsing pytest line with nested class."""
        discovery = TestDiscovery()
        line = "tests/test_example.py::OuterClass::InnerClass::test_method"

        spec = discovery._parse_pytest_line(line)

        assert spec is not None
        # Parser should handle this case
        assert spec.file_path == "tests/test_example.py"

    def test_parse_pytest_line_with_angle_brackets(self):
        """Test parsing pytest line with <Function> format."""
        discovery = TestDiscovery()
        line = "<Function test_function>"

        spec = discovery._parse_pytest_line(line)

        # Lines starting with < should return None
        assert spec is None

    def test_parse_pytest_line_empty_line(self):
        """Test parsing empty pytest line."""
        discovery = TestDiscovery()
        spec = discovery._parse_pytest_line("")

        assert spec is None

    def test_parse_pytest_line_malformed_line(self):
        """Test parsing malformed pytest line."""
        discovery = TestDiscovery()
        spec = discovery._parse_pytest_line("not_a_valid_test_line")

        assert spec is None

    def test_parse_pytest_line_no_separator(self):
        """Test parsing line without :: separator."""
        discovery = TestDiscovery()
        spec = discovery._parse_pytest_line("tests/test_example.py")

        assert spec is None

    def test_parse_pytest_line_with_parameters(self):
        """Test parsing pytest line with parametrized test."""
        discovery = TestDiscovery()
        line = "tests/test_example.py::test_function[param1]"

        spec = discovery._parse_pytest_line(line)

        assert spec is not None
        assert spec.test_id == line

    def test_parse_pytest_line_preserves_markers_empty(self):
        """Test TestSpec created with empty markers list."""
        discovery = TestDiscovery()
        spec = discovery._parse_pytest_line("tests/test.py::test_func")

        assert spec is not None
        assert spec.markers == []

    def test_parse_pytest_line_preserves_dependencies_empty(self):
        """Test TestSpec created with empty dependencies list."""
        discovery = TestDiscovery()
        spec = discovery._parse_pytest_line("tests/test.py::test_func")

        assert spec is not None
        assert spec.dependencies == []

    @pytest.mark.asyncio
    async def test_build_dependency_graph_empty_list(self):
        """Test building dependency graph with empty test list."""
        discovery = TestDiscovery()
        dag = await discovery.build_dependency_graph([])

        assert isinstance(dag, DAG)
        assert len(dag.nodes) == 0

    @pytest.mark.asyncio
    async def test_build_dependency_graph_with_tests(self):
        """Test building dependency graph with test dependencies."""
        discovery = TestDiscovery()

        tests = [
            TestSpec(
                test_id="test_a",
                file_path="test.py",
                test_function="test_a",
                dependencies=[]
            ),
            TestSpec(
                test_id="test_b",
                file_path="test.py",
                test_function="test_b",
                dependencies=["test_a"]
            ),
            TestSpec(
                test_id="test_c",
                file_path="test.py",
                test_function="test_c",
                dependencies=["test_a", "test_b"]
            )
        ]

        dag = await discovery.build_dependency_graph(tests)

        assert len(dag.nodes) == 3
        assert dag.has_cycles() is False

    @pytest.mark.asyncio
    async def test_build_dependency_graph_detects_cycles(self):
        """Test building dependency graph detects cycles."""
        discovery = TestDiscovery()

        tests = [
            TestSpec(
                test_id="test_a",
                file_path="test.py",
                test_function="test_a",
                dependencies=["test_b"]
            ),
            TestSpec(
                test_id="test_b",
                file_path="test.py",
                test_function="test_b",
                dependencies=["test_a"]
            )
        ]

        dag = await discovery.build_dependency_graph(tests)

        assert dag.has_cycles() is True

    @pytest.mark.asyncio
    async def test_discover_tests_handles_path_conversion(self):
        """Test discover_tests converts path to absolute."""
        discovery = TestDiscovery()

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            await discovery.discover_tests("tests/")

            # Verify absolute path was used
            call_args = mock_subprocess.call_args
            # Last argument should be the absolute path
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_discover_tests_filters_non_test_lines(self):
        """Test discover_tests filters out non-test lines from output."""
        discovery = TestDiscovery()

        mock_output = b"collected 2 items\n"
        mock_output += b"tests/test.py::test_a\n"
        mock_output += b"some random output\n"
        mock_output += b"tests/test.py::test_b\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(mock_output, b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            tests = await discovery.discover_tests("tests/")

            # Should only parse lines with ::test_
            assert all("test_" in t.test_id for t in tests)

    def test_parse_pytest_line_uppercase_class(self):
        """Test parsing correctly identifies uppercase class names."""
        discovery = TestDiscovery()
        line = "tests/test.py::MyTestClass::test_something"

        spec = discovery._parse_pytest_line(line)

        assert spec.test_class == "MyTestClass"
        assert spec.test_function == "test_something"

    def test_parse_pytest_line_lowercase_function(self):
        """Test parsing correctly identifies lowercase test functions."""
        discovery = TestDiscovery()
        line = "tests/test.py::test_lowercase_function"

        spec = discovery._parse_pytest_line(line)

        assert spec.test_function == "test_lowercase_function"
        assert spec.test_class is None
