"""Main FastAPI application for autonomous-agent service."""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest

from config import get_settings
from models import (
    HealthResponse,
    TaskRequest,
    TaskResponse,
    StatusResponse,
    ExecuteResponse,
)
from gsd_orchestrator import GSDOrchestrator, Requirements, Plan, Results
from ralph_engine import RalphEngine, Task, Result
from flow_next import FlowNextManager
from metrics import (
    init_service_info,
    record_task_execution,
    record_task_duration,
    increment_active_tasks,
    decrement_active_tasks,
    record_gsd_phase,
)
from tracing import setup_telemetry, instrument_fastapi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Autonomous Agent Service",
    description="Autonomous agent orchestration with Ralph Mode and GSD",
    version=settings.service_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize telemetry
try:
    tracer = setup_telemetry(
        service_name=settings.service_name,
        otlp_endpoint=settings.otlp_endpoint
    )
    app = instrument_fastapi(app, settings.service_name)
    logger.info("OpenTelemetry instrumentation enabled")
except Exception as e:
    logger.warning(f"Failed to initialize telemetry: {e}")
    tracer = None

# Initialize metrics
try:
    init_service_info(
        service_name=settings.service_name,
        version=settings.service_version
    )
    logger.info("Prometheus metrics initialized")
except Exception as e:
    logger.warning(f"Failed to initialize metrics: {e}")

# Initialize orchestrator and managers
orchestrator = GSDOrchestrator()
flow_manager = FlowNextManager(state_dir=Path(settings.state_dir))
ralph_engine = RalphEngine(
    max_retries=settings.max_retries,
    state_file=settings.state_file
)

# In-memory task storage (in production, use a database)
tasks: Dict[str, Dict] = {}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current autonomous agent status."""
    # Read from STATE.md
    try:
        state_content = flow_manager.read_state()

        # Parse retry count from state
        retry_count = 0
        if "retry_count" in state_content:
            for line in state_content.split("\n"):
                if "retry_count" in line:
                    try:
                        retry_count = int(line.split(":")[-1].strip())
                    except (ValueError, IndexError):
                        pass

        # Parse current task
        current_task = None
        if "current_task" in state_content:
            for line in state_content.split("\n"):
                if "current_task" in line:
                    current_task = line.split(":", 1)[-1].strip()
                    break

        return StatusResponse(
            current_task=current_task,
            completed_tasks=[],
            pending_tasks=[task_id for task_id, task in tasks.items() if task.get("status") == "pending"],
            retry_count=retry_count,
            last_updated=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error reading status: {e}")
        return StatusResponse(
            retry_count=0,
            last_updated=datetime.utcnow().isoformat()
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


async def execute_task_pipeline(task_id: str, request: TaskRequest) -> None:
    """Execute task using GSD Discuss→Plan→Execute pipeline with Ralph Mode.

    This function runs in the background and implements:
    1. GSD Discuss Phase: Extract requirements
    2. GSD Plan Phase: Create implementation plan
    3. GSD Execute Phase: Execute with Ralph Mode (persistent retries)
    4. Update external state (STATE.md) using Flow-Next
    """
    try:
        logger.info(f"Starting task execution pipeline for {task_id}")
        increment_active_tasks()

        # Update task status
        tasks[task_id]["status"] = "in_progress"
        tasks[task_id]["phases_completed"] = []

        # Phase 1: Discuss (extract requirements)
        discuss_start = datetime.utcnow()
        with tracer.start_as_current_span("gsd_discuss_phase") if tracer else asyncio.sleep(0):
            requirements = orchestrator.discuss_phase(request.user_request)

            # Write requirements to state
            orchestrator.write_requirements(
                requirements,
                settings.requirements_file
            )

            # Update Flow-Next session
            session = flow_manager.create_fresh_session()
            session.requirements = f"""# Requirements

## Goal
{requirements.goal}

## Constraints
"""
            for constraint in requirements.constraints:
                session.requirements += f"- {constraint}\n"

            session.requirements += "\n## Acceptance Criteria\n"
            for criteria in requirements.acceptance_criteria:
                session.requirements += f"- {criteria}\n"

            session.requirements += f"\n*Generated: {requirements.timestamp}*\n"
            flow_manager.save_and_reset(session)

        discuss_duration = (datetime.utcnow() - discuss_start).total_seconds()
        record_gsd_phase("discuss", discuss_duration)
        tasks[task_id]["phases_completed"].append("discuss")
        tasks[task_id]["requirements"] = {
            "goal": requirements.goal,
            "constraints": requirements.constraints,
            "acceptance_criteria": requirements.acceptance_criteria
        }
        logger.info(f"Discuss phase completed in {discuss_duration:.2f}s")

        # Phase 2: Plan (create implementation plan)
        plan_start = datetime.utcnow()
        with tracer.start_as_current_span("gsd_plan_phase") if tracer else asyncio.sleep(0):
            plan = orchestrator.plan_phase(requirements)

            # Write plan to state
            orchestrator.write_plan(plan, settings.plan_file)

            # Update Flow-Next session
            session = flow_manager.create_fresh_session()
            session.plan = f"""# Implementation Plan

## Overview
- Total Tasks: {len(plan.tasks)}
- Estimated Hours: {plan.estimated_hours}

## Tasks
"""
            for task in plan.tasks:
                deps = ", ".join(task.dependencies) if task.dependencies else "None"
                session.plan += f"""
### Task {task.id}: {task.description}
- Status: {task.status}
- Dependencies: {deps}
"""

            session.plan += f"\n*Generated: {plan.timestamp}*\n"
            flow_manager.save_and_reset(session)

        plan_duration = (datetime.utcnow() - plan_start).total_seconds()
        record_gsd_phase("plan", plan_duration)
        tasks[task_id]["phases_completed"].append("plan")
        tasks[task_id]["plan_tasks"] = [task.description for task in plan.tasks]
        logger.info(f"Plan phase completed in {plan_duration:.2f}s")

        # Phase 3: Execute with Ralph Mode (persistent retries)
        execute_start = datetime.utcnow()
        with tracer.start_as_current_span("gsd_execute_phase") if tracer else asyncio.sleep(0):
            # Create Ralph Engine task
            ralph_task = Task(
                id=task_id,
                requirements=[requirements.goal] + requirements.constraints,
                context={
                    "user_request": request.user_request,
                    "plan": plan
                }
            )

            # Execute with Ralph Mode (persistent retries)
            try:
                result = await ralph_engine.execute_until_promise(
                    task=ralph_task,
                    context={"task_id": task_id}
                )

                # Success: update state
                tasks[task_id]["status"] = "complete"
                tasks[task_id]["result"] = result.data.get("message", "Task completed successfully")
                tasks[task_id]["retry_count"] = ralph_engine.retry_count

                # Update STATE.md with result
                session = flow_manager.create_fresh_session()
                session.state = f"""# Current State

## Task {task_id}
- Status: Complete
- Result: {result.data.get('message', 'Task completed successfully')}
- Retry Count: {ralph_engine.retry_count}
- Completed At: {datetime.utcnow().isoformat()}

## Phases Completed
"""
                for phase in tasks[task_id]["phases_completed"]:
                    session.state += f"- {phase}\n"

                flow_manager.save_and_reset(session)

                record_task_execution("gsd_execute", "success")
                logger.info(f"Execute phase completed in {(datetime.utcnow() - execute_start).total_seconds():.2f}s with {ralph_engine.retry_count} retries")

            except Exception as e:
                # Ralph Mode exceeded backstop
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = str(e)
                tasks[task_id]["retry_count"] = ralph_engine.retry_count

                # Update STATE.md with error
                session = flow_manager.create_fresh_session()
                session.state = f"""# Current State

## Task {task_id}
- Status: Failed
- Error: {str(e)}
- Retry Count: {ralph_engine.retry_count}
- Failed At: {datetime.utcnow().isoformat()}

## Phases Completed
"""
                for phase in tasks[task_id]["phases_completed"]:
                    session.state += f"- {phase}\n"

                flow_manager.save_and_reset(session)

                record_task_execution("gsd_execute", "failure")
                logger.error(f"Execute phase failed after {ralph_engine.retry_count} retries: {e}")

        execute_duration = (datetime.utcnow() - execute_start).total_seconds()
        record_gsd_phase("execute", execute_duration)
        tasks[task_id]["phases_completed"].append("execute")

        # Record total duration
        total_duration = discuss_duration + plan_duration + execute_duration
        record_task_duration("full_pipeline", total_duration)

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        record_task_execution("full_pipeline", "failure")

    finally:
        decrement_active_tasks()


@app.post("/execute", response_model=TaskResponse, status_code=202)
async def execute_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Execute a task using GSD Discuss→Plan→Execute with Ralph Mode.

    This endpoint:
    1. Creates a task ID
    2. Starts background execution using GSD phases
    3. Returns immediately with task ID for status polling

    The background task implements:
    - Discuss Phase: Extract requirements from user request
    - Plan Phase: Create implementation plan
    - Execute Phase: Execute with Ralph Mode (persistent retries)
    - Flow-Next: Load fresh context for each phase
    - State Persistence: Update STATE.md after each phase
    """
    task_id = str(uuid.uuid4())

    # Initialize task
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "user_request": request.user_request,
        "requirements": request.requirements,
        "created_at": datetime.utcnow().isoformat(),
        "phases_completed": [],
    }

    # Start background execution
    background_tasks.add_task(execute_task_pipeline, task_id, request)

    logger.info(f"Task {task_id} queued for execution")

    return TaskResponse(
        task_id=task_id,
        status="pending",
        created_at=datetime.utcnow().isoformat()
    )


@app.get("/execute/{task_id}", response_model=ExecuteResponse)
async def get_task_status(task_id: str):
    """Get status of an executing task.

    Returns the current status, phases completed, and result/error if available.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    return ExecuteResponse(
        task_id=task_id,
        phases_completed=task.get("phases_completed", []),
        requirements=task.get("requirements", {}),
        plan_tasks=task.get("plan_tasks", []),
        result=task.get("result"),
        error=task.get("error"),
        retry_count=task.get("retry_count", 0),
        status=task["status"]
    )


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"State directory: {settings.state_dir}")
    logger.info(f"Max retries: {settings.max_retries}")

    # Ensure state directory exists
    Path(settings.state_dir).mkdir(parents=True, exist_ok=True)

    # Initialize state files if they don't exist
    for filepath, default_content in [
        (settings.requirements_file, "# Requirements\n\nNo requirements yet."),
        (settings.plan_file, "# Implementation Plan\n\nNo plan yet."),
        (settings.state_file, "# Current State\n\nService initialized."),
    ]:
        path = Path(filepath)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(default_content)
            logger.info(f"Initialized state file: {filepath}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info(f"Shutting down {settings.service_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
