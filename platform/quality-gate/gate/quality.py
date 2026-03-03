"""
Quality gate service for Project Chimera.

Enforces quality thresholds for code coverage, test results,
performance, and generates quality reports.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GateStatus(Enum):
    """Quality gate status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class QualityThresholds:
    """Quality threshold configuration."""
    min_coverage: float = 80.0
    min_pass_rate: float = 95.0
    max_flaky_rate: float = 5.0

    # Performance thresholds (ms)
    health_p95_ms: float = 100.0
    health_p99_ms: float = 200.0
    generate_p95_ms: float = 2000.0
    generate_p99_ms: float = 5000.0
    websocket_p95_ms: float = 50.0
    websocket_p99_ms: float = 100.0


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""
    gate_id: str
    status: str
    total_checks: int = 10
    passed_checks: int = 0
    failed_checks: int = 0
    violations: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_passed(self) -> bool:
        """Check if gate passed."""
        return self.status == "passed"

    def get_score(self) -> float:
        """Calculate quality score (0-100)."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100

    def add_violation(self, check: str, threshold: float, actual: float):
        """Add a threshold violation."""
        self.violations.append({
            "check": check,
            "threshold": threshold,
            "actual": actual
        })


class QualityGateService:
    """Service for evaluating quality gates."""

    def __init__(self, **kwargs):
        """Initialize service with custom thresholds."""
        self.thresholds = QualityThresholds(**kwargs)

    def check_coverage_gate(
        self,
        overall_coverage: float,
        new_code_coverage: Optional[float] = None
    ) -> Dict[str, Any]:
        """Check coverage gate against threshold."""
        threshold = self.thresholds.min_coverage
        passed = overall_coverage >= threshold

        result = {
            "passed": passed,
            "threshold": threshold,
            "actual": overall_coverage,
            "diff": overall_coverage - threshold
        }

        if new_code_coverage is not None:
            result["new_code_coverage"] = new_code_coverage

        return result

    def check_test_gate(
        self,
        total_tests: int,
        passed: int,
        failed: int
    ) -> Dict[str, Any]:
        """Check test gate against threshold."""
        threshold = self.thresholds.min_pass_rate
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0.0
        passed = pass_rate >= threshold

        return {
            "passed": passed,
            "threshold": threshold,
            "actual": pass_rate,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed
        }

    def check_flaky_test_gate(
        self,
        total_tests: int,
        flaky_count: int
    ) -> Dict[str, Any]:
        """Check flaky test gate against threshold."""
        threshold = self.thresholds.max_flaky_rate
        flaky_rate = (flaky_count / total_tests * 100) if total_tests > 0 else 0.0
        passed = flaky_rate <= threshold

        return {
            "passed": passed,
            "threshold": threshold,
            "actual": flaky_rate,
            "flaky_count": flaky_count
        }

    def check_performance_gate(
        self,
        endpoint_p95_ms: Optional[float] = None,
        endpoint_p99_ms: Optional[float] = None,
        health_p95_ms: Optional[float] = None,
        health_p99_ms: Optional[float] = None,
        generate_p95_ms: Optional[float] = None,
        generate_p99_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """Check performance gate against thresholds."""
        checks = []

        if health_p95_ms is not None:
            checks.append(("health_p95", self.thresholds.health_p95_ms, health_p95_ms))
        if health_p99_ms is not None:
            checks.append(("health_p99", self.thresholds.health_p99_ms, health_p99_ms))
        if generate_p95_ms is not None:
            checks.append(("generate_p95", self.thresholds.generate_p95_ms, generate_p95_ms))
        if generate_p99_ms is not None:
            checks.append(("generate_p99", self.thresholds.generate_p99_ms, generate_p99_ms))
        if endpoint_p95_ms is not None:
            checks.append(("endpoint_p95", self.thresholds.generate_p95_ms, endpoint_p95_ms))
        if endpoint_p99_ms is not None:
            checks.append(("endpoint_p99", self.thresholds.generate_p99_ms, endpoint_p99_ms))

        all_passed = all(actual <= threshold for _, threshold, actual in checks)

        return {
            "passed": all_passed,
            "checks": [
                {"name": name, "threshold": thresh, "actual": act}
                for name, thresh, act in checks
            ]
        }

    def evaluate_pull_request(
        self,
        pr_id: str,
        pr_data: Dict[str, Any]
    ) -> QualityGateResult:
        """Evaluate full PR against all quality gates."""
        result = QualityGateResult(
            gate_id=pr_id,
            status="failed"
        )

        # Check coverage
        coverage_result = self.check_coverage_gate(
            overall_coverage=pr_data.get("overall_coverage", 0),
            new_code_coverage=pr_data.get("new_code_coverage")
        )
        if coverage_result["passed"]:
            result.passed_checks += 1
        else:
            result.failed_checks += 1
            result.add_violation(
                "coverage",
                coverage_result["threshold"],
                coverage_result["actual"]
            )

        # Check tests
        test_result = self.check_test_gate(
            total_tests=pr_data.get("total_tests", 0),
            passed=pr_data.get("passed", 0),
            failed=pr_data.get("failed", 0)
        )
        if test_result["passed"]:
            result.passed_checks += 1
        else:
            result.failed_checks += 1
            result.add_violation(
                "pass_rate",
                test_result["threshold"],
                test_result["actual"]
            )

        # Check flaky tests
        if "flaky_count" in pr_data:
            flaky_result = self.check_flaky_test_gate(
                total_tests=pr_data.get("total_tests", 0),
                flaky_count=pr_data["flaky_count"]
            )
            if flaky_result["passed"]:
                result.passed_checks += 1
            else:
                result.failed_checks += 1
                result.add_violation(
                    "flaky_rate",
                    flaky_result["threshold"],
                    flaky_result["actual"]
                )

        # Check performance
        perf_result = self.check_performance_gate(
            endpoint_p95_ms=pr_data.get("p95_latency_ms"),
            endpoint_p99_ms=pr_data.get("p99_latency_ms")
        )
        if perf_result["passed"]:
            result.passed_checks += 1
        else:
            result.failed_checks += 1

        # Determine overall status
        if result.failed_checks == 0:
            result.status = "passed"
        elif result.failed_checks <= 2:
            result.status = "warning"

        return result


class QualityReporter:
    """Service for generating quality reports."""

    def generate_report(self, result: QualityGateResult) -> Dict[str, Any]:
        """Generate quality report from gate result."""
        return {
            "gate_id": result.gate_id,
            "status": result.status,
            "score": result.get_score(),
            "total_checks": result.total_checks,
            "passed_checks": result.passed_checks,
            "failed_checks": result.failed_checks,
            "violations": result.violations,
            "timestamp": result.timestamp.isoformat()
        }

    def format_summary(
        self,
        total_prs: int,
        passed_prs: int,
        failed_prs: int,
        avg_score: float
    ) -> Dict[str, Any]:
        """Format quality summary."""
        pass_rate = (passed_prs / total_prs * 100) if total_prs > 0 else 0.0

        return {
            "total_prs": total_prs,
            "passed_prs": passed_prs,
            "failed_prs": failed_prs,
            "pass_rate": pass_rate,
            "avg_score": avg_score
        }

    def format_violations(self, violations: List[Dict[str, Any]]) -> str:
        """Format violations for display."""
        if not violations:
            return "No violations"

        lines = ["Threshold Violations:"]
        for v in violations:
            lines.append(
                f"  - {v['check']}: {v['actual']} (threshold: {v['threshold']})"
            )
        return "\n".join(lines)


__all__ = [
    "GateStatus",
    "QualityThresholds",
    "QualityGateResult",
    "QualityGateService",
    "QualityReporter"
]
