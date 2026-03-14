"""
Scene Execution Engine for Director Agent

Handles the execution of show scenes with multi-agent coordination,
real-time adaptation, and safety controls.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum

from show_definition import (
    ShowDefinition,
    Scene,
    AgentAction,
    WaitAction,
    ParallelActions,
    ConditionalAction,
    AgentType,
    ActionType,
)

logger = logging.getLogger(__name__)


class ExecutionState(str, Enum):
    """Scene execution state."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentClient:
    """Client for communicating with specialized agents."""

    def __init__(self, agent_type: AgentType, base_url: str):
        self.agent_type = agent_type
        self.base_url = base_url.rstrip('/')
        self.timeout = 10.0

    async def call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP call to agent endpoint."""
        import httpx

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Calling {self.agent_type} agent: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {self.agent_type} agent")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.agent_type} agent: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {self.agent_type} agent: {e}")
            raise


class ExecutionEngine:
    """Executes show scenes with multi-agent coordination."""

    # Agent endpoint mappings
    AGENT_ENDPOINTS = {
        AgentType.BSL: "/api/v1/translate",
        AgentType.CAPTIONING: "/api/v1/transcribe",
        AgentType.LIGHTING: "/api/lighting",
        AgentType.SOUND: "/v1/audio/play",
        AgentType.MUSIC: "/v1/audio/play",
        AgentType.SENTIMENT: "/api/analyze",
        AgentType.SCENESPEAK: "/api/generate",
    }

    # Agent base URLs (default ports)
    AGENT_BASE_URLS = {
        AgentType.BSL: "http://localhost:8003",
        AgentType.CAPTIONING: "http://localhost:8002",
        AgentType.LIGHTING: "http://localhost:8005",
        AgentType.SOUND: "http://localhost:8005",
        AgentType.MUSIC: "http://localhost:8005",
        AgentType.SENTIMENT: "http://localhost:8004",
        AgentType.SCENESPEAK: "http://localhost:8001",
    }

    def __init__(self):
        """Initialize execution engine."""
        self.state = ExecutionState.IDLE
        self.current_scene: Optional[Scene] = None
        self.current_scene_index = 0
        self.execution_log: List[Dict[str, Any]] = []
        self.agent_clients: Dict[AgentType, AgentClient] = {}
        self._stop_requested = False
        self._pause_requested = False
        self._human_approval_required = False

        # Initialize agent clients
        for agent_type, base_url in self.AGENT_BASE_URLS.items():
            self.agent_clients[agent_type] = AgentClient(agent_type, base_url)

    def set_agent_base_url(self, agent_type: AgentType, base_url: str) -> None:
        """Override default agent base URL."""
        self.agent_clients[agent_type] = AgentClient(agent_type, base_url)

    async def execute_show(
        self,
        show: ShowDefinition,
        start_scene: int = 0,
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Execute an entire show from start to finish.

        Args:
            show: Show definition to execute
            start_scene: Scene index to start from (for resume)
            require_approval: Require human approval between scenes

        Returns:
            Execution summary
        """
        self.state = ExecutionState.RUNNING
        self.current_scene_index = start_scene
        self._human_approval_required = require_approval

        start_time = datetime.now()
        scenes_executed = 0
        scenes_failed = 0

        logger.info(f"Starting show execution: {show.metadata.title}")

        try:
            for i in range(start_scene, len(show.scenes)):
                if self._stop_requested:
                    logger.info("Stop requested, ending show")
                    break

                # Wait for approval if required
                if require_approval and i > start_scene:
                    logger.info(f"Waiting for approval to start scene {i + 1}")
                    await self._wait_for_approval()

                if self._pause_requested:
                    await self._handle_pause()

                scene = show.scenes[i]
                self.current_scene = scene
                self.current_scene_index = i

                logger.info(f"Executing scene {i + 1}/{len(show.scenes)}: {scene.title}")

                # Execute scene
                result = await self.execute_scene(scene, show.metadata)

                if result["status"] == "completed":
                    scenes_executed += 1
                else:
                    scenes_failed += 1

                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "scene_id": scene.id,
                    "scene_index": i,
                    "result": result
                })

            self.state = ExecutionState.COMPLETED
            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "completed",
                "duration_sec": duration,
                "scenes_executed": scenes_executed,
                "scenes_failed": scenes_failed,
                "total_scenes": len(show.scenes),
                "execution_log": self.execution_log
            }

        except Exception as e:
            logger.error(f"Show execution failed: {e}")
            self.state = ExecutionState.FAILED
            raise

    async def execute_scene(
        self,
        scene: Scene,
        metadata: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single scene with all its actions.

        Args:
            scene: Scene definition
            metadata: Show metadata
            context: Execution context (sentiment, variables, etc.)

        Returns:
            Scene execution result
        """
        scene_start = datetime.now()
        context = context or {}
        context["scene_id"] = scene.id
        context["scene_title"] = scene.title

        actions_completed = 0
        actions_failed = 0
        action_results = []

        logger.info(f"Starting scene: {scene.title}")

        try:
            for action in scene.actions:
                if self._stop_requested:
                    logger.info("Stop requested during scene")
                    break

                if self._pause_requested:
                    await self._handle_pause()

                # Execute action
                result = await self.execute_action(action, context)
                action_results.append(result)

                if result["success"]:
                    actions_completed += 1
                else:
                    actions_failed += 1
                    if not result.get("continue_on_failure", False):
                        logger.error(f"Action failed and continue_on_failure=False")
                        break

            duration = (datetime.now() - scene_start).total_seconds()

            return {
                "status": "completed",
                "duration_sec": duration,
                "actions_completed": actions_completed,
                "actions_failed": actions_failed,
                "action_results": action_results
            }

        except Exception as e:
            logger.error(f"Scene execution failed: {e}")
            duration = (datetime.now() - scene_start).total_seconds()

            return {
                "status": "failed",
                "error": str(e),
                "duration_sec": duration,
                "actions_completed": actions_completed,
                "actions_failed": actions_failed + 1,
                "action_results": action_results
            }

    async def execute_action(
        self,
        action: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single action (can be AgentAction, WaitAction, etc.).

        Args:
            action: Action to execute
            context: Execution context

        Returns:
            Action execution result
        """
        action_start = datetime.now()

        try:
            # Handle different action types
            if isinstance(action, WaitAction):
                return await self._execute_wait(action)
            elif isinstance(action, AgentAction):
                return await self._execute_agent_action(action, context)
            elif isinstance(action, ParallelActions):
                return await self._execute_parallel_actions(action, context)
            elif isinstance(action, ConditionalAction):
                return await self._execute_conditional_action(action, context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {type(action)}",
                    "duration_ms": 0
                }

        except Exception as e:
            duration_ms = int((datetime.now() - action_start).total_seconds() * 1000)
            logger.error(f"Action execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms,
                "continue_on_failure": getattr(action, 'continue_on_failure', False)
            }

    async def _execute_wait(self, action: WaitAction) -> Dict[str, Any]:
        """Execute a wait/delay action."""
        logger.debug(f"Waiting for {action.duration_ms}ms")
        await asyncio.sleep(action.duration_ms / 1000.0)

        return {
            "success": True,
            "action_type": "wait",
            "duration_ms": action.duration_ms
        }

    async def _execute_agent_action(
        self,
        action: AgentAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an agent action."""
        client = self.agent_clients[action.agent]
        endpoint = self.AGENT_ENDPOINTS[action.agent]

        # Prepare parameters with context substitution
        params = self._substitute_context(action.parameters, context)

        logger.info(f"Executing {action.agent} action: {action.action}")

        try:
            result = await client.call(endpoint, params)
            duration_ms = result.get("processing_time_ms", 0)

            return {
                "success": True,
                "agent": action.agent,
                "action": action.action,
                "result": result,
                "duration_ms": duration_ms
            }

        except Exception as e:
            # Retry logic
            for attempt in range(action.retry_count):
                logger.warning(f"Retry {attempt + 1}/{action.retry_count} for {action.agent} action")
                await asyncio.sleep(1.0 * (attempt + 1))

                try:
                    result = await client.call(endpoint, params)
                    return {
                        "success": True,
                        "agent": action.agent,
                        "action": action.action,
                        "result": result,
                        "retries": attempt + 1
                    }
                except Exception as retry_error:
                    logger.error(f"Retry {attempt + 1} failed: {retry_error}")

            return {
                "success": False,
                "agent": action.agent,
                "action": action.action,
                "error": str(e),
                "continue_on_failure": action.continue_on_failure
            }

    async def _execute_parallel_actions(
        self,
        action: ParallelActions,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute multiple actions in parallel."""
        logger.info(f"Executing {len(action.actions)} actions in parallel")

        tasks = [
            self.execute_action(sub_action, context)
            for sub_action in action.actions
        ]

        if action.wait_for_all:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        success_count = 0
        failed_count = 0
        processed_results = []

        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                processed_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1

        return {
            "success": failed_count == 0,
            "action_type": "parallel",
            "results": processed_results,
            "success_count": success_count,
            "failed_count": failed_count
        }

    async def _execute_conditional_action(
        self,
        action: ConditionalAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute conditional action based on context."""
        condition_met = self._evaluate_condition(action.condition, context)

        logger.info(f"Conditional action: condition_met={condition_met}")

        actions_to_execute = action.then_actions if condition_met else (action.else_actions or [])

        results = []
        for sub_action in actions_to_execute:
            result = await self.execute_action(sub_action, context)
            results.append(result)

        return {
            "success": True,
            "action_type": "conditional",
            "condition_met": condition_met,
            "results": results
        }

    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression against context."""
        condition_type = condition.get("type")

        if condition_type == "sentiment":
            # Check sentiment threshold
            sentiment = context.get("sentiment", 0.5)
            operator = condition.get("operator", ">")
            threshold = condition.get("threshold", 0.7)

            if operator == ">":
                return sentiment > threshold
            elif operator == "<":
                return sentiment < threshold
            elif operator == ">=":
                return sentiment >= threshold
            elif operator == "<=":
                return sentiment <= threshold
            elif operator == "==":
                return sentiment == threshold

        elif condition_type == "variable":
            # Check variable equality
            var_name = condition.get("variable")
            expected_value = condition.get("value")
            return context.get(var_name) == expected_value

        return False

    def _substitute_context(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Replace context variables in parameters."""
        substituted = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract variable name
                var_name = value[2:-1]
                substituted[key] = context.get(var_name, value)
            else:
                substituted[key] = value

        return substituted

    async def _wait_for_approval(self) -> None:
        """Wait for human approval to proceed."""
        self._human_approval_required = True

        while self._human_approval_required:
            await asyncio.sleep(0.5)

            if self._stop_requested:
                break

    async def _handle_pause(self) -> None:
        """Handle pause request."""
        logger.info("Show paused")

        while self._pause_requested:
            await asyncio.sleep(0.5)

            if self._stop_requested:
                break

        logger.info("Show resumed")

    def request_stop(self) -> None:
        """Request show to stop (emergency stop)."""
        self._stop_requested = True
        self.state = ExecutionState.STOPPED
        logger.warning("Stop requested")

    def request_pause(self) -> None:
        """Request show to pause."""
        self._pause_requested = True
        self.state = ExecutionState.PAUSED
        logger.info("Pause requested")

    def request_resume(self) -> None:
        """Request show to resume from pause."""
        self._pause_requested = False
        self.state = ExecutionState.RUNNING
        logger.info("Resume requested")

    def grant_approval(self) -> None:
        """Grant human approval to proceed."""
        self._human_approval_required = False
        logger.info("Human approval granted")

    def get_state(self) -> Dict[str, Any]:
        """Get current execution state."""
        return {
            "state": self.state.value,
            "current_scene": self.current_scene.model_dump() if self.current_scene else None,
            "current_scene_index": self.current_scene_index,
            "stop_requested": self._stop_requested,
            "pause_requested": self._pause_requested,
            "awaiting_approval": self._human_approval_required
        }


__all__ = [
    "ExecutionState",
    "ExecutionEngine",
]
