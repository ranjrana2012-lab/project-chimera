"""Lighting preset management routes."""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Any, Optional

from ..models.request import PresetRequest, FixtureValues
from ..models.response import PresetResponse, LightingResponse

router = APIRouter()


def _get_handler():
    """Get the lighting handler instance."""
    from ....main import handler
    return handler


@router.get("/v1/presets", response_model=Dict[str, Any])
async def list_presets() -> Dict[str, Any]:
    """List all available presets.

    Returns:
        Dictionary of preset names and metadata
    """
    handler = _get_handler()

    presets = handler.fixture_manager.get_all_presets()
    preset_list = {}

    for name, preset in presets.items():
        preset_list[name] = {
            "name": preset.name,
            "description": preset.description,
            "fade_time": preset.fade_time,
            "fixture_count": len(preset.fixtures),
            "created_at": preset.created_at.isoformat()
        }

    return {
        "presets": preset_list,
        "active": handler.fixture_manager.get_active_preset(),
        "total": len(preset_list)
    }


@router.get("/v1/presets/{name}", response_model=Dict[str, Any])
async def get_preset(name: str) -> Dict[str, Any]:
    """Get a specific preset.

    Args:
        name: Preset name

    Returns:
        Preset details
    """
    handler = _get_handler()

    preset = handler.fixture_manager.get_preset(name)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{name}' not found"
        )

    return {
        "name": preset.name,
        "description": preset.description,
        "values": preset.values,
        "fixtures": preset.fixtures,
        "fade_time": preset.fade_time,
        "created_at": preset.created_at.isoformat()
    }


@router.post("/v1/presets", response_model=PresetResponse)
async def create_preset(request: PresetRequest) -> PresetResponse:
    """Create a new lighting preset.

    Args:
        request: Preset creation request

    Returns:
        Preset response
    """
    handler = _get_handler()
    return await handler.fixture_manager.create_preset(request)


@router.put("/v1/presets/{name}", response_model=PresetResponse)
async def update_preset(name: str, request: PresetRequest) -> PresetResponse:
    """Update an existing preset.

    Args:
        name: Preset name
        request: Updated preset data

    Returns:
        Preset response
    """
    handler = _get_handler()

    # Ensure the request name matches the URL parameter
    request.name = name
    return await handler.fixture_manager.update_preset(name, request)


@router.delete("/v1/presets/{name}", response_model=Dict[str, str])
async def delete_preset(name: str) -> Dict[str, str]:
    """Delete a preset.

    Args:
        name: Preset name

    Returns:
        Deletion confirmation
    """
    handler = _get_handler()

    success = await handler.fixture_manager.delete_preset(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{name}' not found"
        )

    return {"status": "deleted", "name": name}


@router.post("/v1/presets/{name}/recall", response_model=LightingResponse)
async def recall_preset(
    name: str,
    fade_time: Optional[float] = Query(None, description="Override fade time")
) -> LightingResponse:
    """Recall (apply) a preset.

    Args:
        name: Preset name
        fade_time: Optional fade time override

    Returns:
        Lighting response
    """
    handler = _get_handler()

    import time
    start_time = time.time()

    # Get preset values
    values = await handler.fixture_manager.apply_preset(name, fade_time)
    if not values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{name}' not found"
        )

    # Apply via sACN
    success = await handler.sacn.set_channels(values)

    # Get fade time
    if fade_time is None:
        fade_time = handler.fixture_manager.get_preset_fade_time(name)

    # Simulate fade
    if fade_time > 0:
        import asyncio
        await asyncio.sleep(fade_time)

    total_time = time.time() - start_time

    # Get affected fixtures
    affected_fixtures = list(values.keys())

    return LightingResponse(
        status="success" if success else "failed",
        affected_fixtures=[],
        timing={"fade": fade_time, "total": total_time},
        universe=handler.sacn.universe,
        channels_updated=len(values)
    )


@router.post("/v1/presets/save", response_model=PresetResponse)
async def save_current_state(
    name: str,
    fade_time: float = Query(0.0, description="Default fade time"),
    description: str = Query("", description="Preset description")
) -> PresetResponse:
    """Save current fixture state as a preset.

    Args:
        name: Preset name
        fade_time: Default fade time
        description: Preset description

    Returns:
        Preset response
    """
    handler = _get_handler()

    preset = handler.fixture_manager.create_from_current_state(
        name=name,
        fade_time=fade_time,
        description=description
    )

    await handler.fixture_manager._save_presets()

    return PresetResponse(
        name=name,
        saved=True,
        values=preset.values,
        fixtures=preset.fixtures,
        fade_time=fade_time
    )


@router.post("/v1/presets/import", response_model=Dict[str, Any])
async def import_presets(data: Dict[str, Any]) -> Dict[str, Any]:
    """Import presets from dictionary data.

    Args:
        data: Preset data dictionary

    Returns:
        Import result
    """
    handler = _get_handler()

    count = await handler.fixture_manager.import_presets(data)

    return {
        "status": "imported",
        "count": count
    }


@router.get("/v1/presets/export", response_model=Dict[str, Any])
async def export_presets() -> Dict[str, Any]:
    """Export all presets.

    Returns:
        All preset data
    """
    handler = _get_handler()
    return handler.fixture_manager.export_presets()
