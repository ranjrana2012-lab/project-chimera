"""Ralph Engine - Persistent execution loop with Flow-Next architecture.

The Ralph Engine implements a non-blocking execution model with:
- Persistent execution until promise (success) or backstop (max retries)
- Flow-Next architecture: load_fresh_context() for each execution
- External state persistence (STATE.md updates)
- Graceful degradation with BackstopExceededError
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)


class BackstopExceededError(Exception):
    """Raised when Ralph Engine exceeds maximum retry backstop."""

    def __init__(self, task_id: str, max_retries: int, last_error: Optional[str] = None):
        """Initialize backstop exceeded error.

        Args:
            task_id: ID of the failed task
            max_retries: Maximum retry limit that was exceeded
            last_error: Optional last error message
        """
        self.task_id = task_id
        self.max_retries = max_retries
        self.last_error = last_error
        message = f"Task {task_id} exceeded backstop of {max_retries} retries"
        if last_error:
            message += f". Last error: {last_error}"
        super().__init__(message)


@dataclass
class Task:
    """Represents a task to be executed by the Ralph Engine."""

    id: str
    requirements: List[str]
    context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Execution context for a task (Flow-Next: fresh each time)."""

    task_id: str
    timestamp: datetime
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """Result of task execution."""

    success: bool
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RalphEngine:
    """Ralph Engine - Persistent execution loop with backstop.

    Implements non-blocking execution model:
    - Executes task until promise (success) or backstop (max retries)
    - Flow-Next: loads fresh context for each execution
    - External state persistence (STATE.md updates)
    - Graceful degradation with BackstopExceededError
    """

    def __init__(self, max_retries: int = 5, state_file: str = "STATE.md"):
        """Initialize Ralph Engine.

        Args:
            max_retries: Maximum retry backstop (default: 5)
            state_file: Path to external state file (default: STATE.md)
        """
        settings = get_settings()
        self.max_retries = max_retries
        self.state_file = state_file
        self.retry_count = 0
        self._state: Dict[str, Any] = {}

    async def execute_until_promise(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None
    ) -> Result:
        """Execute task until promise (success) or backstop (max retries).

        Non-blocking execution loop that:
        1. Loads fresh context (Flow-Next architecture)
        2. Executes task with retry logic
        3. Verifies result against promise
        4. Updates external state (STATE.md)
        5. Raises BackstopExceededError if backstop hit

        Args:
            task: Task to execute
            context: Optional initial context

        Returns:
            Result: Execution result with success status

        Raises:
            BackstopExceededError: If max retries exceeded
        """
        self.retry_count = 0
        execution_context = context or {}

        while self.retry_count < self.max_retries:
            try:
                # Flow-Next: load fresh context for each execution
                fresh_context = await self.load_fresh_context(task, execution_context)

                # Execute task
                result = await self.execute_task(task, fresh_context)

                # Verify result against promise
                if await self.verify_result(task, result):
                    # Success: update state and return
                    await self.update_state(task, result)
                    return result

                # Failure: retry with backoff
                self.retry_count += 1
                await self.log_failure(task, result, self.retry_count)

                # Exponential backoff (optional)
                await asyncio.sleep(0.1 * (2 ** self.retry_count))

            except Exception as e:
                # Exception during execution
                self.retry_count += 1
                await self.log_error(task, e, self.retry_count)

                # Exponential backoff
                await asyncio.sleep(0.1 * (2 ** self.retry_count))

        # Backstop exceeded
        raise BackstopExceededError(
            task_id=task.id,
            max_retries=self.max_retries,
            last_error=execution_context.get("last_error")
        )

    async def load_fresh_context(self, task: Task, existing_context: Dict[str, Any]) -> Context:
        """Load fresh context for task execution (Flow-Next architecture).

        Flow-Next principle: each execution loads fresh context from external
        state (STATE.md) rather than carrying state through memory.

        Args:
            task: Task being executed
            existing_context: Existing context from previous execution

        Returns:
            Context: Fresh context for execution
        """
        # Load external state
        external_state = await self._load_external_state()

        # Create fresh context
        fresh_context = Context(
            task_id=task.id,
            timestamp=datetime.utcnow(),
            state=external_state,
            metadata={
                "retry_count": self.retry_count,
                "requirements": task.requirements
            }
        )

        logger.debug(
            f"Loaded fresh context for task {task.id}: "
            f"{len(external_state)} state entries"
        )

        return fresh_context

    async def execute_task(self, task: Task, context: Context) -> Result:
        """Execute task with given context.

        Base implementation - override in subclasses for specific execution logic.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Result: Execution result
        """
        # Placeholder: subclasses should implement actual execution logic
        logger.info(f"Executing task {task.id} with context {context.task_id}")

        # Simulate execution
        return Result(
            success=True,
            data={"message": "Task executed"}
        )

    async def verify_result(self, task: Task, result: Result) -> bool:
        """Verify result against task promise.

        Args:
            task: Task that was executed
            result: Result to verify

        Returns:
            bool: True if result satisfies promise, False otherwise
        """
        # Basic verification: result must be successful
        if not result.success:
            return False

        # Additional verification can be added here
        # (e.g., check result.data against task.requirements)

        return True

    async def update_state(self, task: Task, result: Result) -> None:
        """Update external state (STATE.md) with result.

        Args:
            task: Task that was executed
            result: Result to persist
        """
        # Update internal state
        self._state[task.id] = {
            "result": result.data,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.success
        }

        # Persist to external state file
        await self._persist_external_state()

        logger.info(f"Updated state for task {task.id}")

    async def log_failure(self, task: Task, result: Result, retry_count: int) -> None:
        """Log execution failure for retry.

        Args:
            task: Task that failed
            result: Failed result
            retry_count: Current retry count
        """
        logger.warning(
            f"Task {task.id} failed (retry {retry_count}/{self.max_retries}): "
            f"{result.error}"
        )

    async def log_error(self, task: Task, error: Exception, retry_count: int) -> None:
        """Log execution exception for retry.

        Args:
            task: Task that raised exception
            error: Exception raised
            retry_count: Current retry count
        """
        logger.error(
            f"Task {task.id} raised exception (retry {retry_count}/{self.max_retries}): "
            f"{type(error).__name__}: {error}"
        )

    async def _load_external_state(self) -> Dict[str, Any]:
        """Load external state from STATE.md file.

        Returns:
            Dict[str, Any]: External state dictionary
        """
        try:
            # In production, this would load from actual STATE.md file
            # For now, return internal state
            return self._state.copy()
        except Exception as e:
            logger.warning(f"Failed to load external state: {e}")
            return {}

    async def _persist_external_state(self) -> None:
        """Persist internal state to external STATE.md file."""
        try:
            # In production, this would write to actual STATE.md file
            # For now, just log
            logger.debug(f"Persisted state with {len(self._state)} entries")
        except Exception as e:
            logger.error(f"Failed to persist external state: {e}")
