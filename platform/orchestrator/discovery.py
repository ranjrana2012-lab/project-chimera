"""Test discovery for pytest-based test suites."""
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class TestSpec(BaseModel):
    """Specification for a single test."""
    test_id: str
    file_path: str
    test_class: Optional[str] = None
    test_function: str
    markers: List[str] = Field(default_factory=list)
    estimated_duration: float = 1.0
    dependencies: List[str] = Field(default_factory=list)


class DAG:
    """Directed Acyclic Graph for test dependencies."""

    def __init__(self):
        self.nodes: dict[str, list[str]] = {}

    def add_node(self, test_id: str, dependencies: List[str]):
        """Add a node with its dependencies."""
        self.nodes[test_id] = dependencies

    def has_cycles(self) -> bool:
        """Check if DAG has cycles (returns True if cycle exists)."""
        visited = set()
        rec_stack = set()

        def visit(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in self.nodes.get(node, []):
                if dep not in visited:
                    if visit(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if visit(node):
                    return True
        return False


class TestDiscovery:
    """Discover tests in the codebase using pytest collection."""

    async def discover_tests(self, path: str) -> List[TestSpec]:
        """Discover all tests in the given path."""
        # Convert to absolute path to avoid confusion with parent pytest.ini
        abs_path = str(Path(path).resolve())

        # Use pytest --collect-only to get test data
        # Use -c /dev/null to avoid picking up parent pytest.ini
        # Use -q for quieter output that shows test_id::test_func format
        proc = await asyncio.create_subprocess_exec(
            "pytest",
            "--collect-only",
            "-q",
            "-c",
            "/dev/null",
            abs_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()

        # Parse pytest output
        tests = []
        for line in stdout.decode().split("\n"):
            line = line.strip()
            # Handle format: "tests/file.py::test_func" or "file.py::TestClass::test_func"
            if "::test_" in line:
                test_spec = self._parse_pytest_line(line)
                if test_spec:
                    tests.append(test_spec)

        return tests

    def _parse_pytest_line(self, line: str) -> Optional[TestSpec]:
        """Parse a pytest collection line into TestSpec."""
        try:
            line = line.strip()

            # Handle format: "tests/file.py::TestClass::test_func"
            if "::" in line and not line.startswith("<"):
                parts = line.split("::")
                file_path = parts[0]

                test_class = None
                test_function = None

                for part in parts[1:]:
                    if part.startswith("Test") and part[0].isupper():
                        test_class = part
                    elif part.startswith("test_"):
                        test_function = part

                return TestSpec(
                    test_id=line,
                    file_path=file_path,
                    test_class=test_class,
                    test_function=test_function or test_class or "test",
                    markers=[],
                    dependencies=[]
                )

            # Handle format: "<Function test_func>" inside a class context
            # We need to track context, but for now skip these as they'll be
            # captured by the :: format above
            return None

        except Exception:
            return None

    async def build_dependency_graph(self, tests: List[TestSpec]) -> DAG:
        """Build dependency DAG from test dependencies."""
        dag = DAG()

        for test in tests:
            dag.add_node(test.test_id, test.dependencies)

        return dag
