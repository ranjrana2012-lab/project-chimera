"""
Director Agent - Main Application

Automated show director service for Project Chimera.
Parses show definitions, coordinates multiple agents, and manages live show execution.
"""

import sys
import os

# Add shared module to path for security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from show_definition import (
    ShowDefinition,
    load_show_definition_from_file,
    save_show_definition,
)
from execution_engine import ExecutionEngine, ExecutionState


logger = logging.getLogger(__name__)

# Global execution engine instance
execution_engine: Optional[ExecutionEngine] = None

# Active show storage
active_shows: Dict[str, ShowDefinition] = {}
show_states: Dict[str, Dict[str, Any]] = {}

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time show updates."""

    def __init__(self):
        self.active_connections: set = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast_show_state(self, show_id: str, state: Dict[str, Any]):
        """Broadcast show state update to all connected clients."""
        if not self.active_connections:
            return

        message = {
            "type": "show_state_update",
            "show_id": show_id,
            "state": state,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class LoadShowRequest(BaseModel):
    """Request to load a show definition."""
    show_id: str
    file_path: str


class StartShowRequest(BaseModel):
    """Request to start show execution."""
    show_id: str
    start_scene: int = 0
    require_approval: bool = True


class PauseShowRequest(BaseModel):
    """Request to pause show execution."""
    show_id: str


class ResumeShowRequest(BaseModel):
    """Request to resume show execution."""
    show_id: str


class StopShowRequest(BaseModel):
    """Request to stop show execution."""
    show_id: str


class ApproveRequest(BaseModel):
    """Request to grant approval to proceed."""
    show_id: str


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global execution_engine

    logger.info("Director Agent starting up")

    # Initialize execution engine
    execution_engine = ExecutionEngine()

    # Load example shows from shows/ directory
    shows_dir = os.path.join(os.path.dirname(__file__), "shows")
    if os.path.exists(shows_dir):
        for filename in os.listdir(shows_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                show_id = filename.replace(".yaml", "").replace(".yml", "")
                try:
                    show = load_show_definition_from_file(os.path.join(shows_dir, filename))
                    active_shows[show_id] = show
                    show_states[show_id] = {
                        "loaded": True,
                        "state": ExecutionState.IDLE.value
                    }
                    logger.info(f"Loaded show: {show_id}")
                except Exception as e:
                    logger.error(f"Failed to load show {filename}: {e}")

    logger.info(f"Loaded {len(active_shows)} shows")

    yield

    # Cleanup
    logger.info("Director Agent shutting down")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Director Agent",
    description="Automated show director for Project Chimera",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)

# Apply security configurations
configure_cors(app)
app.add_middleware(SecurityHeadersMiddleware)
setup_rate_limit_error_handler(app)


# ============================================================================
# Health Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "director-agent",
        "version": "1.0.0",
        "shows_loaded": len(active_shows),
        "active_shows": list(show_states.keys())
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe."""
    return {
        "status": "ready",
        "execution_engine_initialized": execution_engine is not None
    }


# ============================================================================
# Show Management Endpoints
# ============================================================================

@app.post("/api/shows/load")
async def load_show(request: LoadShowRequest):
    """
    Load a show definition from file.

    Args:
        request: Load show request with show_id and file_path

    Returns:
        Loaded show information
    """
    try:
        show = load_show_definition_from_file(request.file_path)
        active_shows[request.show_id] = show
        show_states[request.show_id] = {
            "loaded": True,
            "state": ExecutionState.IDLE.value
        }

        logger.info(f"Loaded show: {request.show_id}")

        return {
            "show_id": request.show_id,
            "title": show.metadata.title,
            "scenes_count": len(show.scenes),
            "estimated_duration_ms": show.metadata.estimated_duration_ms
        }

    except Exception as e:
        logger.error(f"Failed to load show: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shows")
async def list_shows():
    """
    List all available shows.

    Returns:
        List of show definitions
    """
    shows = []

    for show_id, show in active_shows.items():
        shows.append({
            "show_id": show_id,
            "title": show.metadata.title,
            "author": show.metadata.author,
            "version": show.metadata.version,
            "description": show.metadata.description,
            "scenes_count": len(show.scenes),
            "estimated_duration_ms": show.metadata.estimated_duration_ms,
            "state": show_states.get(show_id, {}).get("state", "unknown")
        })

    return {"shows": shows}


@app.get("/api/shows/{show_id}")
async def get_show(show_id: str):
    """
    Get show definition details.

    Args:
        show_id: Show identifier

    Returns:
        Show definition details
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    show = active_shows[show_id]

    return {
        "show_id": show_id,
        "metadata": show.metadata.model_dump(),
        "scenes": [
            {
                "id": scene.id,
                "title": scene.title,
                "description": scene.description,
                "duration_ms": scene.duration_ms,
                "actions_count": len(scene.actions)
            }
            for scene in show.scenes
        ],
        "state": show_states.get(show_id, {}).get("state", "unknown")
    }


# ============================================================================
# Show Execution Endpoints
# ============================================================================

@app.post("/api/shows/{show_id}/start")
async def start_show(show_id: str, background_tasks: BackgroundTasks, request: StartShowRequest = None):
    """
    Start show execution.

    Args:
        show_id: Show identifier
        background_tasks: FastAPI background tasks
        request: Optional start request with parameters

    Returns:
        Show execution status
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    show = active_shows[show_id]

    # Check if show is already running
    current_state = show_states.get(show_id, {}).get("state")
    if current_state == ExecutionState.RUNNING.value:
        raise HTTPException(status_code=400, detail="Show is already running")

    # Use request parameters or defaults
    if request:
        start_scene = request.start_scene
        require_approval = request.require_approval
    else:
        start_scene = 0
        require_approval = True

    # Update state
    show_states[show_id] = {
        "loaded": True,
        "state": ExecutionState.RUNNING.value,
        "current_scene_index": start_scene,
        "require_approval": require_approval
    }

    # Execute show in background
    async def run_show():
        try:
            result = await execution_engine.execute_show(
                show,
                start_scene=start_scene,
                require_approval=require_approval
            )

            show_states[show_id]["state"] = ExecutionState.COMPLETED.value
            show_states[show_id]["result"] = result

            # Broadcast completion
            await ws_manager.broadcast_show_state(show_id, show_states[show_id])

            logger.info(f"Show completed: {show_id}")

        except Exception as e:
            logger.error(f"Show execution failed: {e}")
            show_states[show_id]["state"] = ExecutionState.FAILED.value
            show_states[show_id]["error"] = str(e)

            await ws_manager.broadcast_show_state(show_id, show_states[show_id])

    background_tasks.add_task(run_show)

    # Broadcast start
    await ws_manager.broadcast_show_state(show_id, show_states[show_id])

    return {
        "show_id": show_id,
        "status": "started",
        "start_scene": start_scene,
        "require_approval": require_approval
    }


@app.post("/api/shows/{show_id}/pause")
async def pause_show(show_id: str, request: PauseShowRequest = None):
    """
    Pause show execution.

    Args:
        show_id: Show identifier
        request: Pause request (optional)

    Returns:
        Pause status
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    current_state = show_states.get(show_id, {}).get("state")
    if current_state != ExecutionState.RUNNING.value:
        raise HTTPException(status_code=400, detail="Show is not running")

    execution_engine.request_pause()
    show_states[show_id]["state"] = ExecutionState.PAUSED.value

    await ws_manager.broadcast_show_state(show_id, show_states[show_id])

    return {"show_id": show_id, "status": "paused"}


@app.post("/api/shows/{show_id}/resume")
async def resume_show(show_id: str, request: ResumeShowRequest = None):
    """
    Resume show execution.

    Args:
        show_id: Show identifier
        request: Resume request (optional)

    Returns:
        Resume status
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    current_state = show_states.get(show_id, {}).get("state")
    if current_state != ExecutionState.PAUSED.value:
        raise HTTPException(status_code=400, detail="Show is not paused")

    execution_engine.request_resume()
    show_states[show_id]["state"] = ExecutionState.RUNNING.value

    await ws_manager.broadcast_show_state(show_id, show_states[show_id])

    return {"show_id": show_id, "status": "resumed"}


@app.post("/api/shows/{show_id}/stop")
async def stop_show(show_id: str, request: StopShowRequest = None):
    """
    Stop show execution (emergency stop).

    Args:
        show_id: Show identifier
        request: Stop request (optional)

    Returns:
        Stop status
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    execution_engine.request_stop()
    show_states[show_id]["state"] = ExecutionState.STOPPED.value

    await ws_manager.broadcast_show_state(show_id, show_states[show_id])

    return {"show_id": show_id, "status": "stopped"}


@app.post("/api/shows/{show_id}/approve")
async def grant_approval(show_id: str, request: ApproveRequest = None):
    """
    Grant human approval to proceed to next scene.

    Args:
        show_id: Show identifier
        request: Approve request (optional)

    Returns:
        Approval status
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    execution_engine.grant_approval()

    return {"show_id": show_id, "status": "approved"}


@app.get("/api/shows/{show_id}/state")
async def get_show_state(show_id: str):
    """
    Get current show execution state.

    Args:
        show_id: Show identifier

    Returns:
        Current show state
    """
    if show_id not in active_shows:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found")

    engine_state = execution_engine.get_state()
    show_state = show_states.get(show_id, {})

    return {
        "show_id": show_id,
        **show_state,
        "engine_state": engine_state
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/show/{show_id}")
async def websocket_show_updates(websocket: WebSocket, show_id: str):
    """
    WebSocket endpoint for real-time show state updates.

    Clients can connect to receive real-time updates about show execution.

    Example:
        const ws = new WebSocket('ws://localhost:8013/ws/show/my_show');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Show state:', data.state);
        };
    """
    await ws_manager.connect(websocket)

    try:
        # Send initial state
        if show_id in show_states:
            await websocket.send_json({
                "type": "initial_state",
                "show_id": show_id,
                "state": show_states[show_id]
            })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong
            if data.strip().lower() == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for show: {show_id}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ============================================================================
# Metrics Endpoint
# ============================================================================

@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8013,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
