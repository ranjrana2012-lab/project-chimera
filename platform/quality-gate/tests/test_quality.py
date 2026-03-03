"""
Unit tests for quality gate service.

Tests threshold enforcement and quality reporting.
"""

import pytest
from pathlib import Path

# Add quality-gate to path
gate_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(gate_path))


class TestQualityThresholds:
    """Test quality thresholds configuration."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        from gate.quality import QualityThresholds

        thresholds = QualityThresholds()
        assert thresholds.min_coverage == 80.0
        assert thresholds.min_pass_rate == 95.0
        assert thresholds.max_flaky_rate == 5.0

    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        from gate.quality import QualityThresholds

        thresholds = QualityThresholds(
            min_coverage=90.0,
            min_pass_rate=98.0
        )
        assert thresholds.min_coverage == 90.0
        assert thresholds.min_pass_rate == 98.0


class TestQualityGateResult:
    """Test quality gate result."""

    def test_passed_result(self):
        """Test passed gate result."""
        from gate.quality import QualityGateResult

        result = QualityGateResult(
            gate_id="pr-123",
            status="passed",
            total_checks=10,
            passed_checks=10,
            failed_checks=0
        )
        assert result.is_passed() is True
        assert result.get_score() == 100.0

    def test_failed_result(self):
        """Test failed gate result."""
        from gate.quality import QualityGateResult

        result = QualityGateResult(
            gate_id="pr-123",
            status="failed",
            total_checks=10,
            passed_checks=7,
            failed_checks=3
        )
        assert result.is_passed() is False
        assert result.get_score() == 70.0

    def test_result_with_violations(self):
        """Test result with threshold violations."""
        from gate.quality import QualityGateResult

        result = QualityGateResult(
            gate_id="pr-123",
            status="failed",
            violations=[
                {"check": "coverage", "threshold": 80, "actual": 75},
                {"check": "pass_rate", "threshold": 95, "actual": 92}
            ]
        )
        assert len(result.violations) == 2
        assert result.violations[0]["check"] == "coverage"


class TestQualityGateService:
    """Test quality gate service."""

    @pytest.fixture
    def service(self):
        """Create quality gate service."""
        from gate.quality import QualityGateService
        return QualityGateService()

    def test_service_init(self, service):
        """Test service initialization."""
        assert service.thresholds is not None

    def test_check_coverage_gate_passed(self):
        """Test coverage gate that passes."""
        from gate.quality import QualityGateService

        service = QualityGateService(min_coverage=80.0)

        result = service.check_coverage_gate(
            overall_coverage=85.0,
            new_code_coverage=87.0
        )
        assert result["passed"] is True

    def test_check_coverage_gate_failed(self):
        """Test coverage gate that fails."""
        from gate.quality import QualityGateService

        service = QualityGateService(min_coverage=80.0)

        result = service.check_coverage_gate(
            overall_coverage=75.0,
            new_code_coverage=78.0
        )
        assert result["passed"] is False
        assert result["threshold"] == 80.0

    def test_check_test_gate_passed(self):
        """Test test gate that passes."""
        from gate.quality import QualityGateService

        service = QualityGateService(min_pass_rate=95.0)

        result = service.check_test_gate(
            total_tests=100,
            passed=96,
            failed=4
        )
        assert result["passed"] is True

    def test_check_test_gate_failed(self):
        """Test test gate that fails."""
        from gate.quality import QualityGateService

        service = QualityGateService(min_pass_rate=95.0)

        result = service.check_test_gate(
            total_tests=100,
            passed=90,
            failed=10
        )
        assert result["passed"] is False

    def test_check_flaky_test_gate(self):
        """Test flaky test gate."""
        from gate.quality import QualityGateService

        service = QualityGateService(max_flaky_rate=5.0)

        result = service.check_flaky_test_gate(
            total_tests=100,
            flaky_count=3
        )
        assert result["passed"] is True

    def test_check_performance_gate(self):
        """Test performance gate."""
        from gate.quality import QualityGateService

        service = QualityGateService()

        result = service.check_performance_gate(
            endpoint_p95_ms=90,
            endpoint_p99_ms=180,
            health_p95_ms=80
        )
        assert result["passed"] is True

    def test_evaluate_pull_request(self):
        """Test full PR evaluation."""
        from gate.quality import QualityGateService

        service = QualityGateService()

        pr_data = {
            "overall_coverage": 85.0,
            "new_code_coverage": 87.0,
            "total_tests": 100,
            "passed": 96,
            "failed": 4,
            "flaky_count": 2,
            "p95_latency_ms": 90,
            "p99_latency_ms": 180
        }

        result = service.evaluate_pull_request("pr-123", pr_data)
        assert result.is_passed() is True


class TestQualityReporter:
    """Test quality reporter."""

    @pytest.fixture
    def reporter(self):
        """Create quality reporter."""
        from gate.quality import QualityReporter
        return QualityReporter()

    def test_generate_report_passed(self):
        """Test generating report for passed gate."""
        from gate.quality import QualityGateResult, QualityReporter

        result = QualityGateResult(
            gate_id="pr-123",
            status="passed",
            total_checks=10,
            passed_checks=10,
            failed_checks=0
        )

        reporter = QualityReporter()
        report = reporter.generate_report(result)

        assert report["gate_id"] == "pr-123"
        assert report["status"] == "passed"

    def test_generate_report_failed(self):
        """Test generating report for failed gate."""
        from gate.quality import QualityGateResult, QualityReporter

        result = QualityGateResult(
            gate_id="pr-123",
            status="failed",
            violations=[
                {"check": "coverage", "threshold": 80, "actual": 75}
            ]
        )

        reporter = QualityReporter()
        report = reporter.generate_report(result)

        assert report["status"] == "failed"
        assert len(report["violations"]) == 1

    def test_format_summary(self):
        """Test formatting summary."""
        from gate.quality import QualityReporter

        reporter = QualityReporter()

        summary = reporter.format_summary(
            total_prs=100,
            passed_prs=85,
            failed_prs=15,
            avg_score=92.5
        )

        assert summary["pass_rate"] == 85.0
