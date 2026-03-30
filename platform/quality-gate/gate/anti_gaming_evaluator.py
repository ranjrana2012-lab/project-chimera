"""
Anti-Gaming Quality Evaluator for autonomous codebase refactoring.

This module implements ungameable quality metrics to prevent reward hacking
in continuous autonomous refactoring loops, following the AutoResearch
methodology adapted for Project Chimera.

Core Principle: The agent must improve code quality, not just pass tests.
Removing assertions, deleting failing tests, or stubbing functions is
explicitly penalized.

Metrics:
1. Functional Correctness: Pytest exit code must be 0
2. Assertion Density: Total assert count cannot decrease
3. Coverage Growth: Coverage must stay stable (refactor) or increase (test-gen)
4. Deprecation Hygiene: No PyTorch deprecation warnings
5. Mutation Score: Mutation kill rate tracked (mutmut integration)

Based on DGX Spark GB101 specification adapted for Project Chimera x86_64.
"""

import ast
import logging
import re
import subprocess
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EvaluationOutcome(Enum):
    """Outcome of quality gate evaluation."""
    PASSED = "passed"
    FAILED_REWARD_HACKING = "failed_reward_hacking"
    FAILED_FUNCTIONAL = "failed_functional"
    FAILED_COVERAGE = "failed_coverage"
    FAILED_DEPRECATIONS = "failed_deprecations"


@dataclass
class BaselineMetrics:
    """Baseline metrics for comparison (loaded from previous run)."""
    total_assertions: int
    coverage_percent: float
    mutation_score: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EvaluationResult:
    """Result of anti-gaming evaluation."""
    outcome: EvaluationOutcome
    score: float  # Composite score 0-100
    metrics: Dict[str, Any]
    violations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_passed(self) -> bool:
        """Check if evaluation passed."""
        return self.outcome == EvaluationOutcome.PASSED

    def get_violations_summary(self) -> str:
        """Get formatted violations summary."""
        if not self.violations:
            return "No violations"
        return "\n".join(f"  - {v}" for v in self.violations)


class AssertionCounter(ast.NodeVisitor):
    """AST visitor for counting assertions in Python test files."""

    def __init__(self):
        self.assert_count = 0
        # Count both assert statements and pytest assertions
        self.pytest_assertions = 0

    def visit_Assert(self, node: ast.Assert) -> None:
        """Count assert statements."""
        self.assert_count += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Count pytest-style assertions (assert_that, expect, etc.)."""
        if isinstance(node.func, ast.Attribute):
            # Check for common assertion patterns
            if node.func.attr in {
                'assert_that', 'expect', 'should', 'assertEqual',
                'assertNotEqual', 'assertTrue', 'assertFalse',
                'assertIn', 'assertNotIn', 'assertRaises',
                'assertGreater', 'assertLess', 'assertIsNone',
                'assertIsNotNone', 'assertRegex'
            }:
                self.pytest_assertions += 1
        elif isinstance(node.func, ast.Name):
            if node.func.id in {'assert_that', 'expect', 'should'}:
                self.pytest_assertions += 1
        self.generic_visit(node)

    def get_total(self) -> int:
        """Get total assertion count."""
        return self.assert_count + self.pytest_assertions


class DeprecationDetector:
    """Detects PyTorch deprecation warnings in stderr output."""

    # Patterns for PyTorch 2.5/2.6 deprecations
    DEPRECATION_PATTERNS = [
        r'XNNPACKQuantizer.*deprecated',
        r'torch\.ao\.quantization.*deprecated',
        r'TorchCompile.*deprecated',
        r'_scaled_dot_product_efficient_attention.*deprecated',
        r'torch\.nn\.functional\.scaled_dot_product_attention.*warning',
        r'UserWarning.*PyTorch.*deprecated',
        r'DeprecationWarning.*torch\.',
        r'future version.*will be removed',
        r'is deprecated and will be removed',
    ]

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.DEPRECATION_PATTERNS]

    def detect_deprecations(self, stderr: str) -> List[str]:
        """Detect deprecation warnings in stderr output.

        Args:
            stderr: Standard error output from pytest run

        Returns:
            List of deprecation messages found
        """
        deprecations = []
        for line in stderr.split('\n'):
            for pattern in self.patterns:
                if pattern.search(line):
                    deprecations.append(line.strip())
                    break
        return deprecations


class AntiGamingEvaluator:
    """Evaluates code changes against ungameable quality metrics.

    This evaluator implements the AutoResearch methodology adapted for
    Project Chimera: the agent cannot "win" by deleting tests or
    removing assertions. Quality must genuinely improve.
    """

    def __init__(
        self,
        baseline_file: Optional[Path] = None,
        min_coverage: float = 80.0,
        enable_mutation_testing: bool = False
    ):
        """Initialize the evaluator.

        Args:
            baseline_file: Path to baseline metrics JSON file
            min_coverage: Minimum acceptable coverage percentage
            enable_mutation_testing: Whether to run mutation tests
        """
        self.baseline_file = baseline_file or Path("baseline_metrics.json")
        self.min_coverage = min_coverage
        self.enable_mutation_testing = enable_mutation_testing
        self.deprecation_detector = DeprecationDetector()
        self.baseline: Optional[BaselineMetrics] = None

    def load_baseline(self) -> BaselineMetrics:
        """Load baseline metrics from file.

        Returns:
            BaselineMetrics: Loaded baseline or default if not found
        """
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    data = json.load(f)
                return BaselineMetrics(
                    total_assertions=data['total_assertions'],
                    coverage_percent=data['coverage_percent'],
                    mutation_score=data.get('mutation_score'),
                    timestamp=datetime.fromisoformat(data['timestamp'])
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load baseline: {e}, using defaults")

        # Return default baseline
        return BaselineMetrics(
            total_assertions=0,
            coverage_percent=0.0,
            mutation_score=None
        )

    def save_baseline(self, metrics: BaselineMetrics) -> None:
        """Save current metrics as baseline for next iteration.

        Args:
            metrics: Current metrics to save as baseline
        """
        with open(self.baseline_file, 'w') as f:
            json.dump({
                'total_assertions': metrics.total_assertions,
                'coverage_percent': metrics.coverage_percent,
                'mutation_score': metrics.mutation_score,
                'timestamp': metrics.timestamp.isoformat()
            }, f, indent=2)
        logger.info(f"Saved baseline metrics to {self.baseline_file}")

    def count_assertions(self, test_paths: List[Path]) -> int:
        """Count total assertions across all test files.

        Args:
            test_paths: List of paths to test files

        Returns:
            Total assertion count
        """
        total = 0
        for test_path in test_paths:
            if not test_path.exists():
                continue

            try:
                with open(test_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source)
                counter = AssertionCounter()
                counter.visit(tree)
                total += counter.get_total()

            except (SyntaxError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to parse {test_path}: {e}")

        logger.debug(f"Counted {total} assertions across {len(test_paths)} test files")
        return total

    def run_pytest(
        self,
        test_path: Optional[Path] = None,
        coverage_target: Optional[Path] = None
    ) -> Tuple[int, str, str, Optional[float]]:
        """Run pytest with coverage and collect output.

        Args:
            test_path: Path to tests (default: tests/)
            coverage_target: Path to module for coverage measurement

        Returns:
            Tuple of (exit_code, stdout, stderr, coverage_percent)
        """
        cmd = ['python', '-m', 'pytest', '-v', '--tb=short']

        # Add coverage
        if coverage_target:
            cmd.extend([
                '--cov', str(coverage_target),
                '--cov-report', 'term-missing',
                '--cov-report', 'json:.coverage.json'
            ])

        if test_path:
            cmd.append(str(test_path))

        logger.info(f"Running pytest: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse coverage from output or JSON
            coverage = None
            if coverage_target and Path('.coverage.json').exists():
                try:
                    with open('.coverage.json', 'r') as f:
                        cov_data = json.load(f)
                    coverage = cov_data['totals']['percent_covered']
                except (json.JSONDecodeError, KeyError):
                    # Fallback to parsing stdout
                    match = re.search(r'TOTAL\s+(\d+)%\s*', result.stdout)
                    if match:
                        coverage = float(match.group(1))

            return result.returncode, result.stdout, result.stderr, coverage

        except subprocess.TimeoutExpired:
            logger.error("Pytest run timed out after 5 minutes")
            return 1, "", "Timeout after 5 minutes", None
        except Exception as e:
            logger.error(f"Pytest run failed: {e}")
            return 1, "", str(e), None

    def run_mutation_tests(self, test_path: Optional[Path] = None) -> Optional[float]:
        """Run mutation tests using mutmut.

        Args:
            test_path: Path to tests

        Returns:
            Mutation kill rate (0-100) or None if not available
        """
        if not self.enable_mutation_testing:
            return None

        try:
            # Check if mutmut is installed
            subprocess.run(
                ['mutmut', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("mutmut not installed, skipping mutation testing")
            return None

        try:
            cmd = ['mutmut', 'run', '--paths-to-mutate', 'src/']
            if test_path:
                cmd.extend(['--tests-dir', str(test_path)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Parse mutation score from output
            # mutmut output format: "killed 80%, survived 15%, etc."
            match = re.search(r'killed\s+(\d+)%', result.stdout)
            if match:
                return float(match.group(1))

        except subprocess.TimeoutExpired:
            logger.error("Mutation testing timed out")
        except Exception as e:
            logger.warning(f"Mutation testing failed: {e}")

        return None

    def evaluate(
        self,
        test_path: Optional[Path] = None,
        coverage_target: Optional[Path] = None
    ) -> EvaluationResult:
        """Run full anti-gaming evaluation.

        Args:
            test_path: Path to tests
            coverage_target: Path to module for coverage

        Returns:
            EvaluationResult with outcome and metrics
        """
        violations = []
        metrics = {}
        score = 0.0

        # Load baseline
        self.baseline = self.load_baseline()

        # Find all test files
        if test_path and test_path.is_dir():
            test_files = list(test_path.glob('**/test_*.py'))
        elif test_path and test_path.is_file():
            test_files = [test_path]
        else:
            test_files = list(Path('.').glob('tests/**/test_*.py'))

        # Metric 1: Count assertions (anti-gaming: prevent assertion deletion)
        current_assertions = self.count_assertions(test_files)
        metrics['assertions'] = current_assertions

        if self.baseline.total_assertions > 0 and current_assertions < self.baseline.total_assertions:
            violations.append(
                f"Assertion count decreased from {self.baseline.total_assertions} "
                f"to {current_assertions} (reward hacking detected)"
            )

        # Metric 2: Run pytest and check exit code
        exit_code, stdout, stderr, coverage = self.run_pytest(test_path, coverage_target)
        metrics['pytest_exit_code'] = exit_code
        metrics['pytest_output'] = stdout[:1000]  # Truncated for storage

        if exit_code != 0:
            violations.append(f"Pytest failed with exit code {exit_code}")

        # Metric 3: Coverage check
        if coverage is not None:
            metrics['coverage_percent'] = coverage
            if coverage < self.min_coverage:
                violations.append(
                    f"Coverage {coverage:.1f}% below minimum {self.min_coverage}%"
                )

            # Coverage delta check (must not decrease significantly)
            if self.baseline.coverage_percent > 0:
                delta = coverage - self.baseline.coverage_percent
                if delta < -2.0:  # Allow small fluctuations
                    violations.append(
                        f"Coverage decreased by {abs(delta):.1f}% "
                        f"(from {self.baseline.coverage_percent:.1f}% to {coverage:.1f}%)"
                    )

        # Metric 4: Check for deprecation warnings
        deprecations = self.deprecation_detector.detect_deprecations(stderr)
        metrics['deprecation_warnings'] = len(deprecations)

        if deprecations:
            violations.append(
                f"Found {len(deprecations)} PyTorch deprecation warnings"
            )
            metrics['deprecation_details'] = deprecations[:5]  # First 5

        # Metric 5: Mutation testing (optional)
        if self.enable_mutation_testing:
            mutation_score = self.run_mutation_tests(test_path)
            if mutation_score is not None:
                metrics['mutation_score'] = mutation_score
                if self.baseline.mutation_score and mutation_score < self.baseline.mutation_score - 5:
                    violations.append(
                        f"Mutation score decreased from {self.baseline.mutation_score:.1f}% "
                        f"to {mutation_score:.1f}%"
                    )

        # Calculate composite score
        checks = [
            exit_code == 0,
            current_assertions >= self.baseline.total_assertions,
            coverage is None or coverage >= self.min_coverage,
            len(deprecations) == 0
        ]
        score = (sum(checks) / len(checks)) * 100

        # Determine outcome
        if exit_code != 0:
            outcome = EvaluationOutcome.FAILED_FUNCTIONAL
        elif current_assertions < self.baseline.total_assertions:
            outcome = EvaluationOutcome.FAILED_REWARD_HACKING
        elif coverage is not None and coverage < self.min_coverage:
            outcome = EvaluationOutcome.FAILED_COVERAGE
        elif deprecations:
            outcome = EvaluationOutcome.FAILED_DEPRECATIONS
        else:
            outcome = EvaluationOutcome.PASSED

        # Update baseline if passed
        if outcome == EvaluationOutcome.PASSED:
            new_baseline = BaselineMetrics(
                total_assertions=current_assertions,
                coverage_percent=coverage or self.baseline.coverage_percent,
                mutation_score=metrics.get('mutation_score')
            )
            self.save_baseline(new_baseline)

        return EvaluationResult(
            outcome=outcome,
            score=score,
            metrics=metrics,
            violations=violations
        )


__all__ = [
    "EvaluationOutcome",
    "BaselineMetrics",
    "EvaluationResult",
    "AntiGamingEvaluator",
]
