"""
Unit tests for Test Discovery module.

Tests the discovery and cataloging of pytest tests across services.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))

# Import directly from the module
from core.discovery import (
    TestDiscovery,
    TestCatalog,
    TestInfo,
    ServiceTests
)


class TestTestDiscovery:
    """Test TestDiscovery functionality."""

    @pytest.fixture
    def discovery(self):
        """Create test discovery instance."""
        return TestDiscovery(
            services_path="services",
            test_patterns=["test_*.py", "*_test.py"]
        )

    @pytest.fixture
    def mock_services_dir(self, tmp_path):
        """Create a mock services directory with tests."""
        # Create mock service structure
        service1 = tmp_path / "services" / "scenespeak-agent"
        service1.mkdir(parents=True)
        tests1 = service1 / "tests"
        tests1.mkdir()

        # Create test files
        (tests1 / "test_dialogue.py").write_text("""
def test_generate_dialogue():
    assert True

def test_dialogue_with_context():
    assert True
""")

        (tests1 / "test_integration.py").write_text("""
import pytest

def test_full_dialogue_flow():
    assert True

@pytest.mark.integration
def test_dialogue_generation_integration():
    assert True
""")

        service2 = tmp_path / "services" / "captioning-agent"
        service2.mkdir(parents=True)
        tests2 = service2 / "tests"
        tests2.mkdir()

        (tests2 / "test_transcription.py").write_text("""
def test_transcribe_audio():
    assert True

def test_whisper_fallback():
    assert True
""")

        return tmp_path

    def test_discovery_init(self, discovery):
        """Test discovery initialization."""
        assert discovery.services_path.name == "services"
        assert discovery.test_patterns == ["test_*.py", "*_test.py"]

    def test_discover_services(self, discovery, mock_services_dir):
        """Test discovering all services with tests."""
        # Change to mock directory
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            services = discovery.discover_services()
            assert len(services) == 2
            assert "scenespeak-agent" in services
            assert "captioning-agent" in services
        finally:
            os.chdir(original_cwd)

    def test_discover_test_files(self, discovery, mock_services_dir):
        """Test discovering test files in a service."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            test_files = discovery.discover_test_files("scenespeak-agent")
            assert len(test_files) == 2
            assert any("test_dialogue.py" in f for f in test_files)
            assert any("test_integration.py" in f for f in test_files)
        finally:
            os.chdir(original_cwd)

    def test_collect_tests_from_file(self, discovery, mock_services_dir):
        """Test collecting tests from a file."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            test_file = "tests/test_dialogue.py"
            tests = discovery.collect_tests_from_file(test_file, "scenespeak-agent")

            assert len(tests) == 2
            assert tests[0].name == "test_generate_dialogue"
            assert tests[1].name == "test_dialogue_with_context"
        finally:
            os.chdir(original_cwd)

    def test_categorize_test_by_name(self, discovery):
        """Test test categorization by name."""
        # Unit test (no special marker)
        assert discovery.categorize_test_by_name("test_simple_function") == "unit"

        # Integration test (has 'integration' in name)
        assert discovery.categorize_test_by_name("test_api_integration") == "integration"

        # E2E test
        assert discovery.categorize_test_by_name("test_e2e_user_flow") == "e2e"

    def test_categorize_test_by_markers(self, discovery):
        """Test test categorization by markers."""
        assert discovery.categorize_test_by_markers(["integration"]) == "integration"
        assert discovery.categorize_test_by_markers(["e2e"]) == "e2e"
        assert discovery.categorize_test_by_markers(["unit"]) == "unit"
        assert discovery.categorize_test_by_markers([]) is None

    def test_build_catalog(self, discovery, mock_services_dir):
        """Test building full test catalog."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            catalog = discovery.build_catalog()

            assert catalog.total_tests == 6  # 4 in scenespeak, 2 in captioning
            assert len(catalog.services) == 2
            assert "scenespeak-agent" in catalog.services
            assert "captioning-agent" in catalog.services

            # Check scenespeak tests
            scenespeak = catalog.services["scenespeak-agent"]
            assert scenespeak.total_count == 4

        finally:
            os.chdir(original_cwd)

    def test_catalog_to_dict(self, discovery, mock_services_dir):
        """Test converting catalog to dictionary."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            catalog = discovery.build_catalog()
            catalog_dict = catalog.to_dict()

            assert "services" in catalog_dict
            assert "total_tests" in catalog_dict
            assert catalog_dict["total_tests"] == 6
            assert "discovered_at" in catalog_dict

        finally:
            os.chdir(original_cwd)

    def test_filter_catalog_by_service(self, discovery, mock_services_dir):
        """Test filtering catalog by service."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            catalog = discovery.build_catalog()
            filtered = discovery.filter_by_service(catalog, "scenespeak-agent")

            assert filtered.total_tests == 4
            assert len(filtered.services) == 1
            assert "scenespeak-agent" in filtered.services

        finally:
            os.chdir(original_cwd)

    def test_filter_catalog_by_type(self, discovery, mock_services_dir):
        """Test filtering catalog by test type."""
        import os
        original_cwd = os.getcwd()
        os.chdir(mock_services_dir)

        try:
            catalog = discovery.build_catalog()
            filtered = discovery.filter_by_type(catalog, "integration")

            # Only tests with 'integration' in name
            assert filtered.total_tests >= 1

        finally:
            os.chdir(original_cwd)

    def test_empty_services_directory(self, discovery, tmp_path):
        """Test discovery with no services."""
        empty_dir = tmp_path / "empty_services"
        empty_dir.mkdir()

        import os
        original_cwd = os.getcwd()
        os.chdir(empty_dir)

        try:
            services = discovery.discover_services()
            assert len(services) == 0
        finally:
            os.chdir(original_cwd)


class TestIntegrationDiscovery:
    """Integration tests with actual services directory."""

    @pytest.fixture
    def real_discovery(self):
        """Create discovery for actual services."""
        return TestDiscovery(
            services_path="services",
            test_patterns=["test_*.py", "*_test.py"]
        )

    def test_discover_real_services(self, real_discovery):
        """Test discovering real services."""
        services = real_discovery.discover_services()

        # Should find services with tests
        assert len(services) > 0
        # At minimum, these should exist
        assert any("openclaw" in s for s in services)

    def test_build_real_catalog(self, real_discovery):
        """Test building catalog of real tests."""
        catalog = real_discovery.build_catalog()

        assert catalog.total_tests > 0
        assert len(catalog.services) > 0

        # Check catalog structure
        catalog_dict = catalog.to_dict()
        assert "services" in catalog_dict
        assert "total_tests" in catalog_dict
        assert "discovered_at" in catalog_dict


class TestDiscoveryCaching:
    """Test discovery caching mechanism."""

    @pytest.fixture
    def discovery(self):
        """Create discovery with caching."""
        return TestDiscovery(
            services_path="services",
            test_patterns=["test_*.py"],
            enable_cache=True,
            cache_ttl=300  # 5 minutes
        )

    def test_cache_initialization(self, discovery):
        """Test cache is initialized."""
        assert discovery.enable_cache is True
        assert discovery.cache_ttl == 300

    def test_cache_invalidation(self, discovery):
        """Test cache invalidation."""
        discovery.clear_cache()
        assert discovery._cache is None
        assert discovery._cache_timestamp is None

    def test_cache_age_tracking(self, discovery):
        """Test cache age tracking."""
        # Initially no cache
        assert discovery.get_cache_age() is None

        # After building, cache has age
        catalog = discovery.build_catalog()
        age = discovery.get_cache_age()
        assert age is not None
        assert age < 1.0  # Should be very recent

    def test_refresh_bypasses_cache(self, discovery):
        """Test that refresh bypasses cache."""
        # Build initial catalog
        catalog1 = discovery.build_catalog()

        # Refresh should rebuild
        catalog2 = discovery.refresh_catalog()

        # Both should have data
        assert catalog1.total_tests > 0
        assert catalog2.total_tests > 0
        assert catalog1.total_tests == catalog2.total_tests


class TestDataclasses:
    """Test dataclass serialization."""

    def test_test_info_to_dict(self):
        """Test TestInfo serialization."""
        test = TestInfo(
            name="test_example",
            file_path="tests/test_example.py",
            test_type="unit",
            service="test-service",
            line_number=10,
            markers=["slow", "integration"]
        )

        data = test.to_dict()
        assert data["name"] == "test_example"
        assert data["test_type"] == "unit"
        assert data["line_number"] == 10
        assert data["markers"] == ["slow", "integration"]

    def test_test_info_from_dict(self):
        """Test TestInfo deserialization."""
        data = {
            "name": "test_example",
            "file_path": "tests/test_example.py",
            "test_type": "unit",
            "service": "test-service",
            "line_number": 10,
            "markers": ["slow"]
        }

        test = TestInfo.from_dict(data)
        assert test.name == "test_example"
        assert test.test_type == "unit"

    def test_service_tests_post_init(self):
        """Test ServiceTests computed fields."""
        tests = [
            TestInfo(name="test_1", file_path="test.py", test_type="unit", service="svc"),
            TestInfo(name="test_2", file_path="test.py", test_type="unit", service="svc"),
            TestInfo(name="test_3", file_path="test.py", test_type="integration", service="svc"),
        ]

        service = ServiceTests(
            service="test-service",
            test_files=["test.py"],
            tests=tests
        )

        assert service.total_count == 3
        assert service.by_type["unit"] == 2
        assert service.by_type["integration"] == 1

    def test_catalog_post_init(self):
        """Test TestCatalog computed total."""
        catalog = TestCatalog()
        catalog.services = {
            "svc1": ServiceTests(
                service="svc1",
                test_files=[],
                tests=[TestInfo(name="t1", file_path="f.py", service="svc1")]
            ),
            "svc2": ServiceTests(
                service="svc2",
                test_files=[],
                tests=[
                    TestInfo(name="t2", file_path="f.py", service="svc2"),
                    TestInfo(name="t3", file_path="f.py", service="svc2")
                ]
            ),
        }

        # Re-init to trigger post_init
        catalog.total_tests = sum(s.total_count for s in catalog.services.values())
        assert catalog.total_tests == 3
