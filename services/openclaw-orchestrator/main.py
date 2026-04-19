from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import httpx
import json
import os
import sys
import asyncio
import time

# Import shared security middleware
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    limiter,
    setup_rate_limit_error_handler,
)
# Import shared performance utilities (Iteration 35)
from shared.connection_pool import ConnectionPoolManager, get_global_pool, close_global_pool
from shared.cache import RequestCache, get_global_cache, close_global_cache

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
    "autonomous-agent": settings.autonomous_agent_url,
}

# Map skill names to actual agent endpoint paths
SKILL_ENDPOINTS = {
    "dialogue_generator": "/api/generate",
    "captioning": "/api/transcribe",
    "bsl_translation": "/api/translate",
    "sentiment_analysis": "/api/analyze",
    "autonomous_execution": "/execute",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager with connection pool and cache initialization"""
    logger.info("OpenClaw Orchestrator starting up")

    # Initialize global connection pool for performance (Iteration 35)
    pool = get_global_pool()
    logger.info("Connection pool initialized")

    # Initialize global cache for performance (Iteration 35)
    cache = get_global_cache()
    logger.info("Request cache initialized")

    yield

    # Cleanup on shutdown
    logger.info("OpenClaw Orchestrator shutting down")
    await close_global_pool()
    await close_global_cache()
    logger.info("Connection pool and cache closed")

app = FastAPI(
    title="OpenClaw Orchestrator",
    description="Central control plane for Project Chimera - routes skills to agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with environment-based origins (SECURITY: no longer allows all origins)
configure_cors(app)

# Add security headers middleware (SECURITY: prevents XSS, clickjacking, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Set up rate limiting error handler
setup_rate_limit_error_handler(app)

# Instrument FastAPI
instrument_fastapi(app, "openclaw-orchestrator")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "openclaw-orchestrator",
        "version": "1.0.0"
    }


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Check if all agents are ready using connection pooling (Iteration 35)"""
    checks = {}

    # Use global connection pool for health checks
    pool = get_global_pool()

    async def check_agent(agent_name: str, agent_url: str):
        """Check a single agent's health."""
        try:
            session = await pool.get_session(agent_url)
            response = await session.get("/health/live", timeout=5.0)
            is_healthy = response.status_code == 200
            await pool.release_session(agent_url)
            return agent_name, is_healthy
        except Exception as e:
            logger.warning(f"Agent {agent_name} not ready: {e}")
            try:
                await pool.release_session(agent_url)
            except:
                pass
            return agent_name, False

    # Check all agents in parallel
    tasks = [
        check_agent(name, url)
        for name, url in AGENTS.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        agent_name, is_healthy = result
        checks[agent_name] = is_healthy

    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"

    return HealthResponse(status=status, checks=checks)

@app.post("/api/orchestrate")
async def orchestrate_synchronous(request: dict):
    """
    Parallel orchestration pipeline for improved performance (Iteration 35).

    Optimization: Sentiment and Safety checks run in parallel using asyncio.gather().
    Connection pooling eliminates TCP handshake overhead.

    Args:
        request: {
            "prompt": "The hero enters the room",
            "show_id": "default_show",
            "context": {...},
            "webhook_url": "..."  # Optional: if provided, returns 202 with task_id
        }

    Returns:
        {
            "response": "generated dialogue",
            "sentiment": {"label": "positive", "score": 0.95},
            "safety_check": {"passed": true, "reason": "Content approved"},
            "metadata": {"show_id": "...", "processing_time_ms": 1234}
        }
    """
    import uuid
    start_time = time.time()

    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=422, detail="prompt is required")

        show_id = request.get("show_id", "default_show")
        context = request.get("context", {})
        webhook_url = request.get("webhook_url")

        # If webhook_url is provided, return async response
        if webhook_url:
            from fastapi import Response
            from fastapi.responses import JSONResponse
            task_id = str(uuid.uuid4())
            # TODO: Implement async task queue for webhook callbacks
            return JSONResponse(
                status_code=202,
                content={
                    "task_id": task_id,
                    "status": "processing"
                }
            )

        # Get global connection pool (Iteration 35)
        pool = get_global_pool()
        cache = get_global_cache()

        # Check cache first (Iteration 35)
        cache_key = cache.cache_key("orchestrator", prompt, show_id)
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for orchestration request")
            cached_result["metadata"]["from_cache"] = True
            return cached_result

        # Parallel execution: Sentiment + Safety (Iteration 35)
        async def analyze_sentiment():
            """Call sentiment agent with connection pooling."""
            try:
                session = await pool.get_session(AGENTS['sentiment-agent'])
                response = await session.post(
                    "/api/analyze",
                    json={"text": prompt, "detect_language": False}
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Sentiment: {result.get('sentiment', 'unknown')}")
                await pool.release_session(AGENTS['sentiment-agent'])
                return result
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                await pool.release_session(AGENTS['sentiment-agent'])
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}

        async def check_safety():
            """Call safety filter with connection pooling."""
            try:
                session = await pool.get_session(AGENTS['safety-filter'])
                response = await session.post(
                    "/api/check",
                    json={"text": prompt, "policy": "family"}
                )
                response.raise_for_status()
                result = response.json()
                await pool.release_session(AGENTS['safety-filter'])
                return result
            except Exception as e:
                logger.warning(f"Safety check failed: {e}")
                await pool.release_session(AGENTS['safety-filter'])
                return {"safe": True, "reason": "Safety filter unavailable"}

        # Run sentiment and safety in parallel
        sentiment_result, safety_result = await asyncio.gather(
            analyze_sentiment(),
            check_safety(),
            return_exceptions=True
        )

        # Handle exceptions from parallel tasks
        if isinstance(sentiment_result, Exception):
            logger.error(f"Sentiment task failed: {sentiment_result}")
            sentiment_result = {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        if isinstance(safety_result, Exception):
            logger.error(f"Safety task failed: {safety_result}")
            safety_result = {"safe": True, "reason": "Safety filter unavailable"}

        # Normalize sentiment to expected format
        sentiment_label = sentiment_result.get("sentiment", "neutral")
        sentiment_score = sentiment_result.get("score", 0.0)

        # Check if content is safe
        safe = safety_result.get("safe", True)
        safety_reason = safety_result.get("reason", "Content approved")

        if not safe:
            # Return early with blocked response
            return {
                "response": "",
                "sentiment": {
                    "label": sentiment_label,
                    "score": sentiment_score
                },
                "safety_check": {
                    "passed": False,
                    "reason": safety_reason
                },
                "metadata": {
                    "show_id": show_id,
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            }

        # Generate Dialogue via LLM (runs after safety check passes)
        llm_response = ""
        try:
            session = await pool.get_session(AGENTS['scenespeak-agent'])
            response = await session.post(
                "/api/generate",
                json={
                    "prompt": prompt,
                    "context": {
                        **context,
                        "show_id": show_id,
                        "sentiment": sentiment_label
                    },
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=120.0  # Long timeout for LLM
            )
            response.raise_for_status()
            dialogue_result = response.json()
            llm_response = dialogue_result.get("dialogue", "")
            logger.info(f"Generated dialogue: {len(llm_response)} chars")
            await pool.release_session(AGENTS['scenespeak-agent'])
        except Exception as e:
            logger.error(f"Dialogue generation failed: {e}")
            try:
                await pool.release_session(AGENTS['scenespeak-agent'])
            except:
                pass
            llm_response = f"[Could not generate dialogue: {str(e)}]"

        processing_time = int((time.time() - start_time) * 1000)

        result = {
            "response": llm_response,
            "sentiment": {
                "label": sentiment_label,
                "score": sentiment_score
            },
            "safety_check": {
                "passed": safe,
                "reason": safety_reason
            },
            "metadata": {
                "show_id": show_id,
                "processing_time_ms": processing_time
            }
        }

        # Cache the result (Iteration 35) - shorter TTL for orchestrator
        await cache.set(cache_key, result, ttl=60)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synchronous orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _map_sentiment_to_dmx(sentiment: str, score: float) -> dict:
    """
    Map sentiment to DMX lighting values (mock hardware output).

    Args:
        sentiment: positive, negative, or neutral
        score: sentiment score (-1 to 1)

    Returns:
        Dictionary with DMX channel values
    """
    # DMX channels: 1-3 are RGB, 4 is brightness, 5-10 are special effects
    dmx = {
        "red": 128,      # 0-255
        "green": 128,    # 0-255
        "blue": 128,     # 0-255
        "brightness": 200,  # 0-255
        "effect": "none"
    }

    if sentiment == "positive":
        # Warm colors - orange/yellow
        dmx["red"] = 255
        dmx["green"] = min(255, int(200 + score * 55))
        dmx["blue"] = 50
        dmx["brightness"] = 255
        dmx["effect"] = "sparkle"
    elif sentiment == "negative":
        # Cool colors - blue/purple
        dmx["red"] = 50
        dmx["green"] = 50
        dmx["blue"] = 255
        dmx["brightness"] = 180
        dmx["effect"] = "dim"
    else:
        # Neutral - white
        dmx["red"] = 200
        dmx["green"] = 200
        dmx["blue"] = 200
        dmx["brightness"] = 220
        dmx["effect"] = "steady"

    return dmx


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
        },
        {
            "name": "autonomous_execution",
            "description": "Execute complex autonomous tasks with GSD framework",
            "version": "1.0.0",
            "enabled": True
        }
    ]

    return {"skills": skills, "total": len(skills), "enabled": len(skills)}


@app.get("/api/skills")
async def list_skills_api():
    """List available skills with metadata (E2E test compatible)"""
    skills = [
        {
            "name": "generate_dialogue",
            "description": "Generate contextual dialogue for scenes",
            "endpoint": "/v1/generate",
            "method": "POST"
        },
        {
            "name": "captioning",
            "description": "Speech-to-text transcription with timestamps",
            "endpoint": "/v1/transcribe",
            "method": "POST"
        },
        {
            "name": "bsl_translation",
            "description": "Text-to-BSL gloss translation with avatar",
            "endpoint": "/v1/translate",
            "method": "POST"
        },
        {
            "name": "analyze_sentiment",
            "description": "Analyze audience sentiment in real-time",
            "endpoint": "/api/analyze",
            "method": "POST"
        },
        {
            "name": "autonomous_execution",
            "description": "Execute complex autonomous tasks with GSD Discuss→Plan→Execute→Verify framework",
            "endpoint": "/execute",
            "method": "POST"
        }
    ]

    return {
        "skills": skills,
        "total": len(skills),
        "enabled": len(skills)
    }


@app.get("/api/show/status")
async def get_show_status_api():
    """Get current show status (E2E test compatible)"""
    show = show_manager.get_current_show()

    if show:
        return {
            "show_id": show.show_id,
            "state": show.state,  # ShowState is str enum, no .value needed
            "active": show.state != ShowState.IDLE,
            "scene": show.current_scene or "none",
            "audience_metrics": {
                "total_reactions": show.audience_metrics.get("total_reactions", 0),
                "average_sentiment": show.audience_metrics.get("sentiment_score", 0.5)
            },
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "show_id": None,
            "state": "idle",
            "active": False,
            "scene": "none",
            "audience_metrics": {
                "total_reactions": 0,
                "average_sentiment": 0.5
            },
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/show/control")
async def control_show_api(request: dict):
    """Control show via API (start_show/start, stop_show/stop)"""
    action = request.get("action")
    show_id = request.get("show_id", "default_show")

    # Accept both action name variants for compatibility
    if action in ("start", "start_show"):
        # Check if show is already active
        current_show = show_manager.get_current_show()
        if current_show and current_show.state in ("running", "active"):
            raise HTTPException(
                status_code=409,
                detail=f"Show {current_show.show_id} is already active"
            )
        show = show_manager.create_show(show_id)
        show.start()
        return {
            "show_id": show.show_id,
            "state": show.state,
            "status": "starting"
        }
    elif action in ("stop", "stop_show"):
        show = show_manager.end_show(show_id)
        if show:
            return {
                "show_id": show.show_id,
                "state": show.state,
                "action": "stop",
                "status": "success"
            }
        else:
            raise HTTPException(status_code=404, detail="Show not found")
    else:
        raise HTTPException(status_code=422, detail=f"Invalid action: {action}")


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
        "autonomous_execution": AGENTS["autonomous-agent"],
    }

    if skill not in skill_to_agent:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill}")

    return skill_to_agent[skill]

async def call_agent(agent_url: str, skill: str, input_data: dict) -> dict:
    """Call agent endpoint using connection pooling (Iteration 35).

    Special handling for autonomous-agent which uses /execute endpoint
    """
    # Use skill endpoint mapping for correct API paths
    endpoint = SKILL_ENDPOINTS.get(skill, f"/v1/{skill}")

    # Use global connection pool
    pool = get_global_pool()
    session = await pool.get_session(agent_url)

    try:
        response = await session.post(
            endpoint,
            json=input_data,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    finally:
        await pool.release_session(agent_url)
