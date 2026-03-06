"""
Lighting-Sound-Music Service - Main Application

Provides DMX lighting control, audio playback, and synchronization services
for live theatre productions on Project Chimera.
"""

import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import Response
from pydantic import BaseModel, Field

from config import get_settings
from models import (
    LightingSceneRequest,
    AudioCueRequest,
    SyncSceneRequest,
    LightingResponse,
    AudioResponse,
    SyncResponse,
    HealthResponse
)
from dmx_controller import DMXController
from audio_controller import AudioController
from sync_manager import SyncManager
from tracing import setup_telemetry, instrument_fastapi, record_error
from metrics import record_lighting_cue, record_audio_cue, record_sync_scene

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_telemetry("lighting-sound-music")
dmx_controller = DMXController()
audio_controller = AudioController()
sync_manager = SyncManager(dmx_controller, audio_controller)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("Lighting-Sound-Music Service starting up")

    # Initialize audio controller
    try:
        await audio_controller.initialize()
        logger.info("Audio controller initialized successfully")
    except Exception as e:
        logger.warning(f"Audio controller initialization warning: {e}")

    yield

    # Cleanup
    logger.info("Lighting-Sound-Music Service shutting down")
    try:
        await audio_controller.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Lighting-Sound-Music Service",
    description="DMX lighting control, audio playback, and synchronization for live theatre",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


@app.get("/health/live")
async def liveness():
    """Liveness probe - is the service running?"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe - can the service handle requests?"""
    checks = {
        "dmx_controller": dmx_controller.is_ready(),
        "audio_controller": audio_controller.is_ready()
    }

    all_ready = all(checks.values())

    return HealthResponse(
        status="ready" if all_ready else "not_ready",
        service="lighting-sound-music",
        checks=checks
    )


@app.post("/v1/lighting/set", response_model=LightingResponse)
async def set_lighting_scene(request: LightingSceneRequest) -> LightingResponse:
    """
    Set a lighting scene using DMX controller.

    Args:
        request: Lighting scene configuration

    Returns:
        LightingResponse with execution details
    """
    import time
    start_time = time.time()

    try:
        with tracer.start_as_current_span("set_lighting_scene") as span:
            span.set_attribute("scene_id", request.scene_id)
            span.set_attribute("channel_count", len(request.channels))

            # Set the lighting scene
            result = await dmx_controller.set_scene(request.channels)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            record_lighting_cue(
                scene_id=request.scene_id,
                channel_count=len(request.channels),
                duration=duration,
                success=result.get("success", True)
            )

            logger.info(
                f"Lighting scene set: scene_id={request.scene_id}, "
                f"channels={len(request.channels)}, duration={duration:.3f}s"
            )

            return LightingResponse(
                scene_id=request.scene_id,
                status="success",
                channels_set=result.get("channels_set", len(request.channels)),
                duration_ms=int(duration * 1000),
                message="Lighting scene applied successfully"
            )

    except Exception as e:
        logger.error(f"Failed to set lighting scene: {e}")
        record_error("set_lighting_scene", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/audio/play", response_model=AudioResponse)
async def play_audio_cue(request: AudioCueRequest) -> AudioResponse:
    """
    Play an audio cue file.

    Args:
        request: Audio cue configuration

    Returns:
        AudioResponse with playback details
    """
    import time
    start_time = time.time()

    try:
        with tracer.start_as_current_span("play_audio_cue") as span:
            span.set_attribute("cue_id", request.cue_id)
            span.set_attribute("file_path", request.file_path)
            span.set_attribute("volume", request.volume)

            # Play audio
            result = await audio_controller.play_audio(
                file_path=request.file_path,
                volume=request.volume,
                loop=request.loop
            )

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            record_audio_cue(
                cue_id=request.cue_id,
                duration=duration,
                success=result.get("success", True)
            )

            logger.info(
                f"Audio cue played: cue_id={request.cue_id}, "
                f"file={request.file_path}, duration={duration:.3f}s"
            )

            return AudioResponse(
                cue_id=request.cue_id,
                status="playing",
                duration_ms=int(duration * 1000),
                message="Audio cue started successfully"
            )

    except Exception as e:
        logger.error(f"Failed to play audio cue: {e}")
        record_error("play_audio_cue", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/audio/stop")
async def stop_audio_cue():
    """
    Stop currently playing audio cue.

    Returns:
        Status message
    """
    try:
        result = await audio_controller.stop_audio()

        return {
            "status": "stopped",
            "message": "Audio playback stopped"
        }

    except Exception as e:
        logger.error(f"Failed to stop audio: {e}")
        record_error("stop_audio_cue", str(e))
        raise HTTPException(status_code=500, detail=str(e))


class VolumeRequest(BaseModel):
    """Request model for setting volume"""
    volume: float = Field(..., ge=0.0, le=1.0, description="Volume level (0.0 to 1.0)")


@app.post("/v1/audio/volume")
async def set_audio_volume(request: VolumeRequest):
    """
    Set master audio volume.

    Args:
        request: Volume request with volume value

    Returns:
        Status message
    """
    try:
        result = await audio_controller.set_volume(request.volume)

        return {
            "status": "success",
            "volume": request.volume,
            "message": f"Volume set to {request.volume}"
        }

    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        record_error("set_audio_volume", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/sync/scene", response_model=SyncResponse)
async def trigger_sync_scene(request: SyncSceneRequest) -> SyncResponse:
    """
    Trigger a synchronized lighting and audio scene.

    Args:
        request: Synchronized scene configuration

    Returns:
        SyncResponse with timing details
    """
    import time
    start_time = time.time()

    try:
        with tracer.start_as_current_span("trigger_sync_scene") as span:
            span.set_attribute("scene_id", request.scene_id)

            # Trigger synchronized scene
            result = await sync_manager.trigger_scene(
                lighting_channels=request.lighting_channels,
                audio_file=request.audio_file,
                audio_volume=request.audio_volume,
                delay_ms=request.delay_ms
            )

            # Calculate duration
            duration = time.time() - start_time
            total_duration = duration + (request.delay_ms / 1000.0)

            # Record metrics
            record_sync_scene(
                scene_id=request.scene_id,
                duration=total_duration,
                success=result.get("success", True)
            )

            logger.info(
                f"Sync scene triggered: scene_id={request.scene_id}, "
                f"total_duration={total_duration:.3f}s"
            )

            return SyncResponse(
                scene_id=request.scene_id,
                status="success",
                lighting_triggered_at=result.get("lighting_time", 0.0),
                audio_triggered_at=result.get("audio_time", 0.0),
                duration_ms=int(total_duration * 1000),
                message="Synchronized scene triggered successfully"
            )

    except Exception as e:
        logger.error(f"Failed to trigger sync scene: {e}")
        record_error("trigger_sync_scene", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
