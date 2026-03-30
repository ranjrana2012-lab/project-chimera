#!/usr/bin/env python3
"""
Autonomous Refactoring Orchestrator - Main Loop

This script implements the Ralph-style stateless loop for autonomous
codebase refactoring on Project Chimera.

Based on DGX Spark GB101 specification adapted for x86_64.

Usage:
    python orchestrator.py [--max-iterations N] [--worktree-path PATH]

Environment:
    CHIMERA_WORKTREE_PATH - Path to git worktree (default: auto-create)
    CHIMERA_MAX_ITERATIONS - Maximum iterations before exit (default: unlimited)
    CHIMERA_PROGRAM_MD - Path to program.md (default: .claude/autonomous-refactor/program.md)
    CHIMERA_LEARNINGS_MD - Path to learnings.md (default: .claude/autonomous-refactor/learnings.md)
    CHIMERA_QUEUE_TXT - Path to queue.txt (default: .claude/autonomous-refactor/queue.txt)
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """A task from the queue."""
    priority: str
    mode: str
    module_path: str
    test_path: str
    description: str

    @classmethod
    def from_line(cls, line: str) -> Optional['Task']:
        """Parse a task from queue.txt line."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        parts = [p.strip() for p in line.split('|')]
        if len(parts) != 5:
            logger.warning(f"Invalid task line: {line}")
            return None

        return cls(
            priority=parts[0],
            mode=parts[1],
            module_path=parts[2],
            test_path=parts[3],
            description=parts[4]
        )


@dataclass
class IterationResult:
    """Result of a single iteration."""
    iteration: int
    task: Optional[Task]
    success: bool
    exit_code: int
    duration_seconds: float
    error: Optional[str] = None
    committed: bool = False


class GitWorktreeManager:
    """Manages ephemeral git worktrees for isolated execution."""

    def __init__(
        self,
        repo_root: Path,
        worktree_base: Path = Path(".claude/autonomous-refactor/worktrees")
    ):
        """Initialize worktree manager.

        Args:
            repo_root: Path to git repository root
            worktree_base: Base directory for worktrees
        """
        self.repo_root = repo_root
        self.worktree_base = worktree_base
        self.current_worktree: Optional[Path] = None

    def create_worktree(self, branch: str = "main") -> Path:
        """Create a new ephemeral worktree.

        Args:
            branch: Branch to base worktree on (default: main)

        Returns:
            Path to the new worktree
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worktree_name = f"iter_{timestamp}"
        worktree_path = self.worktree_base / worktree_name

        # Create worktree
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch],
            cwd=self.repo_root,
            check=True,
            capture_output=True
        )

        self.current_worktree = worktree_path
        logger.info(f"Created worktree: {worktree_path}")
        return worktree_path

    def remove_worktree(self, worktree: Path) -> None:
        """Remove an ephemeral worktree.

        Args:
            worktree: Path to worktree to remove
        """
        subprocess.run(
            ["git", "worktree", "remove", str(worktree)],
            cwd=self.repo_root,
            check=True,
            capture_output=True
        )
        logger.info(f"Removed worktree: {worktree}")

    def reset_worktree(self, worktree: Path) -> None:
        """Hard reset worktree to clean state.

        Args:
            worktree: Path to worktree to reset
        """
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=worktree,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            cwd=worktree,
            check=True,
            capture_output=True
        )
        logger.info(f"Reset worktree: {worktree}")

    def commit_changes(
        self,
        worktree: Path,
        message: str
    ) -> bool:
        """Commit changes in worktree.

        Args:
            worktree: Path to worktree
            message: Commit message

        Returns:
            True if commit succeeded
        """
        try:
            # Stage changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=worktree,
                check=True,
                capture_output=True
            )

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=worktree
            )
            if result.returncode == 0:
                logger.info("No changes to commit")
                return False

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=worktree,
                check=True,
                capture_output=True
            )

            logger.info(f"Committed changes: {message}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e}")
            return False


class RalphOrchestrator:
    """Main orchestrator for autonomous refactoring loop."""

    def __init__(
        self,
        repo_root: Path,
        program_md: Path,
        learnings_md: Path,
        queue_txt: Path,
        evaluator_path: Path,
        max_iterations: Optional[int] = None
    ):
        """Initialize orchestrator.

        Args:
            repo_root: Path to git repository root
            program_md: Path to program.md (constitutional constraints)
            learnings_md: Path to learnings.md (historical context)
            queue_txt: Path to queue.txt (task queue)
            evaluator_path: Path to evaluator.sh script
            max_iterations: Maximum iterations (None = unlimited)
        """
        self.repo_root = repo_root
        self.program_md = program_md
        self.learnings_md = learnings_md
        self.queue_txt = queue_txt
        self.evaluator_path = evaluator_path
        self.max_iterations = max_iterations

        self.worktree_manager = GitWorktreeManager(repo_root)
        self.iteration = 0
        self.stats = {
            "total_iterations": 0,
            "successful_iterations": 0,
            "failed_iterations": 0,
            "commits_made": 0
        }

    def load_tasks(self) -> List[Task]:
        """Load tasks from queue.txt.

        Returns:
            List of tasks
        """
        tasks = []
        with open(self.queue_txt, 'r') as f:
            for line in f:
                task = Task.from_line(line)
                if task:
                    tasks.append(task)

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 99))

        return tasks

    def remove_task_from_queue(self, task: Task) -> None:
        """Remove completed task from queue.

        Args:
            task: Task to remove
        """
        lines = []
        with open(self.queue_txt, 'r') as f:
            for line in f:
                # Skip the completed task
                if task.description in line and task.module_path in line:
                    continue
                lines.append(line)

        with open(self.queue_txt, 'w') as f:
            f.writelines(lines)

    def append_learning(
        self,
        task: Task,
        result: IterationResult
    ) -> None:
        """Append learning to learnings.md.

        Args:
            task: Task that was attempted
            result: Result of the attempt
        """
        with open(self.learnings_md, 'a') as f:
            f.write(f"\n### {datetime.now().isoformat()} - Iteration {self.iteration} - {task.module_path}\n\n")
            f.write(f"**Outcome**: {'FAILED' if not result.success else 'PASSED'}\n\n")
            f.write(f"**Exit Code**: {result.exit_code}\n\n")
            f.write(f"**What Was Attempted**: {task.description}\n\n")
            f.write(f"**What Happened**: {result.error or 'Changes committed successfully'}\n\n")

            if not result.success:
                f.write(f"**Root Cause Hypothesis**: Analysis needed\n\n")
                f.write(f"**What to Try Instead**: Different approach on next attempt\n\n")

    def run_iteration(self, worktree: Path, task: Task) -> IterationResult:
        """Run a single iteration.

        Args:
            worktree: Path to worktree for execution
            task: Task to execute

        Returns:
            IterationResult
        """
        start_time = datetime.now()
        logger.info(f"Iteration {self.iteration}: {task.description}")
        logger.info(f"  Module: {task.module_path}")
        logger.info(f"  Mode: {task.mode}")

        try:
            # Read program.md and learnings.md for context
            program_context = self.program_md.read_text()
            learnings_context = self.learnings_md.read_text()

            # Build prompt for Claude Code
            prompt = f"""You are an autonomous refactoring agent for Project Chimera.

CONSTRAINTS (from program.md):
{program_context[:2000]}  # Truncated for practical use

HISTORICAL CONTEXT (from learnings.md):
{learnings_context[-1000]}  # Recent learnings

CURRENT TASK:
{task.description}
Module: {task.module_path}
Mode: {task.mode}

Execute the task following the constraints above. Remember:
- DO NOT delete assertions or tests
- DO NOT reduce coverage
- DO NOT ignore pytest exit codes
- Run pytest to verify changes
"""

            # Run Claude Code
            result = subprocess.run(
                ["claude", "-p", prompt],
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Claude Code failed: {result.stderr}")
                return IterationResult(
                    iteration=self.iteration,
                    task=task,
                    success=False,
                    exit_code=1,
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    error=f"Claude Code failed: {result.stderr[:500]}"
                )

            # Run the evaluator
            logger.info("Running evaluator...")
            eval_result = subprocess.run(
                [str(self.evaluator_path), "--test-path", f"{worktree}/{task.test_path}"],
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            if eval_result.returncode == 0:
                # Success - commit changes
                commit_msg = f"AutoQA: {task.description} ({task.module_path})"
                committed = self.worktree_manager.commit_changes(worktree, commit_msg)

                self.stats["successful_iterations"] += 1
                if committed:
                    self.stats["commits_made"] += 1

                return IterationResult(
                    iteration=self.iteration,
                    task=task,
                    success=True,
                    exit_code=0,
                    duration_seconds=duration,
                    committed=committed
                )
            else:
                # Failure - reset worktree
                logger.warning(f"Evaluator failed with exit code {eval_result.returncode}")
                logger.warning(f"  stderr: {eval_result.stderr[:500]}")
                self.worktree_manager.reset_worktree(worktree)

                self.stats["failed_iterations"] += 1

                return IterationResult(
                    iteration=self.iteration,
                    task=task,
                    success=False,
                    exit_code=eval_result.returncode,
                    duration_seconds=duration,
                    error=eval_result.stderr[:500]
                )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout: {e}")
            self.worktree_manager.reset_worktree(worktree)
            return IterationResult(
                iteration=self.iteration,
                task=task,
                success=False,
                exit_code=1,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error="Timeout"
            )
        except Exception as e:
            logger.error(f"Exception: {e}")
            self.worktree_manager.reset_worktree(worktree)
            return IterationResult(
                iteration=self.iteration,
                task=task,
                success=False,
                exit_code=1,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )

    def run(self) -> None:
        """Run the autonomous refactoring loop."""
        logger.info("=== Autonomous Refactoring Loop Started ===")
        logger.info(f"Repo Root: {self.repo_root}")
        logger.info(f"Program MD: {self.program_md}")
        logger.info(f"Learnings MD: {self.learnings_md}")
        logger.info(f"Queue: {self.queue_txt}")
        logger.info(f"Max Iterations: {self.max_iterations or 'unlimited'}")

        # Create initial worktree
        worktree = self.worktree_manager.create_worktree()

        try:
            while True:
                # Check max iterations
                if self.max_iterations and self.iteration >= self.max_iterations:
                    logger.info(f"Reached max iterations: {self.max_iterations}")
                    break

                # Load tasks
                tasks = self.load_tasks()
                if not tasks:
                    logger.info("No more tasks in queue")
                    break

                # Get next task
                task = tasks[0]
                self.iteration += 1

                # Run iteration
                result = self.run_iteration(worktree, task)

                # Record learning
                self.append_learning(task, result)

                # Update stats
                self.stats["total_iterations"] = self.iteration

                # Log result
                logger.info(
                    f"Iteration {self.iteration} complete: "
                    f"{'SUCCESS' if result.success else 'FAILED'} "
                    f"({result.duration_seconds:.1f}s)"
                )

                # If successful, remove task from queue
                if result.success:
                    self.remove_task_from_queue(task)
                    # Recreate worktree for clean slate
                    self.worktree_manager.remove_worktree(worktree)
                    worktree = self.worktree_manager.create_worktree()

        finally:
            # Cleanup worktree
            if worktree and worktree.exists():
                self.worktree_manager.remove_worktree(worktree)

        # Log final stats
        logger.info("=== Autonomous Refactoring Loop Complete ===")
        logger.info(f"Total Iterations: {self.stats['total_iterations']}")
        logger.info(f"Successful: {self.stats['successful_iterations']}")
        logger.info(f"Failed: {self.stats['failed_iterations']}")
        logger.info(f"Commits Made: {self.stats['commits_made']}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Refactoring Orchestrator for Project Chimera"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum iterations before exit (default: unlimited)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository root"
    )
    parser.add_argument(
        "--worktree-path",
        type=Path,
        default=None,
        help="Base path for worktrees (default: .claude/autonomous-refactor/worktrees)"
    )

    args = parser.parse_args()

    # Set paths from environment or defaults
    repo_root = args.repo_root
    program_md = Path(os.environ.get(
        "CHIMERA_PROGRAM_MD",
        repo_root / ".claude/autonomous-refactor/program.md"
    ))
    learnings_md = Path(os.environ.get(
        "CHIMERA_LEARNINGS_MD",
        repo_root / ".claude/autonomous-refactor/learnings.md"
    ))
    queue_txt = Path(os.environ.get(
        "CHIMERA_QUEUE_TXT",
        repo_root / ".claude/autonomous-refactor/queue.txt"
    ))
    evaluator_path = Path(os.environ.get(
        "CHIMERA_EVALUATOR",
        repo_root / "platform/quality-gate/evaluate.sh"
    ))

    # Create orchestrator
    orchestrator = RalphOrchestrator(
        repo_root=repo_root,
        program_md=program_md,
        learnings_md=learnings_md,
        queue_txt=queue_txt,
        evaluator_path=evaluator_path,
        max_iterations=args.max_iterations
    )

    # Run loop
    orchestrator.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
