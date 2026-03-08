from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import httpx
import json

from config import get_settings
from tracing import setup_telemetry, instrument_fastapi
from metrics import init_service_info, record_request
from models import OrchestrateRequest, OrchestrateResponse, HealthResponse
from show_manager import show_manager, ShowState

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize tracing
tracer = setup_telemetry(settings.service_name, settings.otlp_endpoint)
init_service_info(settings.service_name, "1.0.0")

# Agent registry (will be used for readiness checks)
AGENTS = {
    "scenespeak-agent": settings.scenespeak_agent_url,
    "captioning-agent": settings.captioning_agent_url,
    "bsl-agent": settings.bsl_agent_url,
    "sentiment-agent": settings.sentiment_agent_url,
    "lighting-sound-music": settings.lighting_sound_music_url,
    "safety-filter": settings.safety_filter_url,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("OpenClaw Orchestrator starting up")
    yield
    logger.info("OpenClaw Orchestrator shutting down")

app = FastAPI(
    title="OpenClaw Orchestrator",
    description="Central control plane for Project Chimera - routes skills to agents",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI
instrument_fastapi(app, "openclaw-orchestrator")

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Check if all agents are ready"""
    checks = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent_name, agent_url in AGENTS.items():
            try:
                response = await client.get(f"{agent_url}/health/live")
                checks[agent_name] = response.status_code == 200
            except Exception as e:
                logger.warning(f"Agent {agent_name} not ready: {e}")
                checks[agent_name] = False

    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"

    return HealthResponse(status=status, checks=checks)

@app.post("/v1/orchestrate")
async def orchestrate(request: OrchestrateRequest):
    """Route skill request to appropriate agent"""
    import time
    start_time = time.time()

    try:
        # Determine which agent handles this skill
        agent_url = get_agent_for_skill(request.skill)

        # Call the agent
        result = await call_agent(agent_url, request.skill, request.input)

        duration = (time.time() - start_time) * 1000

        # Record metrics
        record_request(request.skill, 200, duration / 1000)

        return OrchestrateResponse(
            result=result,
            skill_used=request.skill,
            execution_time=duration / 1000,
            metadata={}
        )

    except httpx.ConnectError as e:
        logger.error(f"Agent connection failed: {e}")
        duration = (time.time() - start_time) * 1000
        record_request(request.skill, 503, duration / 1000)
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        duration = (time.time() - start_time) * 1000
        record_request(request.skill, 500, duration / 1000)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skills")
async def list_skills():
    """List available skills"""
    skills = [
        {
            "name": "dialogue_generator",
            "description": "Generate contextual dialogue",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "captioning",
            "description": "Speech-to-text transcription",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "bsl_translation",
            "description": "Text-to-BSL gloss translation",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "sentiment_analysis",
            "description": "Analyze audience sentiment",
            "version": "1.0.0",
            "enabled": True
        }
    ]

    return {"skills": skills, "total": len(skills), "enabled": len(skills)}


@app.get("/api/show/current")
async def get_current_show():
    """Get current show information"""
    show = show_manager.get_current_show()
    if show:
        return show.to_dict()
    return {"show_id": None, "state": "idle"}


@app.post("/api/show/{show_id}/start")
async def start_show(show_id: str):
    """Start a show"""
    show = show_manager.create_show(show_id)
    show.start()
    return show.to_dict()


@app.post("/api/show/{show_id}/end")
async def end_show(show_id: str):
    """End a show"""
    show = show_manager.end_show(show_id)
    if show:
        return show.to_dict()
    raise HTTPException(status_code=404, detail="Show not found")


@app.websocket("/ws/show")
async def websocket_show_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time show updates"""
    await websocket.accept()
    connection_id = f"conn_{id(websocket)}"

    # Get or create default show
    show = show_manager.get_current_show()
    if show is None:
        show = show_manager.create_show("default_show")

    # Add connection to show
    show_manager.add_connection(show.show_id, connection_id)

    # Store connection for broadcasting
    if not hasattr(app.state, "websocket_connections"):
        app.state.websocket_connections = {}
    app.state.websocket_connections[connection_id] = websocket

    # Initialize message history for this connection
    if not hasattr(app.state, "message_history"):
        app.state.message_history = {}
    app.state.message_history[connection_id] = []

    logger.info(f"WebSocket connected: {connection_id}")

    async def broadcast_to_all(message_type: str, data: dict):
        """Broadcast message to all connected WebSocket clients"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Add to all message histories
        for conn_id in app.state.websocket_connections.keys():
            if conn_id in app.state.message_history:
                app.state.message_history[conn_id].append(message)

        # Send to all connected clients
        disconnected = []
        for conn_id, ws in app.state.websocket_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(conn_id)

        # Clean up disconnected clients
        for conn_id in disconnected:
            app.state.websocket_connections.pop(conn_id, None)
            app.state.message_history.pop(conn_id, None)
            show_manager.remove_connection(show.show_id, conn_id)

    try:
        # Send initial show state
        initial_state = {
            "type": "show_state",
            "data": show.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(initial_state)
        app.state.message_history[connection_id].append(initial_state)

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Store message in history (for getMessages functionality)
            app.state.message_history[connection_id].append(message)

            # Handle different message types
            action = message.get("action")
            message_type = message.get("type")

            if action == "start_show":
                show_id = message.get("show_id", show.show_id)
                show = show_manager.start_show(show_id)
                if show:
                    await broadcast_to_all("show_state", show.to_dict())

            elif action == "end_show":
                show = show_manager.end_show(show.show_id)
                if show:
                    await broadcast_to_all("show_state", show.to_dict())

            elif action == "update_state":
                # Update show state and broadcast to all clients
                new_state = message.get("state")
                show_id = message.get("show_id", show.show_id)

                if new_state:
                    # Update show state
                    show.state = new_state

                    # Broadcast to all clients
                    await broadcast_to_all("show_state", show.to_dict())

            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                # Echo back other messages for testing
                echo_message = {
                    "type": message_type or "echo",
                    "data": message,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(echo_message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        show_manager.remove_connection(show.show_id, connection_id)
        app.state.websocket_connections.pop(connection_id, None)
        app.state.message_history.pop(connection_id, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        show_manager.remove_connection(show.show_id, connection_id)
        app.state.websocket_connections.pop(connection_id, None)
        app.state.message_history.pop(connection_id, None)


@app.post("/api/sentiment/webhook")
async def sentiment_webhook(request: dict):
    """Webhook endpoint for sentiment agent to broadcast updates.

    Expects:
        {
            "text": "input text",
            "sentiment": "positive|negative|neutral",
            "score": 0.95,
            "confidence": 0.88
        }
    """
    try:
        text = request.get("text", "")
        sentiment = request.get("sentiment", "neutral")
        confidence = request.get("confidence", 0.0)
        score = request.get("score", 0.0)

        # Broadcast to all WebSocket connections
        if hasattr(app.state, "websocket_connections"):
            disconnected = []
            for conn_id, websocket in app.state.websocket_connections.items():
                try:
                    await websocket.send_json({
                        "type": "sentiment_update",
                        "data": {
                            "sentiment": sentiment,
                            "confidence": confidence,
                            "score": score,
                            "text": text
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to send to {conn_id}: {e}")
                    disconnected.append(conn_id)

            # Clean up disconnected clients
            for conn_id in disconnected:
                app.state.websocket_connections.pop(conn_id, None)

        logger.info(f"Broadcast sentiment update: {sentiment} (confidence: {confidence})")
        return {"status": "ok", "broadcast": True}

    except Exception as e:
        logger.error(f"Sentiment webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_sentiment_update(sentiment: str, confidence: float, metadata: dict = None):
    """Create a sentiment update message for WebSocket broadcast.

    Args:
        sentiment: Sentiment value (positive, negative, neutral)
        confidence: Confidence score
        metadata: Optional additional metadata

    Returns:
        Dictionary sentiment update message
    """
    return {
        "type": "sentiment_update",
        "data": {
            "sentiment": sentiment,
            "confidence": confidence,
            "metadata": metadata or {}
        },
        "timestamp": datetime.now().isoformat()
    }


def get_agent_for_skill(skill: str) -> str:
    """Map skill to agent URL"""
    skill_to_agent = {
        "dialogue_generator": AGENTS["scenespeak-agent"],
        "captioning": AGENTS["captioning-agent"],
        "bsl_translation": AGENTS["bsl-agent"],
        "sentiment_analysis": AGENTS["sentiment-agent"],
    }

    if skill not in skill_to_agent:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill}")

    return skill_to_agent[skill]

async def call_agent(agent_url: str, skill: str, input_data: dict) -> dict:
    """Call agent endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent_url}/v1/{skill}",
            json=input_data
        )
        response.raise_for_status()
        return response.json()
