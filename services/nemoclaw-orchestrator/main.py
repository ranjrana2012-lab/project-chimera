from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from config import get_settings
from errors.handlers import register_error_handlers

# Policy & Privacy
from policy import CHIMERA_POLICIES, PolicyEngine
from llm import PrivacyRouter, NemotronClient, GuardedCloudClient

# State Management
from state import ShowStateMachine, RedisStateStore

# Agent Coordination
from agents import AgentCoordinator

# WebSocket
from websocket import WebSocketManager, WebSocketMessageHandler

logger = logging.getLogger(__name__)
settings = get_settings()

# Global components
policy_engine: PolicyEngine = None
privacy_router: PrivacyRouter = None
state_machine: ShowStateMachine = None
state_store: RedisStateStore = None
agent_coordinator: AgentCoordinator = None
ws_manager: WebSocketManager = None
ws_handler: WebSocketMessageHandler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global policy_engine, privacy_router, state_machine, state_store
    global agent_coordinator, ws_manager, ws_handler

    logger.info("Nemo Claw Orchestrator starting up")

    # Initialize Policy Engine
    policy_engine = PolicyEngine(CHIMERA_POLICIES)
    logger.info("Policy engine initialized")

    # Initialize Privacy Router
    nemotron_client = NemotronClient(
        endpoint=settings.dgx_endpoint,
        model=settings.nemotron_model
    )
    guarded_cloud = GuardedCloudClient()
    privacy_router = PrivacyRouter(
        nemotron_client=nemotron_client,
        guarded_cloud=guarded_cloud,
        local_ratio=settings.local_ratio
    )
    logger.info("Privacy router initialized")

    # Initialize State Store
    try:
        state_store = RedisStateStore(
            url=settings.redis_url,
            ttl=settings.redis_show_state_ttl
        )
        await state_store.connect()
        logger.info("Redis state store connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. State will not be persisted.")
        state_store = None

    # Initialize State Machine
    state_machine = ShowStateMachine(show_id="default", state_store=state_store)
    logger.info("Show state machine initialized")

    # Initialize Agent Coordinator
    agent_urls = {
        "scenespeak": settings.scenespeak_agent_url,
        "captioning": settings.captioning_agent_url,
        "bsl": settings.bsl_agent_url,
        "sentiment": settings.sentiment_agent_url,
        "lighting": settings.lighting_sound_music_url,
        "safety": settings.safety_filter_url,
        "music": settings.music_generation_url,
        "autonomous": settings.autonomous_agent_url,
    }
    agent_coordinator = AgentCoordinator(agent_urls)
    await agent_coordinator.start()
    logger.info("Agent coordinator initialized")

    # Initialize WebSocket Manager
    ws_manager = WebSocketManager(policy_engine)
    ws_handler = WebSocketMessageHandler(
        state_machine=state_machine,
        agent_coordinator=agent_coordinator,
        ws_manager=ws_manager
    )
    logger.info("WebSocket manager initialized")

    yield

    # Cleanup
    logger.info("Nemo Claw Orchestrator shutting down")

    if agent_coordinator:
        await agent_coordinator.stop()

    if state_store:
        await state_store.disconnect()

app = FastAPI(
    title="Nemo Claw Orchestrator",
    description="Project Chimera orchestration with Nemo Claw security and privacy",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

@app.get("/health/live")
async def liveness():
    return {"status": "alive", "service": settings.service_name}

@app.get("/health/ready")
async def readiness():
    """Readiness check with component status"""
    components = {
        "policy_engine": policy_engine is not None,
        "privacy_router": privacy_router is not None,
        "state_machine": state_machine is not None,
        "state_store": state_store is not None,
        "agent_coordinator": agent_coordinator is not None,
        "websocket_manager": ws_manager is not None,
    }

    all_ready = all(components.values())

    return {
        "status": "ready" if all_ready else "degraded",
        "service": settings.service_name,
        "components": components
    }

@app.post("/v1/orchestrate")
async def orchestrate(request: Dict[str, Any]):
    """
    Main orchestration endpoint.

    Routes requests through privacy-aware LLM router.
    """
    if not privacy_router:
        return {"status": "error", "message": "Privacy router not initialized"}

    prompt = request.get("prompt")
    if not prompt:
        return {"status": "error", "message": "Missing prompt"}

    try:
        response = await privacy_router.route(prompt)
        return {
            "status": "success",
            "response": response,
            "routing_metadata": response.get("metadata", {})
        }
    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/show/start")
async def start_show(show_id: str = "default"):
    """
    Start a show.

    Args:
        show_id: Optional show identifier

    Returns:
        Current show state
    """
    if not state_machine:
        return {"status": "error", "message": "State machine not initialized"}

    try:
        state_machine.start()
        return {"status": "success", "state": state_machine.to_dict()}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error starting show: {e}")
        return {"status": "error", "message": "Failed to start show"}

@app.post("/api/show/end")
async def end_show(show_id: str = "default"):
    """
    End a show.

    Args:
        show_id: Optional show identifier

    Returns:
        Current show state
    """
    if not state_machine:
        return {"status": "error", "message": "State machine not initialized"}

    try:
        state_machine.end()
        return {"status": "success", "state": state_machine.to_dict()}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error ending show: {e}")
        return {"status": "error", "message": "Failed to end show"}

@app.get("/api/show/state")
async def get_show_state():
    """
    Get current show state.

    Returns:
        Current show state
    """
    if not state_machine:
        return {"status": "error", "message": "State machine not initialized"}

    return {
        "status": "success",
        "state": state_machine.get_state(),
        "is_running": state_machine.is_running(),
        "is_paused": state_machine.is_paused(),
        "is_ended": state_machine.is_ended()
    }

@app.websocket("/ws/show")
async def websocket_show_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time show updates.

    Accepts messages with format:
    {
        "action": "start_show" | "end_show" | "agent_call" | "ping",
        "data": {...}
    }
    """
    if not ws_manager or not ws_handler:
        await websocket.close(code=1011, reason="WebSocket not initialized")
        return

    await websocket.accept()

    # Generate connection ID
    import uuid
    connection_id = str(uuid.uuid4())

    # Register connection
    await ws_manager.connect(connection_id, websocket)

    try:
        # Send connection confirmation
        await ws_manager.send_to(connection_id, "connected", {
            "connection_id": connection_id,
            "message": "Connected to Nemo Claw Orchestrator"
        })

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()

            try:
                import json
                message = json.loads(data)
                await ws_handler.handle_message(connection_id, message)

            except json.JSONDecodeError:
                await ws_manager.send_to(connection_id, "error", {
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await ws_manager.send_to(connection_id, "error", {
                    "message": f"Error processing message: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)
