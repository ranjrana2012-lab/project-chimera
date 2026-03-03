"""
Test Discovery - OpenClaw Test Orchestrator

Discovers and catalogs pytest tests across all services.
"""

import os
import ast
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)


@dataclass
class TestInfo:
    """
    Represents a single discovered test.

    Attributes:
        name: Test function name
        file_path: Path to test file
        test_type: Type of test (unit, integration, e2e)
        service: Service name
        line_number: Line number of test definition
        markers: Pytest markers on the test
    """
    name: str
    file_path: str
    test_type: str = "unit"
    service: str = ""
    line_number: int = 0
    markers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "test_type": self.test_type,
            "service": self.service,
            "line_number": self.line_number,
            "markers": self.markers
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestInfo":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            file_path=data["file_path"],
            test_type=data.get("test_type", "unit"),
            service=data.get("service", ""),
            line_number=data.get("line_number", 0),
            markers=data.get("markers", [])
        )


@dataclass
class ServiceTests:
    """
    Represents all tests in a service.

    Attributes:
        service: Service name
        test_files: List of test file paths
        tests: List of TestInfo objects
        total_count: Total number of tests
        by_type: Count of tests by type
    """
    service: str
    test_files: List[str] = field(default_factory=list)
    tests: List[TestInfo] = field(default_factory=list)
    total_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived fields."""
        self.total_count = len(self.tests)
        self.by_type = {}
        for test in self.tests:
            self.by_type[test.test_type] = self.by_type.get(test.test_type, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "test_files": self.test_files,
            "tests": [t.to_dict() for t in self.tests],
            "total_count": self.total_count,
            "by_type": self.by_type
        }


@dataclass
class TestCatalog:
    """
    Catalog of all discovered tests.

    Attributes:
        services: Dictionary of service name to ServiceTests
        total_tests: Total number of tests across all services
        discovered_at: Timestamp of discovery
        discovery_duration: Time taken to discover tests (seconds)
    """
    services: Dict[str, ServiceTests] = field(default_factory=dict)
    total_tests: int = 0
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    discovery_duration: float = 0.0

    def __post_init__(self):
        """Calculate total tests."""
        self._recalculate_total()

    def _recalculate_total(self):
        """Recalculate total tests from services."""
        self.total_tests = sum(s.total_count for s in self.services.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "services": {
                name: service.to_dict()
                for name, service in self.services.items()
            },
            "total_tests": self.total_tests,
            "discovered_at": self.discovered_at,
            "discovery_duration": self.discovery_duration
        }


class TestDiscovery:
    """
    Discovers and catalogs pytest tests across services.

    Uses AST parsing to find test functions without executing them.
    """

    DEFAULT_PATTERNS = ["test_*.py", "*_test.py"]
    DEFAULT_SERVICES_PATH = "services"

    def __init__(
        self,
        services_path: str = DEFAULT_SERVICES_PATH,
        test_patterns: Optional[List[str]] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300
    ):
        """
        Initialize test discovery.

        Args:
            services_path: Path to services directory
            test_patterns: Glob patterns for test files
            enable_cache: Enable caching of discovery results
            cache_ttl: Cache TTL in seconds
        """
        self.services_path = Path(services_path)
        self.test_patterns = test_patterns or self.DEFAULT_PATTERNS
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl

        self._cache: Optional[TestCatalog] = None
        self._cache_timestamp: Optional[float] = None

        logger.info(
            f"TestDiscovery initialized (services_path={services_path}, "
            f"patterns={test_patterns})"
        )

    def discover_services(self) -> List[str]:
        """
        Discover all services with test directories.

        Returns:
            List of service names
        """
        services = []

        if not self.services_path.exists():
            logger.warning(f"Services path does not exist: {self.services_path}")
            return services

        for service_dir in self.services_path.iterdir():
            if not service_dir.is_dir():
                continue

            # Skip hidden directories and venv
            if service_dir.name.startswith(".") or "venv" in service_dir.name:
                continue

            # Check for tests directory
            tests_dir = service_dir / "tests"
            if tests_dir.exists() and tests_dir.is_dir():
                services.append(service_dir.name)

        logger.info(f"Discovered {len(services)} services with tests")
        return services

    def discover_test_files(self, service: str) -> List[str]:
        """
        Discover all test files in a service.

        Args:
            service: Service name

        Returns:
            List of test file paths (relative to service root)
        """
        test_files = []
        service_path = self.services_path / service / "tests"

        if not service_path.exists():
            return test_files

        for pattern in self.test_patterns:
            for test_file in service_path.rglob(pattern):
                # Skip __pycache__ and .pytest_cache
                if any(p.startswith(".") or p == "__pycache__"
                       for p in test_file.parts):
                    continue

                # Get relative path from service root
                rel_path = str(test_file.relative_to(self.services_path / service))
                test_files.append(rel_path)

        # Remove duplicates and sort
        test_files = sorted(set(test_files))

        logger.debug(f"Found {len(test_files)} test files in {service}")
        return test_files

    def collect_tests_from_file(self, file_path: str, service: str) -> List[TestInfo]:
        """
        Collect tests from a single file using AST parsing.

        Args:
            file_path: Path to test file
            service: Service name

        Returns:
            List of TestInfo objects
        """
        tests = []
        full_path = self.services_path / service / file_path

        if not full_path.exists():
            logger.warning(f"Test file does not exist: {full_path}")
            return tests

        try:
            with open(full_path, "r") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(full_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        # Get line number
                        line_number = node.lineno or 0

                        # Check for decorators (markers)
                        markers = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                markers.append(decorator.id)
                            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                                if decorator.func.attr == "mark":
                                    # Extract marker name: @pytest.mark.integration
                                    if isinstance(decorator.func.value, ast.Attribute):
                                        markers.append(decorator.func.value.attr)

                        # Create test info
                        test_type = self.categorize_test_by_name(node.name)
                        if not test_type:
                            test_type = self.categorize_test_by_markers(markers)

                        test_info = TestInfo(
                            name=node.name,
                            file_path=file_path,
                            test_type=test_type,
                            service=service,
                            line_number=line_number,
                            markers=markers
                        )
                        tests.append(test_info)

        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")

        return tests

    def categorize_test_by_name(self, test_name: str) -> str:
        """
        Categorize test based on its name.

        Args:
            test_name: Test function name

        Returns:
            Test type (unit, integration, e2e)
        """
        name_lower = test_name.lower()

        if "integration" in name_lower or "integ" in name_lower:
            return "integration"
        elif "e2e" in name_lower or "end_to_end" in name_lower or "endtoend" in name_lower:
            return "e2e"
        else:
            return "unit"

    def categorize_test_by_markers(self, markers: List[str]) -> str:
        """
        Categorize test based on pytest markers.

        Args:
            markers: List of marker names

        Returns:
            Test type or None if no type markers found
        """
        for marker in markers:
            if marker.lower() in ("integration", "integ"):
                return "integration"
            elif marker.lower() in ("e2e", "end_to_end", "endtoend"):
                return "e2e"
            elif marker.lower() == "unit":
                return "unit"
        return None

    def categorize_test(self, test_obj: Any) -> str:
        """
        Categorize a test object (compatibility method).

        Args:
            test_obj: Test object with name attribute

        Returns:
            Test type
        """
        if hasattr(test_obj, "name"):
            return self.categorize_test_by_name(test_obj.name)
        return "unit"

    def build_catalog(self, services: Optional[List[str]] = None) -> TestCatalog:
        """
        Build complete test catalog.

        Args:
            services: Optional list of services to catalog.
                     If None, discovers all services.

        Returns:
            TestCatalog with all discovered tests
        """
        start_time = time.time()

        # Check cache
        if self._cache is not None and self.enable_cache:
            cache_age = time.time() - (self._cache_timestamp or 0)
            if cache_age < self.cache_ttl:
                logger.info(f"Using cached catalog (age={cache_age:.1f}s)")
                return self._cache

        if services is None:
            services = self.discover_services()

        catalog = TestCatalog()

        for service in services:
            test_files = self.discover_test_files(service)
            all_tests = []

            for test_file in test_files:
                tests = self.collect_tests_from_file(test_file, service)
                all_tests.extend(tests)

            if all_tests:
                service_tests = ServiceTests(
                    service=service,
                    test_files=test_files,
                    tests=all_tests
                )
                catalog.services[service] = service_tests

        # Recalculate total after all services added
        catalog._recalculate_total()
        catalog.discovery_duration = time.time() - start_time

        catalog.discovery_duration = time.time() - start_time

        # Update cache
        if self.enable_cache:
            self._cache = catalog
            self._cache_timestamp = time.time()

        logger.info(
            f"Built catalog: {catalog.total_tests} tests in {len(catalog.services)} services "
            f"in {catalog.discovery_duration:.2f}s"
        )

        return catalog

    def filter_by_service(self, catalog: TestCatalog, service: str) -> TestCatalog:
        """
        Filter catalog to include only specified service.

        Args:
            catalog: Original catalog
            service: Service name to keep

        Returns:
            Filtered TestCatalog
        """
        filtered = TestCatalog(
            services={},
            discovered_at=catalog.discovered_at
        )

        if service in catalog.services:
            filtered.services[service] = catalog.services[service]

        filtered._recalculate_total()
        return filtered

    def filter_by_type(self, catalog: TestCatalog, test_type: str) -> TestCatalog:
        """
        Filter catalog to include only tests of specified type.

        Args:
            catalog: Original catalog
            test_type: Test type to filter (unit, integration, e2e)

        Returns:
            Filtered TestCatalog
        """
        filtered = TestCatalog(
            services={},
            discovered_at=catalog.discovered_at
        )

        for service_name, service_tests in catalog.services.items():
            filtered_tests = [
                t for t in service_tests.tests if t.test_type == test_type
            ]

            if filtered_tests:
                filtered.services[service_name] = ServiceTests(
                    service=service_name,
                    test_files=service_tests.test_files,
                    tests=filtered_tests
                )

        filtered._recalculate_total()
        return filtered

    def clear_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None
        self._cache_timestamp = None
        logger.debug("Discovery cache cleared")

    def get_cache_age(self) -> Optional[float]:
        """
        Get age of cached catalog in seconds.

        Returns:
            Cache age in seconds, or None if no cache
        """
        if self._cache_timestamp is None:
            return None
        return time.time() - self._cache_timestamp

    def refresh_catalog(self) -> TestCatalog:
        """
        Force refresh of catalog, bypassing cache.

        Returns:
            Fresh TestCatalog
        """
        self.clear_cache()
        return self.build_catalog()
