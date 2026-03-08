"""
BSL Agent - Main Application

Provides text-to-BSL-gloss translation and avatar rendering services with
OpenTelemetry tracing, Prometheus metrics, and health checks.
"""

import time
import logging
import json
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, HTMLResponse, FileResponse
from opentelemetry import trace
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import get_settings
from translator import BSLTranslator
from avatar_renderer import AvatarRenderer
from avatar_webgl import AvatarWebGLRenderer
from models import (
    TranslateRequest,
    TranslateResponse,
    RenderRequest,
    RenderResponse,
    HealthResponse,
    APITranslateRequest,
    APITranslateResponse,
    SignMetadata,
    APIAvatarGenerateRequest,
    APIAvatarGenerateResponse,
    APIAvatarExpressionRequest,
    APIAvatarExpressionResponse,
    APIAvatarHandshapeRequest,
    APIAvatarHandshapeResponse,
    AnimationMetadata,
    VALID_EXPRESSIONS,
    VALID_HANDSHAPES
)
from tracing import setup_telemetry, instrument_fastapi, add_span_attributes, record_error
from metrics import record_translation, record_render

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_telemetry("bsl-agent")
translator = BSLTranslator()
avatar_renderer = AvatarRenderer(
    model_path=settings.avatar_model_path,
    resolution=tuple(map(int, settings.avatar_resolution.split('x'))),
    fps=settings.avatar_fps,
    enable_facial_expressions=settings.enable_facial_expressions,
    enable_body_language=settings.enable_body_language
)
avatar_webgl = AvatarWebGLRenderer(
    model_path=settings.avatar_model_path,
    resolution=tuple(map(int, settings.avatar_resolution.split('x'))),
    fps=settings.avatar_fps,
    enable_facial_expressions=settings.enable_facial_expressions,
    enable_body_language=settings.enable_body_language
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Get static files directory
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("BSL Agent starting up")
    logger.info(f"Avatar rendering enabled: {settings.enable_facial_expressions}")
    logger.info(f"Avatar resolution: {settings.avatar_resolution} @ {settings.avatar_fps}fps")
    yield
    logger.info("BSL Agent shutting down")


# Create FastAPI app
app = FastAPI(
    title="BSL Agent",
    description="British Sign Language gloss notation translation and avatar rendering service",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


@app.get("/health")
async def health():
    """Health check endpoint with renderer information for E2E tests."""
    return HealthResponse(
        status="alive",
        service="bsl-agent",
        translator_ready=True,
        avatar_ready=True,
        renderer={
            "type": "webgl",
            "version": "1.0.0",
            "model": settings.avatar_model_path,
            "resolution": settings.avatar_resolution,
            "fps": settings.avatar_fps
        }
    )


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    return HealthResponse(
        status="ready",
        service="bsl-agent",
        translator_ready=True,
        avatar_ready=True
    )


@app.post("/v1/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest) -> TranslateResponse:
    """
    Translate English text to BSL gloss notation.

    Args:
        request: Translation request with text and options

    Returns:
        TranslateResponse with gloss notation and metadata

    Example:
        POST /v1/translate
        {
            "text": "Hello, how are you?",
            "include_nmm": true,
            "context": {"show_id": "bards-tale"}
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("translate_text") as span:
            # Extract context
            context = request.context or {}
            show_id = context.get("show_id", "unknown")

            # Perform translation
            result = translator.translate_with_nmm(request.text)

            # Extract NMM markers if requested
            nmm_markers = result["non_manual_markers"] if request.include_nmm else None

            # Calculate duration
            duration_sec = time.time() - start_time

            # Record metrics
            record_translation(
                show_id=show_id,
                words=len(request.text.split()),
                duration=duration_sec,
                quality=result["confidence"],
                gloss_words=len(result["breakdown"])
            )

            # Add span attributes for tracing
            add_span_attributes(span, {
                "show.id": show_id,
                "translation.text_length": len(request.text),
                "translation.word_count": len(request.text.split()),
                "translation.gloss_word_count": len(result["breakdown"]),
                "translation.gloss_format": "singspell",
                "translation.confidence": result["confidence"],
                "translation.include_nmm": request.include_nmm,
                "translation.nmm_count": len(nmm_markers) if nmm_markers else 0
            })

            logger.info(
                f"Translation completed for show={show_id}, "
                f"words={len(request.text.split())}, "
                f"duration={duration_sec:.3f}s"
            )

            return TranslateResponse(
                gloss=result["gloss"],
                breakdown=result["breakdown"],
                duration_estimate=result["duration_estimate"],
                confidence=result["confidence"],
                non_manual_markers=nmm_markers,
                translation_time_ms=result["translation_time_ms"]
            )

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        duration_sec = time.time() - start_time

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "translation",
            "error.text_length": len(request.text)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate", response_model=APITranslateResponse)
async def translate_text_api(request: APITranslateRequest) -> APITranslateResponse:
    """
    Translate English text to BSL gloss notation (E2E test compatible).

    This endpoint is designed for E2E testing and provides sign metadata
    including handshapes and locations.

    Args:
        request: Translation request with text and optional context

    Returns:
        APITranslateResponse with gloss, duration, and sign metadata

    Example:
        POST /api/translate
        {
            "text": "Hello, how are you?",
            "context": {"formal": true}
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("translate_text_api") as span:
            # Perform translation
            gloss, breakdown, duration = translator.text_to_gloss(request.text)

            # Generate sign metadata with handshapes and locations
            signs = _generate_sign_metadata(breakdown)

            # Extract context if provided
            context = request.context or {}
            formal_mode = context.get("formal", False)

            # Adjust duration for formal mode (slower signing)
            if formal_mode:
                duration *= 1.2

            # Calculate metrics
            duration_sec = time.time() - start_time

            # Add span attributes
            add_span_attributes(span, {
                "translation.text_length": len(request.text),
                "translation.word_count": len(request.text.split()),
                "translation.gloss_word_count": len(breakdown),
                "translation.formal_mode": formal_mode
            })

            logger.info(
                f"API translation completed: '{request.text}' -> '{gloss}' "
                f"({len(breakdown)} signs, {duration_sec:.3f}s)"
            )

            return APITranslateResponse(
                gloss=gloss,
                duration=duration,
                signs=signs
            )

    except Exception as e:
        logger.error(f"API translation failed: {e}")

        # Record error
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "api_translation",
            "error.text_length": len(request.text)
        })

        raise HTTPException(status_code=500, detail=str(e))


def _generate_sign_metadata(breakdown: list[str]) -> list[SignMetadata]:
    """
    Generate sign metadata including handshapes and locations.

    Args:
        breakdown: List of BSL gloss words

    Returns:
        List of SignMetadata objects with handshape and location info
    """
    # Common handshapes for BSL
    handshapes = {
        "HELLO": "flat_hand_wave",
        "GOOD": "flat_hand",
        "MORNING": "flat_hand_chest",
        "PLEASE": "flat_hand_circular",
        "THANK": "flat_hand_chest",
        "YOU": "pointing_finger",
        "HOW": "flat_hand",
        "WHAT": "flat_hand",
        "WHERE": "index_finger",
        "WHEN": "flat_hand",
        "WHY": "flat_hand",
        "WHO": "index_finger",
        "WHICH": "index_finger",
        "THIS": "index_finger",
        "THAT": "index_finger",
        "HERE": "flat_hand",
        "THERE": "pointing_finger",
        "YES": "fist_nod",
        "NO": "flat_hand_wave",
        "UNDERSTAND": "flat_hand_head",
        "LOOK": "v_hand_eyes",
        "LISTEN": "cupped_hand_ear",
        "WELCOME": "flat_hand_sweep",
        "GOODBYE": "flat_hand_wave",
        "NAME": "index_finger_chest",
        "MY": "flat_hand_chest",
        "YOUR": "pointing_finger",
        "STOP": "flat_hand_palm",
        "WAIT": "flat_hand_up",
    }

    # Common locations for BSL
    locations = {
        "HELLO": "forehead",
        "GOOD": "chest",
        "MORNING": "chest",
        "PLEASE": "chest_circular",
        "THANK": "chest",
        "YOU": "forward",
        "HOW": "chest",
        "WHAT": "chest",
        "WHERE": "side",
        "WHEN": "chest",
        "WHY": "chest",
        "WHO": "side",
        "WHICH": "side",
        "THIS": "forward",
        "THAT": "forward",
        "HERE": "down",
        "THERE": "forward_point",
        "YES": "head_nod",
        "NO": "head_shake",
        "UNDERSTAND": "head",
        "LOOK": "eyes",
        "LISTEN": "ear",
        "WELCOME": "outward_sweep",
        "GOODBYE": "outward",
        "NAME": "chest",
        "MY": "chest",
        "YOUR": "forward",
        "STOP": "palm_out",
        "WAIT": "palm_up",
    }

    signs = []

    for gloss_word in breakdown:
        # Get handshape and location, with defaults
        handshape = handshapes.get(gloss_word, "flat_hand")
        location = locations.get(gloss_word, "neutral_space")

        # Handle finger-spelling
        if gloss_word.startswith("FS-"):
            handshape = "finger_spelling"
            location = "neutral_space"

        signs.append(SignMetadata(
            gloss=gloss_word,
            handshape=handshape,
            location=location
        ))

    return signs


# ============================================================================
# E2E Avatar Endpoints
# ============================================================================

@app.post("/api/avatar/generate", response_model=APIAvatarGenerateResponse)
async def api_avatar_generate(request: APIAvatarGenerateRequest) -> APIAvatarGenerateResponse:
    """
    Generate avatar animation data for text (E2E test compatible).

    Args:
        request: Avatar generation request with text and optional expression

    Returns:
        APIAvatarGenerateResponse with animation data and metadata

    Example:
        POST /api/avatar/generate
        {
            "text": "Welcome to the show",
            "expression": "happy"  // optional
        }
    """
    start_time = time.time()

    try:
        # Translate text to gloss
        gloss, breakdown, duration = translator.text_to_gloss(request.text)

        # Generate animation frames using WebGL renderer
        animation_data = avatar_webgl.generate_animation(
            gloss=breakdown,
            expression=request.expression or "neutral"
        )

        # Create metadata
        processing_time = time.time() - start_time
        metadata = AnimationMetadata(
            duration_ms=processing_time * 1000,
            fps=settings.avatar_fps
        )

        # Record render metric
        # Note: record_render requires show_id, gesture_count, duration - using defaults for E2E
        try:
            record_render(
                show_id="e2e_test",
                gesture_count=len(breakdown),
                duration=processing_time
            )
        except Exception as e:
            logger.warning(f"Failed to record render metrics: {e}")

        logger.info(
            f"API avatar generation completed: '{request.text}' -> {len(animation_data.get('frames', []))} frames"
        )

        return APIAvatarGenerateResponse(
            animation_data=animation_data,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"API avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/expression", response_model=APIAvatarExpressionResponse)
async def api_avatar_expression(request: APIAvatarExpressionRequest) -> APIAvatarExpressionResponse:
    """
    Apply expression to avatar (E2E test compatible).

    Args:
        request: Expression request with expression name

    Returns:
        APIAvatarExpressionResponse with expression and applied status

    Example:
        POST /api/avatar/expression
        {
            "expression": "happy"
        }
    """
    try:
        # Validate expression
        if request.expression not in VALID_EXPRESSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid expression: '{request.expression}'. Valid expressions: {VALID_EXPRESSIONS}"
            )

        # Apply expression using avatar renderer
        applied = avatar_webgl.set_expression(request.expression)

        logger.info(f"Expression '{request.expression}' applied: {applied}")

        return APIAvatarExpressionResponse(
            expression=request.expression,
            applied=applied
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Expression application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/handshape", response_model=APIAvatarHandshapeResponse)
async def api_avatar_handshape(request: APIAvatarHandshapeRequest) -> APIAvatarHandshapeResponse:
    """
    Apply handshape to avatar (E2E test compatible).

    Args:
        request: Handshape request with handshape and hand

    Returns:
        APIAvatarHandshapeResponse with handshape, hand, and applied status

    Example:
        POST /api/avatar/handshape
        {
            "handshape": "wave",
            "hand": "right"
        }
    """
    try:
        # Validate hand parameter
        if request.hand not in ("left", "right"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid hand: '{request.hand}'. Must be 'left' or 'right'"
            )

        # Validate handshape
        if request.handshape not in VALID_HANDSHAPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid handshape: '{request.handshape}'. Valid handshapes: {VALID_HANDSHAPES}"
            )

        # Apply handshape using avatar renderer
        applied = avatar_webgl.set_handshape(request.handshape, request.hand)

        logger.info(f"Handshape '{request.handshape}' applied to {request.hand} hand: {applied}")

        return APIAvatarHandshapeResponse(
            handshape=request.handshape,
            hand=request.hand,
            applied=applied
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Handshape application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Internal API Endpoints
# ============================================================================

@app.post("/v1/render", response_model=RenderResponse)
async def render_avatar(request: RenderRequest) -> RenderResponse:
    """
    Render BSL signs using avatar system.

    Args:
        request: Render request with gloss and session info

    Returns:
        RenderResponse with animation data and status

    Example:
        POST /v1/render
        {
            "gloss": "HELLO HOW YOU",
            "session_id": "user-123",
            "include_nmm": true
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("render_avatar") as span:
            # Generate animation data
            animation_data = avatar_renderer.render_gloss(
                gloss=request.gloss,
                non_manual_markers=[] if not request.include_nmm else None
            )

            # Calculate metrics
            gesture_count = len(animation_data["gestures"])
            duration_sec = time.time() - start_time

            # Record metrics
            session_id = request.session_id or "unknown"
            record_render(
                show_id="unknown",  # Could be extracted from context in future
                gesture_count=gesture_count,
                duration=duration_sec,
                session_id=session_id
            )

            # Add span attributes for tracing
            add_span_attributes(span, {
                "render.gloss_word_count": len(request.gloss.split()),
                "render.gesture_count": gesture_count,
                "render.duration_total": animation_data["total_duration"],
                "render.session_id": session_id,
                "render.include_nmm": request.include_nmm
            })

            logger.info(
                f"Avatar render completed: gestures={gesture_count}, "
                f"duration={duration_sec:.3f}s, session={session_id}"
            )

            return RenderResponse(
                success=True,
                animation_data=animation_data,
                gestures_queued=gesture_count,
                session_id=request.session_id,
                message=f"Successfully queued {gesture_count} gestures for rendering"
            )

    except Exception as e:
        logger.error(f"Avatar rendering failed: {e}")

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "render",
            "error.gloss_length": len(request.gloss)
        })

        # Return error response
        return RenderResponse(
            success=False,
            animation_data={},
            gestures_queued=0,
            session_id=request.session_id,
            message=f"Rendering failed: {str(e)}"
        )


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/avatar", response_class=HTMLResponse)
async def get_avatar_viewer():
    """
    Serve the 3D avatar viewer HTML page.

    Returns:
        HTML page with Three.js-based avatar viewer
    """
    avatar_html_path = STATIC_DIR / "avatar.html"
    if avatar_html_path.exists():
        return FileResponse(avatar_html_path)
    return HTMLResponse("<h1>Avatar viewer not found</h1>", status_code=404)


@app.get("/static/{file_path:path}")
async def serve_static_files(file_path: str):
    """
    Serve static files for the avatar viewer.

    Args:
        file_path: Path to the static file

    Returns:
        File response
    """
    file_path = STATIC_DIR / file_path
    if file_path.exists():
        return FileResponse(file_path)
    return Response(content="File not found", status_code=404)


@app.post("/api/avatar/generate")
async def generate_avatar_animation(request: RenderRequest) -> Dict[str, Any]:
    """
    Generate NMM animation for BSL gloss.

    Creates WebGL/Three.js compatible animation data for the 3D avatar.

    Args:
        request: Render request with gloss and session info

    Returns:
        NMM animation data for client-side rendering

    Example:
        POST /api/avatar/generate
        {
            "gloss": "HELLO HOW YOU",
            "session_id": "user-123",
            "include_nmm": true
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("generate_avatar_animation") as span:
            # Determine NMM markers
            nmm_markers = None if request.include_nmm else []

            # Generate NMM animation
            animation_data = avatar_webgl.render_gloss_to_nmm(
                gloss=request.gloss,
                non_manual_markers=nmm_markers
            )

            # Calculate metrics
            duration_sec = time.time() - start_time

            # Record metrics
            session_id = request.session_id or "unknown"
            record_render(
                show_id="unknown",
                gesture_count=len(request.gloss.split()),
                duration=duration_sec,
                session_id=session_id
            )

            # Add span attributes
            add_span_attributes(span, {
                "avatar.gloss_word_count": len(request.gloss.split()),
                "avatar.animation_duration": animation_data["metadata"]["duration"],
                "avatar.session_id": session_id,
                "avatar.format": "nmm-animation-v1"
            })

            logger.info(
                f"NMM animation generated: gloss='{request.gloss}', "
                f"duration={duration_sec:.3f}s, session={session_id}"
            )

            return {
                "success": True,
                "animation_data": animation_data,
                "session_id": request.session_id,
                "message": f"Successfully generated animation for {len(request.gloss.split())} signs"
            }

    except Exception as e:
        logger.error(f"Avatar animation generation failed: {e}")

        # Record error
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "avatar_animation",
            "error.gloss_length": len(request.gloss)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar/info")
async def get_avatar_info() -> Dict[str, Any]:
    """
    Get avatar renderer information.

    Returns:
        Avatar renderer configuration and status
    """
    return avatar_webgl.get_renderer_info()


@app.post("/api/avatar/expression")
async def set_avatar_expression(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set facial expression for the avatar.

    Args:
        data: Expression data with 'expression' and optional 'intensity'

    Returns:
        Expression morph target values

    Example:
        POST /api/avatar/expression
        {
            "expression": "happy",
            "intensity": 0.8
        }
    """
    try:
        expression = data.get("expression", "neutral")
        intensity = data.get("intensity", 1.0)

        result = avatar_webgl.set_expression(expression, intensity)

        # Broadcast to all connected WebSocket clients
        await manager.broadcast({
            "type": "expression",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/avatar/handshape")
async def set_avatar_handshape(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set hand shape for BSL signing.

    Args:
        data: Handshape data with 'hand', 'handshape', and optional 'intensity'

    Returns:
        Hand configuration

    Example:
        POST /api/avatar/handshape
        {
            "hand": "right",
            "handshape": "fist",
            "intensity": 1.0
        }
    """
    try:
        hand = data.get("hand", "right")
        handshape = data.get("handshape", "fist")
        intensity = data.get("intensity", 1.0)

        result = avatar_webgl.set_handshape(hand, handshape, intensity)

        # Broadcast to all connected WebSocket clients
        await manager.broadcast({
            "type": "handshape",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.websocket("/ws/avatar")
async def avatar_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time avatar animation updates.

    Clients can connect to receive real-time animation updates,
    expression changes, and other avatar state changes.

    Example:
        const ws = new WebSocket('ws://localhost:8003/ws/avatar');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'animation') {
                // Update avatar animation
            }
        };
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "play_animation":
                # Play animation
                animation_name = data.get("animation")
                if animation_name:
                    result = avatar_webgl.play_animation(animation_name)
                    await websocket.send_json({
                        "type": "animation_started",
                        "data": result
                    })

            elif message_type == "set_expression":
                # Set expression
                expression = data.get("expression", "neutral")
                intensity = data.get("intensity", 1.0)
                try:
                    result = avatar_webgl.set_expression(expression, intensity)
                    await manager.broadcast({
                        "type": "expression",
                        "data": result
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message_type == "set_handshape":
                # Set handshape
                hand = data.get("hand", "right")
                handshape = data.get("handshape", "fist")
                intensity = data.get("intensity", 1.0)
                try:
                    result = avatar_webgl.set_handshape(hand, handshape, intensity)
                    await manager.broadcast({
                        "type": "handshape",
                        "data": result
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )
