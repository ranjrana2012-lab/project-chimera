"""
Test Hardening Task for autonomous refactoring loop.

Extends the Ralph Engine with tasks specifically designed for test
hardening and codebase refactoring with anti-gaming protections.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ralph_engine import Context, Result, Task

logger = logging.getLogger(__name__)


@dataclass
class RefactoringTarget:
    """A Python module requiring refactoring or test hardening."""

    module_path: Path
    test_path: Path
    priority: str = "medium"  # high, medium, low
    issue_type: str = "untested"  # untested, low_coverage, technical_debt
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestHardeningTask(Task):
    """Task for hardening tests or refactoring code."""

    target_module: Path
    target_tests: Path
    mode: str = "test_hardening"  # test_hardening, refactor, both
    completion_criteria: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default requirements based on mode."""
        if not self.requirements:
            self.requirements = [
                "All tests must pass (pytest exit code 0)",
                "Assertion count must not decrease",
                "Coverage must remain stable or increase",
                "No PyTorch deprecation warnings"
            ]

        if not self.completion_criteria:
            self.completion_criteria = [
                "pytest_exit_code == 0",
                "assertion_count >= baseline",
                "coverage_percent >= baseline",
                "deprecation_warnings == 0"
            ]


class ClaudeCodeExecutor:
    """Executes Claude Code CLI for autonomous refactoring."""

    def __init__(
        self,
        claude_path: str = "claude",
        max_turns: int = 15,
        timeout: int = 300
    ):
        """Initialize Claude Code executor.

        Args:
            claude_path: Path to claude CLI command
            max_turns: Maximum number of tool calls per session
            timeout: Timeout in seconds for claude execution
        """
        self.claude_path = claude_path
        self.max_turns = max_turns
        self.timeout = timeout

    def execute_refactoring(
        self,
        task: TestHardeningTask,
        context: Context
    ) -> Result:
        """Execute Claude Code for refactoring task.

        Args:
            task: The test hardening task
            context: Execution context

        Returns:
            Result of Claude Code execution
        """
        # Build prompt for Claude
        prompt = self._build_prompt(task, context)

        # Execute Claude Code in headless mode
        try:
            cmd = [
                self.claude_path,
                "-p",  # Print/headless mode
                prompt
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=Path.cwd()
            )

            if result.returncode == 0:
                return Result(
                    success=True,
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "changes_made": self._detect_changes(task)
                    }
                )
            else:
                return Result(
                    success=False,
                    error=f"Claude Code failed: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            return Result(
                success=False,
                error=f"Claude Code timed out after {self.timeout}s"
            )
        except Exception as e:
            return Result(
                success=False,
                error=f"Claude Code execution error: {e}"
            )

    def _build_prompt(self, task: TestHardeningTask, context: Context) -> str:
        """Build prompt for Claude Code.

        Args:
            task: The test hardening task
            context: Execution context

        Returns:
            Prompt string for Claude Code
        """
        base_prompt = f"""You are an autonomous refactoring agent working on Project Chimera.

TASK: {task.mode.upper()}
Target Module: {task.target_module}
Test File: {task.target_tests}

REQUIREMENTS:
{chr(10).join(f"- {r}" for r in task.requirements)}

"""

        if task.mode == "test_hardening":
            mode_prompt = """Your goal is to HARDEN TESTS for the target module:
1. Read and understand the module's public interface
2. Add parameterized tests for edge cases
3. Add assertions to validate expected behavior
4. DO NOT modify the module's source code (only tests)
5. Run pytest to verify all tests pass

DO NOT:
- Delete existing assertions
- Remove failing tests (fix them instead)
- Stub out functions to bypass tests
- Reduce test coverage
"""

        elif task.mode == "refactor":
            mode_prompt = """Your goal is to REFACTOR the target module for better modularity:
1. Identify code smells and coupling issues
2. Extract functions/classes for better organization
3. Improve type annotations
4. Maintain or improve test coverage
5. Run pytest to ensure no regressions

DO NOT:
- Break existing functionality
- Remove error handling
- Reduce test coverage
- Delete assertions from tests
"""

        else:  # both
            mode_prompt = """Your goal is to BOTH refactor AND harden tests:
1. Refactor the module for better modularity
2. Add comprehensive tests with good coverage
3. Ensure all edge cases are covered
4. Run pytest to verify everything works

DO NOT:
- Break existing functionality
- Delete assertions or tests
- Reduce coverage or assertion density
"""

        return base_prompt + mode_prompt

    def _detect_changes(self, task: TestHardeningTask) -> Dict[str, bool]:
        """Detect what changes were made by Claude.

        Args:
            task: The task that was executed

        Returns:
            Dictionary indicating what changed
        """
        # In production, this would use git diff to detect changes
        # For now, return placeholder
        return {
            "tests_modified": True,
            "module_modified": task.mode in ("refactor", "both"),
            "new_tests_added": True
        }


class TestHardeningEngine:
    """Engine for running test hardening and refactoring tasks."""

    def __init__(
        self,
        evaluator_path: Optional[Path] = None,
        claude_executor: Optional[ClaudeCodeExecutor] = None
    ):
        """Initialize the test hardening engine.

        Args:
            evaluator_path: Path to the evaluator script
            claude_executor: Claude Code executor instance
        """
        self.evaluator_path = evaluator_path or Path("platform/quality-gate/evaluate.sh")
        self.claude_executor = claude_executor or ClaudeCodeExecutor()

    def run_task(
        self,
        task: TestHardeningTask,
        context: Context
    ) -> Result:
        """Run a test hardening task with evaluation.

        Args:
            task: The test hardening task
            context: Execution context

        Returns:
            Result of task execution with evaluation
        """
        # Step 1: Execute Claude Code for refactoring
        logger.info(f"Running Claude Code for task {task.id}")
        claude_result = self.claude_executor.execute_refactoring(task, context)

        if not claude_result.success:
            return claude_result

        # Step 2: Run the evaluator (immutable quality gate)
        logger.info("Running anti-gaming evaluator")
        eval_result = self._run_evaluator(task)

        if not eval_result["passed"]:
            return Result(
                success=False,
                error=f"Evaluation failed: {eval_result['outcome']}",
                data={
                    "claude_result": claude_result.data,
                    "eval_result": eval_result
                }
            )

        # Step 3: Return success if all checks passed
        return Result(
            success=True,
            data={
                "claude_result": claude_result.data,
                "eval_result": eval_result,
                "completion_criteria_met": True
            }
        )

    def _run_evaluator(self, task: TestHardeningTask) -> Dict[str, Any]:
        """Run the anti-gaming evaluator.

        Args:
            task: The task to evaluate

        Returns:
            Evaluation result dictionary
        """
        try:
            cmd = [
                str(self.evaluator_path),
                "--test-path", str(task.target_tests.parent),
                "--coverage-target", str(task.target_module.parent)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Parse evaluation result from exit code
            exit_code = result.returncode

            outcome_map = {
                0: "passed",
                1: "failed_functional",
                2: "failed_reward_hacking",
                3: "failed_coverage",
                4: "failed_deprecations",
                5: "error"
            }

            return {
                "passed": exit_code == 0,
                "outcome": outcome_map.get(exit_code, "unknown"),
                "exit_code": exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "outcome": "timeout",
                "error": "Evaluator timed out"
            }
        except Exception as e:
            return {
                "passed": False,
                "outcome": "error",
                "error": str(e)
            }


__all__ = [
    "RefactoringTarget",
    "TestHardeningTask",
    "ClaudeCodeExecutor",
    "TestHardeningEngine",
]
