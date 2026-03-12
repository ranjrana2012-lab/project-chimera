# tests/metrics_report.py
"""Test metrics collector and report generator.

This module collects test metrics including pass rates, latency measurements,
and flakiness detection to generate comprehensive test reports.
"""

import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, dict
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TestResult:
    """Result of a single test run."""

    name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float
    error_message: str | None = None
    test_file: str = ""


@dataclass
class TestSuiteMetrics:
    """Metrics for a test suite."""

    name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    pass_rate: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)


@dataclass
class FlakyTest:
    """Information about a flaky test."""

    name: str
    test_file: str
    failure_count: int
    success_count: int
    flakiness_ratio: float


class TestMetricsCollector:
    """Collect and analyze test metrics."""

    def __init__(self, project_root: str | None = None):
        """Initialize metrics collector.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_results: dict[str, TestSuiteMetrics] = {}
        self.flaky_tests: list[FlakyTest] = []
        self._run_history: dict[str, list[TestResult]] = defaultdict(list)

    def run_pytest(
        self,
        test_path: str = "tests/",
        verbose: bool = True,
        coverage: bool = False,
    ) -> subprocess.CompletedProcess:
        """Run pytest and collect results.

        Args:
            test_path: Path to tests
            verbose: Enable verbose output
            coverage: Enable coverage reporting

        Returns:
            Completed process result
        """
        cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]

        if coverage:
            cmd.extend(["--cov=.", "--cov-report=term-missing"])

        # Add JSON output for parsing
        json_file = self.project_root / ".pytest_results.json"
        cmd.extend(["--json-report-file", str(json_file)])

        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        # Parse JSON results if available
        if json_file.exists():
            self._parse_json_results(json_file)
            json_file.unlink()  # Clean up

        return result

    def _parse_json_results(self, json_file: Path) -> None:
        """Parse pytest JSON results file.

        Args:
            json_file: Path to JSON results file
        """
        try:
            with open(json_file) as f:
                data = json.load(f)

            for test in data.get("tests", []):
                test_name = test.get("name", "")
                outcome = test.get("outcome", "unknown")
                duration = test.get("duration", 0.0)

                result = TestResult(
                    name=test_name,
                    status=outcome,
                    duration=duration,
                    test_file=test.get("location", ""),
                )

                # Store in run history
                self._run_history[test_name].append(result)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON results: {e}")

    def collect_from_coverage(self) -> dict[str, float]:
        """Collect coverage data from .coverage file.

        Returns:
            Dictionary mapping module names to coverage percentages
        """
        coverage_file = self.project_root / ".coverage"

        if not coverage_file.exists():
            return {}

        # Run coverage report command
        result = subprocess.run(
            ["python", "-m", "coverage", "report", "--json"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        coverage_data = {}

        try:
            data = json.loads(result.stdout)
            for file_info in data.get("files", []):
                filename = file_info.get("file", "")
                coverage = file_info.get("summary", {}).get("percent_covered", 0.0)
                coverage_data[filename] = coverage
        except (json.JSONDecodeError, KeyError):
            pass

        return coverage_data

    def analyze_flakiness(
        self,
        min_runs: int = 3,
        flakiness_threshold: float = 0.3,
    ) -> list[FlakyTest]:
        """Analyze test flakiness from run history.

        Args:
            min_runs: Minimum number of runs to consider
            flakiness_threshold: Ratio threshold for considering a test flaky

        Returns:
            List of flaky tests
        """
        flaky = []

        for test_name, results in self._run_history.items():
            if len(results) < min_runs:
                continue

            failures = sum(1 for r in results if r.status in ("failed", "error"))
            successes = sum(1 for r in results if r.status == "passed")
            total_runs = len(results)

            if total_runs == 0:
                continue

            flakiness_ratio = failures / total_runs

            if flakiness_ratio >= flakiness_ratio and flakiness_ratio < 1.0:
                # Not always failing, but fails sometimes
                test_file = results[0].test_file if results else ""

                flaky.append(FlakyTest(
                    name=test_name,
                    test_file=test_file,
                    failure_count=failures,
                    success_count=successes,
                    flakiness_ratio=flakiness_ratio,
                ))

        self.flaky_tests = sorted(
            flaky,
            key=lambda x: x.flakiness_ratio,
            reverse=True,
        )

        return self.flaky_tests

    def calculate_suite_metrics(self, suite_name: str, results: list[TestResult]) -> TestSuiteMetrics:
        """Calculate metrics for a test suite.

        Args:
            suite_name: Name of the test suite
            results: List of test results

        Returns:
            TestSuiteMetrics object
        """
        metrics = TestSuiteMetrics(name=suite_name)

        for result in results:
            metrics.total_tests += 1
            metrics.total_duration += result.duration

            if result.status == "passed":
                metrics.passed += 1
            elif result.status == "failed":
                metrics.failed += 1
            elif result.status == "skipped":
                metrics.skipped += 1
            elif result.status == "error":
                metrics.errors += 1

        if metrics.total_tests > 0:
            metrics.avg_duration = metrics.total_duration / metrics.total_tests
            metrics.pass_rate = (metrics.passed / metrics.total_tests) * 100

        metrics.test_results = results

        return metrics

    def generate_report(
        self,
        output_file: str | None = None,
        format: str = "markdown",
    ) -> str:
        """Generate test metrics report.

        Args:
            output_file: Optional file to write report to
            format: Report format ("markdown", "json", "html")

        Returns:
            Report content as string
        """
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "suites": {},
            "flaky_tests": [
                {
                    "name": t.name,
                    "test_file": t.test_file,
                    "failure_count": t.failure_count,
                    "success_count": t.success_count,
                    "flakiness_ratio": t.flakiness_ratio,
                }
                for t in self.flaky_tests
            ],
        }

        # Add suite metrics
        for suite_name, metrics in self.test_results.items():
            report_data["suites"][suite_name] = {
                "total_tests": metrics.total_tests,
                "passed": metrics.passed,
                "failed": metrics.failed,
                "skipped": metrics.skipped,
                "errors": metrics.errors,
                "total_duration": metrics.total_duration,
                "avg_duration": metrics.avg_duration,
                "pass_rate": metrics.pass_rate,
            }

        if format == "json":
            report = json.dumps(report_data, indent=2)
        elif format == "markdown":
            report = self._generate_markdown_report(report_data)
        elif format == "html":
            report = self._generate_html_report(report_data)
        else:
            raise ValueError(f"Unknown format: {format}")

        if output_file:
            output_path = self.project_root / output_file
            with open(output_path, "w") as f:
                f.write(report)
            print(f"Report written to {output_path}")

        return report

    def _generate_markdown_report(self, data: dict) -> str:
        """Generate markdown format report.

        Args:
            data: Report data dictionary

        Returns:
            Markdown formatted report
        """
        lines = [
            "# Test Metrics Report",
            f"Generated: {data['timestamp']}",
            "",
            "## Summary",
            "",
        ]

        total_tests = sum(s["total_tests"] for s in data["suites"].values())
        total_passed = sum(s["passed"] for s in data["suites"].values())
        total_failed = sum(s["failed"] for s in data["suites"].values())
        total_duration = sum(s["total_duration"] for s in data["suites"].values())

        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        lines.extend([
            f"- **Total Tests**: {total_tests}",
            f"- **Passed**: {total_passed}",
            f"- **Failed**: {total_failed}",
            f"- **Pass Rate**: {overall_pass_rate:.1f}%",
            f"- **Total Duration**: {total_duration:.2f}s",
            "",
            "## Test Suites",
            "",
        ])

        for suite_name, metrics in data["suites"].items():
            lines.extend([
                f"### {suite_name}",
                f"- Tests: {metrics['total_tests']}",
                f"- Passed: {metrics['passed']}",
                f"- Failed: {metrics['failed']}",
                f"- Pass Rate: {metrics['pass_rate']:.1f}%",
                f"- Avg Duration: {metrics['avg_duration']:.3f}s",
                "",
            ])

        if data["flaky_tests"]:
            lines.extend([
                "## Flaky Tests",
                "",
                "| Test | File | Failures | Successes | Flakiness |",
                "|------|------|----------|-----------|-----------|",
            ])

            for test in data["flaky_tests"]:
                lines.append(
                    f"| {test['name']} | {test['test_file']} | "
                    f"{test['failure_count']} | {test['success_count']} | "
                    f"{test['flakiness_ratio']:.1%} |"
                )

        return "\n".join(lines)

    def _generate_html_report(self, data: dict) -> str:
        """Generate HTML format report.

        Args:
            data: Report data dictionary

        Returns:
            HTML formatted report
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Metrics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ccc; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Test Metrics Report</h1>
    <p>Generated: {data['timestamp']}</p>

    <div class="summary">
        <h2>Summary</h2>
"""

        total_tests = sum(s["total_tests"] for s in data["suites"].values())
        total_passed = sum(s["passed"] for s in data["suites"].values())
        total_failed = sum(s["failed"] for s in data["suites"].values())
        total_duration = sum(s["total_duration"] for s in data["suites"].values())
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        html += f"""
        <p><strong>Total Tests:</strong> {total_tests}</p>
        <p><strong>Passed:</strong> <span class="pass">{total_passed}</span></p>
        <p><strong>Failed:</strong> <span class="fail">{total_failed}</span></p>
        <p><strong>Pass Rate:</strong> {overall_pass_rate:.1f}%</p>
        <p><strong>Total Duration:</strong> {total_duration:.2f}s</p>
    </div>

    <h2>Test Suites</h2>
    <table>
        <tr>
            <th>Suite</th>
            <th>Tests</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Pass Rate</th>
            <th>Avg Duration</th>
        </tr>
"""

        for suite_name, metrics in data["suites"].items():
            html += f"""
        <tr>
            <td>{suite_name}</td>
            <td>{metrics['total_tests']}</td>
            <td class="pass">{metrics['passed']}</td>
            <td class="fail">{metrics['failed']}</td>
            <td>{metrics['pass_rate']:.1f}%</td>
            <td>{metrics['avg_duration']:.3f}s</td>
        </tr>
"""

        html += """
    </table>
"""

        if data["flaky_tests"]:
            html += """
    <h2>Flaky Tests</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>File</th>
            <th>Failures</th>
            <th>Successes</th>
            <th>Flakiness</th>
        </tr>
"""

            for test in data["flaky_tests"]:
                html += f"""
        <tr>
            <td>{test['name']}</td>
            <td>{test['test_file']}</td>
            <td>{test['failure_count']}</td>
            <td>{test['success_count']}</td>
            <td>{test['flakiness_ratio']:.1%}</td>
        </tr>
"""

            html += """
    </table>
"""

        html += """
</body>
</html>
"""

        return html


def generate_resilience_test_report() -> str:
    """Generate test report for resilience patterns.

    Returns:
        Report content
    """
    collector = TestMetricsCollector()

    # Run resilience tests
    print("Running resilience tests...")
    result = collector.run_pytest("tests/resilience/")

    # Analyze results
    collector.analyze_flakiness()

    # Calculate metrics for each test file
    test_files = [
        ("test_retry", "tests/resilience/test_retry.py"),
        ("test_circuit_breaker", "tests/resilience/test_circuit_breaker.py"),
        ("test_degradation", "tests/resilience/test_degradation.py"),
    ]

    for suite_name, test_file in test_files:
        metrics = collector.calculate_suite_metrics(suite_name, [])
        collector.test_results[suite_name] = metrics

    # Generate report
    report = collector.generate_report(
        output_file="test-results/resilience-report.md",
        format="markdown",
    )

    return report


if __name__ == "__main__":
    # Generate the report when run directly
    print("Generating resilience test metrics report...")
    report = generate_resilience_test_report()
    print("\n" + report)
