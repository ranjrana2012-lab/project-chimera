"""Lighting cue execution with timing and sequencing."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..models.request import CueRequest
from ..models.response import CueResponse

logger = logging.getLogger(__name__)


class CueState(str, Enum):
    """Cue execution states."""
    PENDING = "pending"
    DELAYED = "delayed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class CueDefinition:
    """Defines a lighting cue."""
    cue_number: str
    cue_list: str
    preset_name: Optional[str]
    values: Dict[int, int]
    fade_time: float
    delay_secs: float
    follow_on: bool
    description: str = ""
    auto_follow: Optional[str] = None  # Next cue number for auto-follow


@dataclass
class CueExecution:
    """Tracks a cue execution."""
    cue: CueDefinition
    state: CueState
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class CueList:
    """Manages a list of cues."""

    def __init__(self, name: str = "main"):
        """Initialize cue list.

        Args:
            name: Cue list identifier
        """
        self.name = name
        self.cues: Dict[str, CueDefinition] = {}
        self.execution_order: List[str] = []

    def add_cue(self, cue: CueDefinition) -> bool:
        """Add a cue to the list.

        Args:
            cue: Cue definition

        Returns:
            True if added successfully
        """
        if cue.cue_number in self.cues:
            logger.warning(f"Cue {cue.cue_number} already exists in list {self.name}")
            return False

        self.cues[cue.cue_number] = cue
        self.execution_order.append(cue.cue_number)
        logger.info(f"Added cue {cue.cue_number} to list {self.name}")
        return True

    def remove_cue(self, cue_number: str) -> bool:
        """Remove a cue from the list.

        Args:
            cue_number: Cue identifier

        Returns:
            True if removed
        """
        if cue_number in self.cues:
            del self.cues[cue_number]
            if cue_number in self.execution_order:
                self.execution_order.remove(cue_number)
            return True
        return False

    def get_cue(self, cue_number: str) -> Optional[CueDefinition]:
        """Get a cue definition.

        Args:
            cue_number: Cue identifier

        Returns:
            Cue definition or None
        """
        return self.cues.get(cue_number)

    def get_all_cues(self) -> Dict[str, CueDefinition]:
        """Get all cues.

        Returns:
            Dictionary of cues
        """
        return self.cues.copy()

    def get_next_cue(self, cue_number: str) -> Optional[CueDefinition]:
        """Get the next cue in execution order.

        Args:
            cue_number: Current cue number

        Returns:
            Next cue or None
        """
        try:
            index = self.execution_order.index(cue_number)
            if index + 1 < len(self.execution_order):
                next_number = self.execution_order[index + 1]
                return self.cues.get(next_number)
        except ValueError:
            pass
        return None

    def find_cue_by_number(self, number: float) -> Optional[CueDefinition]:
        """Find cue by numeric value.

        Args:
            number: Cue number

        Returns:
            Cue definition or None
        """
        return self.cues.get(str(number))


class CueExecutor:
    """Executes lighting cues with timing control."""

    def __init__(self):
        """Initialize cue executor."""
        self.cue_lists: Dict[str, CueList] = {}
        self.active_executions: Dict[str, CueExecution] = {}
        self.current_cue: Optional[str] = None
        self.execution_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._executor_task: Optional[asyncio.Task] = None
        self._apply_lighting_callback: Optional[Callable] = None

    def register_lighting_callback(self, callback: Callable) -> None:
        """Register callback for applying lighting values.

        Args:
            callback: Async function taking (values, fade_time)
        """
        self._apply_lighting_callback = callback

    def create_cue_list(self, name: str) -> CueList:
        """Create a new cue list.

        Args:
            name: Cue list identifier

        Returns:
            New CueList
        """
        cue_list = CueList(name)
        self.cue_lists[name] = cue_list
        return cue_list

    def get_cue_list(self, name: str) -> Optional[CueList]:
        """Get a cue list.

        Args:
            name: Cue list identifier

        Returns:
            CueList or None
        """
        return self.cue_lists.get(name)

    def add_cue(self, cue: CueDefinition, list_name: str = "main") -> bool:
        """Add a cue to a list.

        Args:
            cue: Cue definition
            list_name: Cue list name

        Returns:
            True if added successfully
        """
        if list_name not in self.cue_lists:
            self.cue_lists[list_name] = CueList(list_name)

        return self.cue_lists[list_name].add_cue(cue)

    async def execute_cue(
        self,
        cue_request: CueRequest,
        preset_values: Optional[Dict[int, int]] = None
    ) -> CueResponse:
        """Execute a lighting cue.

        Args:
            cue_request: Cue execution request
            preset_values: Optional preset values to use

        Returns:
            Cue execution response
        """
        cue_list = self.cue_lists.get(cue_request.cue_list)
        if not cue_list:
            return CueResponse(
                cue_number=cue_request.cue_number,
                executed=False,
                status="failed",
                error_message=f"Cue list '{cue_request.cue_list}' not found"
            )

        # Get or build cue definition
        cue = cue_list.get_cue(cue_request.cue_number)
        if not cue:
            # Create ad-hoc cue from request
            cue = CueDefinition(
                cue_number=cue_request.cue_number,
                cue_list=cue_request.cue_list,
                preset_name=cue_request.preset_name,
                values=cue_request.values or {},
                fade_time=cue_request.fade_time or 0.0,
                delay_secs=cue_request.delay_secs,
                follow_on=cue_request.follow_on
            )

        # Create execution record
        execution = CueExecution(
            cue=cue,
            state=CueState.PENDING,
            start_time=datetime.now()
        )

        async with self.execution_lock:
            try:
                # Handle delay
                if cue.delay_secs > 0:
                    execution.state = CueState.DELAYED
                    logger.info(f"Cue {cue.cue_number} delayed for {cue.delay_secs}s")
                    await asyncio.sleep(cue.delay_secs)

                # Get values to apply
                values_to_apply = cue.values.copy()
                if preset_values:
                    values_to_apply.update(preset_values)

                # Execute fade
                execution.state = CueState.RUNNING
                self.current_cue = cue.cue_number
                self.active_executions[cue.cue_number] = execution

                fade_time = cue_request.fade_time if cue_request.fade_time is not None else cue.fade_time

                if self._apply_lighting_callback:
                    await self._apply_lighting_callback(values_to_apply, fade_time)
                else:
                    logger.warning("No lighting callback registered")
                    await asyncio.sleep(fade_time)  # Simulate fade

                execution.state = CueState.COMPLETED
                execution.end_time = datetime.now()

                response = CueResponse(
                    cue_number=cue.cue_number,
                    executed=True,
                    status="completed",
                    preset_used=cue.preset_name,
                    timing={
                        "delay": cue.delay_secs,
                        "fade": fade_time,
                        "total": cue.delay_secs + fade_time
                    }
                )

                # Handle follow-on
                if cue.follow_on or cue_request.follow_on:
                    next_cue = cue_list.get_next_cue(cue.cue_number)
                    if next_cue:
                        response.follow_triggered = True
                        # Schedule next cue
                        asyncio.create_task(self._execute_follow_cue(
                            cue_request.cue_list,
                            next_cue.cue_number
                        ))

                logger.info(f"Cue {cue.cue_number} completed")
                return response

            except asyncio.CancelledError:
                execution.state = CueState.STOPPED
                return CueResponse(
                    cue_number=cue.cue_number,
                    executed=False,
                    status="stopped",
                    error_message="Cue execution cancelled"
                )
            except Exception as e:
                execution.state = CueState.FAILED
                execution.error_message = str(e)
                logger.error(f"Cue {cue.cue_number} failed: {e}")
                return CueResponse(
                    cue_number=cue.cue_number,
                    executed=False,
                    status="failed",
                    error_message=str(e)
                )

    async def _execute_follow_cue(
        self,
        cue_list_name: str,
        cue_number: str
    ) -> None:
        """Execute a follow-on cue.

        Args:
            cue_list_name: Cue list name
            cue_number: Cue number to execute
        """
        logger.info(f"Executing follow cue {cue_number}")
        await self.execute_cue(CueRequest(
            cue_number=cue_number,
            cue_list=cue_list_name
        ))

    async def execute_cue_list(
        self,
        list_name: str,
        start_from: Optional[str] = None
    ) -> List[CueResponse]:
        """Execute an entire cue list sequentially.

        Args:
            list_name: Cue list to execute
            start_from: Optional starting cue number

        Returns:
            List of cue responses
        """
        cue_list = self.cue_lists.get(list_name)
        if not cue_list:
            return [CueResponse(
                cue_number="0",
                executed=False,
                status="failed",
                error_message=f"Cue list '{list_name}' not found"
            )]

        responses = []
        start_index = 0

        if start_from:
            try:
                start_index = cue_list.execution_order.index(start_from)
            except ValueError:
                logger.warning(f"Start cue {start_from} not found")

        for cue_number in cue_list.execution_order[start_index:]:
            response = await self.execute_cue(CueRequest(
                cue_number=cue_number,
                cue_list=list_name
            ))
            responses.append(response)

            # Stop if failed
            if not response.executed and response.status != "completed":
                break

        return responses

    async def stop_all(self) -> None:
        """Stop all cue executions."""
        self._stop_event.set()
        for execution in self.active_executions.values():
            if execution.state in [CueState.PENDING, CueState.DELAYED, CueState.RUNNING]:
                execution.state = CueState.STOPPED
        logger.info("All cue executions stopped")

    async def resume(self) -> None:
        """Resume cue execution."""
        self._stop_event.clear()

    def get_current_cue(self) -> Optional[str]:
        """Get currently executing cue number.

        Returns:
            Cue number or None
        """
        return self.current_cue

    def get_execution_state(self, cue_number: str) -> Optional[CueState]:
        """Get execution state for a cue.

        Args:
            cue_number: Cue number

        Returns:
            Cue state or None
        """
        execution = self.active_executions.get(cue_number)
        return execution.state if execution else None

    def get_active_executions(self) -> Dict[str, CueExecution]:
        """Get all active cue executions.

        Returns:
            Dictionary of active executions
        """
        return {
            k: v for k, v in self.active_executions.items()
            if v.state in [CueState.PENDING, CueState.DELAYED, CueState.RUNNING]
        }

    def clear_history(self, older_than_secs: float = 3600) -> int:
        """Clear old execution history.

        Args:
            older_than_secs: Clear executions older than this

        Returns:
            Number of executions cleared
        """
        cutoff = datetime.now().timestamp() - older_than_secs
        to_remove = []

        for cue_number, execution in self.active_executions.items():
            if execution.state == CueState.COMPLETED:
                if execution.end_time and execution.end_time.timestamp() < cutoff:
                    to_remove.append(cue_number)

        for cue_number in to_remove:
            del self.active_executions[cue_number]

        return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self.active_executions)
        by_state = {}
        for state in CueState:
            by_state[state.value] = sum(
                1 for e in self.active_executions.values()
                if e.state == state
            )

        return {
            "total_executions": total,
            "by_state": by_state,
            "current_cue": self.current_cue,
            "cue_lists": list(self.cue_lists.keys())
        }
