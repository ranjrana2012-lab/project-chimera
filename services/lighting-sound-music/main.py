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
    HealthResponse,
    # E2E-compatible models
    DMXInfo,
    ExtendedHealthResponse,
    SetLightingRequest,
    SetLightingResponse,
    SetColorRequest,
    SetColorResponse,
    SetIntensityRequest,
    SetIntensityResponse,
    TransitionState,
    TransitionRequest,
    TransitionResponse,
    LightingStateResponse,
    PresetScene,
    PresetsResponse,
    ApplyPresetRequest,
    ApplyPresetResponse,
    ZoneRequest,
    ZoneResponse,
    EffectParams,
    EffectRequest,
    EffectResponse,
    BatchUpdate,
    BatchRequest,
    BatchResponse,
    ResetResponse
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

# In-memory lighting state for E2E tests
class LightingState:
    """Simple in-memory state tracker for lighting"""
    def __init__(self):
        self.color = "#FFFFFF"
        self.intensity = 1.0
        self.scene = "default"
        self.presets = {
            "dramatic_spotlight": PresetScene(
                name="dramatic_spotlight",
                description="Dramatic spotlight effect"
            ),
            "soft_wash": PresetScene(
                name="soft_wash",
                description="Soft color wash"
            ),
            "high_contrast": PresetScene(
                name="high_contrast",
                description="High contrast lighting"
            )
        }

lighting_state = LightingState()


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


@app.get("/health")
async def health():
    """
    Health check endpoint with DMX info for E2E tests.
    Returns overall health status including DMX connection information.
    """
    return ExtendedHealthResponse(
        status="alive",
        service="lighting-sound-music",
        dmx_info=DMXInfo(
            connected=dmx_controller.is_connected(),
            universe=dmx_controller.get_universe()
        )
    )


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


# ============================================================================
# E2E-Compatible Lighting API Endpoints
# ============================================================================

def validate_hex_color(color: str) -> bool:
    """Validate hex color format (#RRGGBB)"""
    import re
    pattern = r'^#[0-9A-Fa-f]{6}$'
    return re.match(pattern, color) is not None


@app.post("/api/lighting", response_model=SetLightingResponse)
async def set_lighting(request: SetLightingRequest):
    """
    Set lighting scene with scene identifier and optional mood.

    Args:
        request: Lighting scene request

    Returns:
        SetLightingResponse with success status
    """
    try:
        lighting_state.scene = request.scene
        # Update state based on mood if provided
        if request.mood == "dramatic":
            lighting_state.color = "#FF5733"
            lighting_state.intensity = 0.8
        elif request.mood == "calm":
            lighting_state.color = "#87CEEB"
            lighting_state.intensity = 0.6

        logger.info(f"Lighting scene set: {request.scene} (mood: {request.mood})")

        return SetLightingResponse(
            success=True,
            scene=request.scene
        )

    except Exception as e:
        logger.error(f"Failed to set lighting scene: {e}")
        return SetLightingResponse(success=False, scene=request.scene)


@app.post("/api/lighting/color", response_model=SetColorResponse)
async def set_lighting_color(request: SetColorRequest):
    """
    Set lighting color with hex color code and intensity.

    Args:
        request: Color request

    Returns:
        SetColorResponse with applied status
    """
    if not validate_hex_color(request.color):
        raise HTTPException(
            status_code=422,
            detail="Invalid color format. Must be hex color code (#RRGGBB)"
        )

    try:
        lighting_state.color = request.color
        lighting_state.intensity = request.intensity

        logger.info(f"Lighting color set: {request.color} at intensity {request.intensity}")

        return SetColorResponse(
            applied=True,
            color=request.color
        )

    except Exception as e:
        logger.error(f"Failed to set lighting color: {e}")
        return SetColorResponse(applied=False, color=request.color)


@app.post("/api/lighting/intensity", response_model=SetIntensityResponse)
async def set_lighting_intensity(request: SetIntensityRequest):
    """
    Set lighting intensity level (0.0 to 1.0).

    Args:
        request: Intensity request

    Returns:
        SetIntensityResponse with applied status
    """
    try:
        lighting_state.intensity = request.intensity

        logger.info(f"Lighting intensity set: {request.intensity}")

        return SetIntensityResponse(
            applied=True,
            intensity=request.intensity
        )

    except Exception as e:
        logger.error(f"Failed to set lighting intensity: {e}")
        return SetIntensityResponse(applied=False, intensity=request.intensity)


@app.post("/api/lighting/transition", response_model=TransitionResponse)
async def lighting_transition(request: TransitionRequest):
    """
    Transition between two lighting states over a duration.

    Args:
        request: Transition request

    Returns:
        TransitionResponse with started status
    """
    try:
        # Validate colors
        if not validate_hex_color(request.from_state.color):
            raise HTTPException(
                status_code=422,
                detail="Invalid from_state color format"
            )
        if not validate_hex_color(request.to_state.color):
            raise HTTPException(
                status_code=422,
                detail="Invalid to_state color format"
            )

        # Update to target state
        lighting_state.color = request.to_state.color
        lighting_state.intensity = request.to_state.intensity

        logger.info(
            f"Lighting transition: {request.from_state.color} -> "
            f"{request.to_state.color} over {request.duration}ms"
        )

        return TransitionResponse(
            started=True,
            duration=request.duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start lighting transition: {e}")
        return TransitionResponse(started=False, duration=request.duration)


@app.get("/api/lighting/state", response_model=LightingStateResponse)
async def get_lighting_state():
    """
    Get current lighting state.

    Returns:
        LightingStateResponse with current color, intensity, and scene
    """
    return LightingStateResponse(
        color=lighting_state.color,
        intensity=lighting_state.intensity,
        scene=lighting_state.scene
    )


@app.get("/api/lighting/presets", response_model=PresetsResponse)
async def get_lighting_presets():
    """
    Get available lighting preset scenes.

    Returns:
        PresetsResponse with list of available presets
    """
    return PresetsResponse(
        presets=list(lighting_state.presets.values())
    )


@app.post("/api/lighting/preset", response_model=ApplyPresetResponse)
async def apply_lighting_preset(request: ApplyPresetRequest):
    """
    Apply a lighting preset scene.

    Args:
        request: Preset request

    Returns:
        ApplyPresetResponse with applied status
    """
    if request.preset not in lighting_state.presets:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{request.preset}' not found"
        )

    try:
        preset = lighting_state.presets[request.preset]
        lighting_state.scene = preset.name

        # Set preset-specific values
        if preset.name == "dramatic_spotlight":
            lighting_state.color = "#FFD700"
            lighting_state.intensity = 0.9
        elif preset.name == "soft_wash":
            lighting_state.color = "#E6E6FA"
            lighting_state.intensity = 0.5
        elif preset.name == "high_contrast":
            lighting_state.color = "#FFFFFF"
            lighting_state.intensity = 1.0

        logger.info(f"Lighting preset applied: {request.preset}")

        return ApplyPresetResponse(
            applied=True,
            preset=request.preset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply preset: {e}")
        return ApplyPresetResponse(applied=False, preset=request.preset)


@app.post("/api/lighting/zone", response_model=ZoneResponse)
async def set_zone_lighting(request: ZoneRequest):
    """
    Set lighting for a specific zone.

    Args:
        request: Zone lighting request

    Returns:
        ZoneResponse with applied status
    """
    if not validate_hex_color(request.color):
        raise HTTPException(
            status_code=422,
            detail="Invalid color format. Must be hex color code (#RRGGBB)"
        )

    try:
        # In a real implementation, this would control specific DMX channels
        # for the zone. For now, we just acknowledge the request.
        logger.info(
            f"Zone {request.zone} lighting set: "
            f"{request.color} at intensity {request.intensity}"
        )

        return ZoneResponse(
            zone=request.zone,
            applied=True
        )

    except Exception as e:
        logger.error(f"Failed to set zone lighting: {e}")
        return ZoneResponse(zone=request.zone, applied=False)


@app.post("/api/lighting/effect", response_model=EffectResponse)
async def set_lighting_effect(request: EffectRequest):
    """
    Apply a lighting effect (e.g., strobe, pulse).

    Args:
        request: Effect request

    Returns:
        EffectResponse with started status
    """
    try:
        # Validate effect name
        valid_effects = ["strobe", "pulse", "fade", "rainbow", "sparkle"]
        if request.effect not in valid_effects:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid effect. Valid effects: {', '.join(valid_effects)}"
            )

        params = request.params or EffectParams()
        logger.info(
            f"Lighting effect started: {request.effect} "
            f"(speed: {params.speed}, duration: {params.duration})"
        )

        return EffectResponse(
            effect=request.effect,
            started=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start lighting effect: {e}")
        return EffectResponse(effect=request.effect, started=False)


@app.post("/api/lighting/batch", response_model=BatchResponse)
async def batch_lighting_updates(request: BatchRequest):
    """
    Apply multiple lighting updates in a single request.

    Args:
        request: Batch request with list of updates

    Returns:
        BatchResponse with list of zones that were updated
    """
    updated_zones = []

    try:
        for update in request.updates:
            if not validate_hex_color(update.color):
                logger.warning(f"Invalid color for zone {update.zone}, skipping")
                continue

            # Simulate zone update
            updated_zones.append(update.zone)
            logger.info(
                f"Batch update: zone {update.zone} -> "
                f"{update.color} at intensity {update.intensity}"
            )

        return BatchResponse(updated=updated_zones)

    except Exception as e:
        logger.error(f"Failed to apply batch updates: {e}")
        return BatchResponse(updated=[])


@app.post("/api/lighting/reset", response_model=ResetResponse)
async def reset_lighting():
    """
    Reset lighting to default state.

    Returns:
        ResetResponse with reset status
    """
    try:
        lighting_state.color = "#FFFFFF"
        lighting_state.intensity = 1.0
        lighting_state.scene = "default"

        # Also reset DMX controller
        await dmx_controller.reset()

        logger.info("Lighting reset to default")

        return ResetResponse(reset=True)

    except Exception as e:
        logger.error(f"Failed to reset lighting: {e}")
        return ResetResponse(reset=False)


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
