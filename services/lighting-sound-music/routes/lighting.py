"""Lighting control routes."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from ..models.request import LightingRequest, OSCMessageRequest
from ..models.response import LightingResponse, LightingState, OSCResponse
from ..models.response import FixtureState

router = APIRouter()


def _get_handler():
    """Get the lighting handler instance."""
    from ....main import handler
    return handler


@router.post("/v1/lighting/set", response_model=LightingResponse)
async def set_lighting(request: LightingRequest) -> LightingResponse:
    """Set lighting values via sACN.

    Args:
        request: Lighting request with universe, channels, fade time

    Returns:
        Lighting response with status and timing
    """
    handler = _get_handler()

    import time
    start_time = time.time()

    # Set channels via sACN
    success = await handler.sacn.set_channels(request.values)

    # Calculate affected fixtures
    affected_fixtures = []
    for fixture_id, fixture_state in handler.fixture_manager.get_all_fixtures().items():
        # Check if any of the fixture's channels are in the request
        fixture_channels = range(
            fixture_state.dmx_address,
            fixture_state.dmx_address + len(fixture_state.channel_values)
        )
        if any(ch in fixture_channels for ch in request.values.keys()):
            affected_fixtures.append(fixture_id)
            # Update fixture state
            handler.fixture_manager.update_fixture(
                fixture_id,
                list(request.values.values())[:len(fixture_state.channel_values)],
                1.0
            )

    fade_time = request.fade_time
    if fade_time > 0:
        await _simulate_fade(fade_time)

    total_time = time.time() - start_time

    return LightingResponse(
        status="success" if success else "failed",
        affected_fixtures=affected_fixtures,
        timing={"fade": fade_time, "total": total_time},
        universe=request.universe,
        channels_updated=len(request.values)
    )


@router.post("/v1/lighting/fixture/{fixture_id}", response_model=LightingResponse)
async def set_fixture(
    fixture_id: str,
    channel_values: list[int],
    intensity: float = 1.0
) -> LightingResponse:
    """Set values for a specific fixture.

    Args:
        fixture_id: Fixture identifier
        channel_values: List of channel values
        intensity: Intensity modifier (0.0-1.0)

    Returns:
        Lighting response
    """
    handler = _get_handler()

    import time
    start_time = time.time()

    # Set fixture via sACN
    success = await handler.sacn.set_fixture(fixture_id, channel_values, intensity)

    # Update fixture manager
    handler.fixture_manager.update_fixture(fixture_id, channel_values, intensity)

    total_time = time.time() - start_time

    return LightingResponse(
        status="success" if success else "failed",
        affected_fixtures=[fixture_id] if success else [],
        timing={"total": total_time},
        universe=handler.sacn.universe,
        channels_updated=len(channel_values)
    )


@router.get("/v1/lighting/state", response_model=LightingState)
async def get_lighting_state() -> LightingState:
    """Get current lighting system state.

    Returns:
        Current lighting state including all fixtures
    """
    handler = _get_handler()

    # Build fixture states
    fixtures = handler.fixture_manager.get_all_fixtures()

    return LightingState(
        universe=handler.sacn.universe,
        dmx_values=await handler.sacn.get_all_channels(),
        fixtures=fixtures,
        active_preset=handler.fixture_manager.get_active_preset(),
        active_cue=handler.cue_executor.get_current_cue(),
        sACN_active=handler.sacn.is_active,
        OSC_active=handler.osc.client_connected
    )


@router.post("/v1/lighting/blackout", response_model=LightingResponse)
async def blackout() -> LightingResponse:
    """Blackout all lighting.

    Returns:
        Lighting response
    """
    handler = _get_handler()

    import time
    start_time = time.time()

    success = await handler.sacn.blackout()
    handler.fixture_manager.clear_active_preset()

    total_time = time.time() - start_time

    return LightingResponse(
        status="success" if success else "failed",
        affected_fixtures=list(handler.fixture_manager.get_all_fixtures().keys()),
        timing={"total": total_time},
        universe=handler.sacn.universe,
        channels_updated=512
    )


@router.post("/v1/lighting/channel/{channel:int}", response_model=LightingResponse)
async def set_channel(channel: int, value: int) -> LightingResponse:
    """Set a single DMX channel.

    Args:
        channel: DMX channel number (1-512)
        value: DMX value (0-255)

    Returns:
        Lighting response
    """
    handler = _get_handler()

    if not 1 <= channel <= 512:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel: {channel}. Must be 1-512."
        )

    if not 0 <= value <= 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {value}. Must be 0-255."
        )

    success = await handler.sacn.set_channel(channel, value)

    return LightingResponse(
        status="success" if success else "failed",
        affected_fixtures=[],
        timing={},
        universe=handler.sacn.universe,
        channels_updated=1
    )


@router.post("/v1/osc/send", response_model=OSCResponse)
async def send_osc(request: OSCMessageRequest) -> OSCResponse:
    """Send an OSC message.

    Args:
        request: OSC message request

    Returns:
        OSC response
    """
    handler = _get_handler()

    from datetime import datetime, timezone

    success = await handler.osc.send(request.address, *request.arguments)

    return OSCResponse(
        sent=success,
        address=request.address,
        host=request.host,
        port=request.port,
        timestamp=datetime.now(timezone.utc),
        error_message=None if success else "Failed to send OSC message"
    )


async def _simulate_fade(fade_time: float) -> None:
    """Simulate fade transition.

    Args:
        fade_time: Fade time in seconds
    """
    if fade_time > 0:
        import asyncio
        await asyncio.sleep(fade_time)
