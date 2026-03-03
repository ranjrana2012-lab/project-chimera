"""
Unit tests for Coverage Collector.

Tests coverage measurement and reporting.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
import json

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))

from core.coverage import (
    CoverageCollector,
    CoverageReport,
    CoverageData,
    FileCoverage
)


class TestFileCoverage:
    """Test FileCoverage dataclass."""

    def test_create_file_coverage(self):
        """Test creating file coverage data."""
        coverage = FileCoverage(
            path="test_file.py",
            total_lines=100,
            covered_lines=80,
            percentage=80.0,
            missing_lines=[10, 20, 30]
        )

        assert coverage.path == "test_file.py"
        assert coverage.percentage == 80.0
        assert len(coverage.missing_lines) == 3


class TestCoverageData:
    """Test CoverageData dataclass."""

    def test_create_coverage_data(self):
        """Test creating coverage data."""
        files = {
            "file1.py": FileCoverage(
                path="file1.py",
                total_lines=50,
                covered_lines=40,
                percentage=80.0
            )
        }

        data = CoverageData(
            total_lines=50,
            covered_lines=40,
            percentage=80.0,
            files=files
        )

        assert data.percentage == 80.0
        assert len(data.files) == 1


class TestCoverageReport:
    """Test CoverageReport dataclass."""

    def test_create_report(self):
        """Test creating coverage report."""
        coverage_data = CoverageData(
            total_lines=100,
            covered_lines=85,
            percentage=85.0,
            files={}
        )

        report = CoverageReport(
            service="test-service",
            coverage=coverage_data,
            timestamp="2026-03-04T00:00:00Z"
        )

        assert report.service == "test-service"
        assert report.coverage.percentage == 85.0

    def test_to_dict(self):
        """Test converting report to dict."""
        coverage_data = CoverageData(
            total_lines=100,
            covered_lines=85,
            percentage=85.0,
            files={}
        )

        report = CoverageReport(
            service="test-service",
            coverage=coverage_data
        )

        data = report.to_dict()

        assert "service" in data
        assert "coverage" in data
        assert data["service"] == "test-service"


class TestCoverageCollector:
    """Test CoverageCollector functionality."""

    @pytest.fixture
    def collector(self):
        """Create coverage collector instance."""
        return CoverageCollector()

    @pytest.fixture
    def mock_coverage_json(self, tmp_path):
        """Create mock coverage.json file."""
        coverage_data = {
            "meta": {
                "timestamp": "2026-03-04T00:00:00Z"
            },
            "files": {
                "test_module.py": {
                    "summary": {
                        "num_statements": 50,
                        "covered_lines": 40,
                        "percent_covered": 80.0
                    },
                    "missing_lines": [10, 20, 30]
                },
                "another_module.py": {
                    "summary": {
                        "num_statements": 30,
                        "covered_lines": 30,
                        "percent_covered": 100.0
                    },
                    "missing_lines": []
                }
            },
            "totals": {
                "num_statements": 80,
                "covered_lines": 70,
                "percent_covered": 87.5
            }
        }

        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        return tmp_path

    def test_collector_init(self, collector):
        """Test collector initialization."""
        assert collector is not None

    def test_parse_coverage_json(self, collector, mock_coverage_json):
        """Test parsing coverage.json file."""
        coverage_file = mock_coverage_json / "coverage.json"

        data = collector.parse_coverage_json(coverage_file)

        assert data is not None
        assert data.total_lines == 80
        assert data.covered_lines == 70
        assert data.percentage == 87.5
        assert len(data.files) == 2

    def test_parse_missing_file(self, collector, tmp_path):
        """Test parsing non-existent file."""
        missing_file = tmp_path / "nonexistent.json"

        data = collector.parse_coverage_json(missing_file)

        assert data is None

    def test_generate_report(self, collector, mock_coverage_json):
        """Test generating coverage report."""
        coverage_file = mock_coverage_json / "coverage.json"

        report = collector.generate_report("test-service", coverage_file)

        assert report.service == "test-service"
        assert report.coverage.percentage == 87.5

    def test_collect_coverage_from_service(self, collector, tmp_path):
        """Test collecting coverage from a service directory."""
        service_path = tmp_path / "test-service"
        service_path.mkdir()

        # Create coverage.json
        coverage_data = {
            "files": {},
            "totals": {
                "num_statements": 100,
                "covered_lines": 90,
                "percent_covered": 90.0
            }
        }

        coverage_file = service_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        report = collector.collect_from_service(str(service_path), "test-service")

        assert report is not None
        assert report.service == "test-service"
        assert report.coverage.percentage == 90.0

    def test_collect_no_coverage_file(self, collector, tmp_path):
        """Test collecting when no coverage file exists."""
        service_path = tmp_path / "test-service"
        service_path.mkdir()

        report = collector.collect_from_service(str(service_path), "test-service")

        assert report is None

    def test_aggregate_coverage(self, collector):
        """Test aggregating coverage from multiple reports."""
        report1 = CoverageReport(
            service="svc1",
            coverage=CoverageData(
                total_lines=100,
                covered_lines=80,
                percentage=80.0,
                files={}
            )
        )

        report2 = CoverageReport(
            service="svc2",
            coverage=CoverageData(
                total_lines=50,
                covered_lines=50,
                percentage=100.0,
                files={}
            )
        )

        aggregated = collector.aggregate_reports([report1, report2])

        assert aggregated.total_lines == 150  # 100 + 50
        assert aggregated.covered_lines == 130  # 80 + 50
        assert abs(aggregated.percentage - 86.67) < 0.01  # 130/150 * 100

    def test_get_uncovered_files(self, collector, mock_coverage_json):
        """Test getting list of uncovered files."""
        coverage_file = mock_coverage_json / "coverage.json"

        data = collector.parse_coverage_json(coverage_file)
        uncovered = collector.get_uncovered_files(data)

        # test_module.py has missing lines
        assert "test_module.py" in uncovered
        # another_module.py is fully covered
        assert "another_module.py" not in uncovered

    def test_filter_by_threshold(self, collector):
        """Test filtering files by coverage threshold."""
        file1 = FileCoverage(
            path="low_coverage.py",
            total_lines=100,
            covered_lines=50,
            percentage=50.0
        )

        file2 = FileCoverage(
            path="high_coverage.py",
            total_lines=100,
            covered_lines=95,
            percentage=95.0
        )

        data = CoverageData(
            total_lines=200,
            covered_lines=145,
            percentage=72.5,
            files={
                "low_coverage.py": file1,
                "high_coverage.py": file2
            }
        )

        # Filter for files below 80% coverage
        low_files = collector.filter_by_coverage(data, min_percentage=80.0, below=True)

        assert "low_coverage.py" in low_files
        assert "high_coverage.py" not in low_files


class TestCoverageFormatting:
    """Test coverage report formatting."""

    @pytest.fixture
    def collector(self):
        """Create coverage collector instance."""
        return CoverageCollector()

    def test_format_summary(self, collector):
        """Test formatting coverage summary."""
        data = CoverageData(
            total_lines=1000,
            covered_lines=850,
            percentage=85.0,
            files={}
        )

        summary = collector.format_summary(data)

        assert "85.0%" in summary
        assert "850" in summary
        assert "1000" in summary

    def test_format_file_list(self, collector):
        """Test formatting file coverage list."""
        files = {
            "file1.py": FileCoverage(
                path="file1.py",
                total_lines=100,
                covered_lines=80,
                percentage=80.0
            ),
            "file2.py": FileCoverage(
                path="file2.py",
                total_lines=50,
                covered_lines=50,
                percentage=100.0
            )
        }

        data = CoverageData(
            total_lines=150,
            covered_lines=130,
            percentage=86.67,
            files=files
        )

        file_list = collector.format_file_list(data)

        assert "file1.py" in file_list
        assert "80.0%" in file_list
        assert "file2.py" in file_list
        assert "100.0%" in file_list

    def test_to_json(self, collector):
        """Test JSON serialization of coverage data."""
        data = CoverageData(
            total_lines=100,
            covered_lines=85,
            percentage=85.0,
            files={}
        )

        json_str = data.to_json()

        # Verify valid JSON
        parsed = json.loads(json_str)
        assert parsed["percentage"] == 85.0
