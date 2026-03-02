"""Cues Module - Coordinated multi-media scenes.

This module provides coordinated execution of lighting, sound, and music
cues for theatrical productions. It manages timelines, scene presets,
and synchronization primitives.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from schemas import (
    CoordinatedCue,
    CueState,
    CueExecutionRequest,
    CueLibraryEntry,
    CueExecutionStatus,
    TimelineEvent,
    LightingCue,
    SoundCue,
    MusicCue
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Configuration
MAX_CONCURRENT_CUES = 4
DEFAULT_FADE_TIME = 1.0

# In-memory state
_cue_library: Dict[str, CoordinatedCue] = {}
_active_executions: Dict[str, CueExecutionStatus] = {}
_execution_history: List[Dict] = []
_next_execution_id = 1


async def _execute_lighting_cue(cue: LightingCue, delay: float = 0.0):
    """Execute a lighting cue.

    TODO: Integrate with actual lighting module.
    """
    if delay > 0:
        await asyncio.sleep(delay)

    logger.info(f"Lighting cue: fixture={cue.fixture_id}, intensity={cue.intensity}")

    # TODO: Call actual lighting module
    # await lighting.set_fixture(cue.fixture_id, cue.dmx_values, cue.intensity)


async def _execute_sound_cue(cue: SoundCue, delay: float = 0.0):
    """Execute a sound cue.

    TODO: Integrate with actual sound module.
    """
    if delay > 0:
        await asyncio.sleep(delay)

    logger.info(f"Sound cue: sound={cue.sound_name}, volume={cue.volume}")

    # TODO: Call actual sound module
    # await sound.play_sound(cue.sound_name, cue.volume)


async def _execute_music_cue(cue: MusicCue, delay: float = 0.0):
    """Execute a music cue.

    TODO: Integrate with actual music module.
    """
    if delay > 0:
        await asyncio.sleep(delay)

    logger.info(f"Music cue: action={cue.action}, track={cue.track_id}")

    # TODO: Call actual music module
    # if cue.action == "play":
    #     await music.play_track(cue.track_id, cue.volume, fade_time=cue.fade_time)
    # elif cue.action == "stop":
    #     await music.stop()
    # elif cue.action == "fade":
    #     await music.set_volume(cue.volume, cue.fade_time)


async def _build_timeline(cue: CoordinatedCue) -> List[TimelineEvent]:
    """Build execution timeline from coordinated cue.

    Args:
        cue: Coordinated cue

    Returns:
        List of timeline events
    """
    events = []

    # Add lighting events
    for lighting_cue in cue.lighting:
        events.append(TimelineEvent(
            time=0.0,
            module="lighting",
            action="set_fixture",
            parameters={
                "fixture_id": lighting_cue.fixture_id,
                "intensity": lighting_cue.intensity,
                "color": lighting_cue.color,
                "fade_time": lighting_cue.fade_time
            }
        ))

    # Add sound events
    for sound_cue in cue.sound:
        events.append(TimelineEvent(
            time=sound_cue.start_time,
            module="sound",
            action="play",
            parameters={
                "sound_name": sound_cue.sound_name,
                "volume": sound_cue.volume,
                "fade_in": sound_cue.fade_in
            }
        ))

    # Add music event
    if cue.music:
        events.append(TimelineEvent(
            time=cue.music.start_time,
            module="music",
            action=cue.music.action,
            parameters={
                "track_id": cue.music.track_id,
                "volume": cue.music.volume,
                "fade_time": cue.music.fade_time
            }
        ))

    # Sort by time
    events.sort(key=lambda e: e.time)

    return events


async def _execute_cue_worker(cue_name: str, execution_id: str):
    """Worker to execute a coordinated cue.

    Args:
        cue_name: Name of the cue to execute
        execution_id: Unique execution ID
    """
    try:
        if cue_name not in _cue_library:
            _active_executions[execution_id].state = CueState.FAILED
            _active_executions[execution_id].error = f"Cue not found: {cue_name}"
            return

        cue = _cue_library[cue_name]
        status = _active_executions[execution_id]
        status.state = CueState.RUNNING
        status.started_at = datetime.now().isoformat()

        # Build timeline
        timeline = await _build_timeline(cue)

        # Execute timeline events
        for event in timeline:
            if status.state == CueState.STOPPED:
                break

            # Wait until event time
            await asyncio.sleep(event.time)

            # Execute based on module
            if event.module == "lighting":
                lighting_cue = LightingCue(**event.parameters)
                await _execute_lighting_cue(lighting_cue)
            elif event.module == "sound":
                sound_cue = SoundCue(**event.parameters)
                await _execute_sound_cue(sound_cue)
            elif event.module == "music":
                music_cue = MusicCue(**event.parameters)
                await _execute_music_cue(music_cue)

            # Update progress
            status.progress = event.time / cue.duration

        # Wait for any remaining duration
        remaining_time = cue.duration - (timeline[-1].time if timeline else 0)
        if remaining_time > 0 and status.state != CueState.STOPPED:
            await asyncio.sleep(remaining_time)

        # Mark complete
        if status.state != CueState.STOPPED:
            status.state = CueState.COMPLETED
            status.progress = 1.0

        status.completed_at = datetime.now().isoformat()

        # Update execution history
        if cue_name in _cue_library:
            # Find and update library entry
            for entry in _cue_library.values():
                if entry.name == cue_name:
                    # Update metadata
                    if "execution_count" not in entry.metadata:
                        entry.metadata["execution_count"] = 0
                    entry.metadata["execution_count"] += 1
                    entry.metadata["last_executed"] = datetime.now().isoformat()
                    break

        logger.info(f"Cue execution complete: {cue_name}")

    except Exception as e:
        logger.error(f"Cue execution failed: {cue_name} - {e}")
        if execution_id in _active_executions:
            _active_executions[execution_id].state = CueState.FAILED
            _active_executions[execution_id].error = str(e)
            _active_executions[execution_id].completed_at = datetime.now().isoformat()


@router.get("/library")
async def list_cues() -> Dict:
    """List all saved cues.

    Returns:
        Dictionary of all cues in the library
    """
    entries = []
    for cue in _cue_library.values():
        entries.append(CueLibraryEntry(
            name=cue.name,
            description=cue.description,
            duration=cue.duration,
            created_at=cue.metadata.get("created_at", ""),
            tags=cue.tags,
            last_executed=cue.metadata.get("last_executed"),
            execution_count=cue.metadata.get("execution_count", 0)
        ))

    return {
        "cues": entries,
        "count": len(_cue_library)
    }


@router.post("/library")
async def save_cue(cue: CoordinatedCue) -> Dict:
    """Save a cue to the library.

    Args:
        cue: Coordinated cue to save

    Returns:
        Save confirmation
    """
    if cue.name in _cue_library:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cue already exists: {cue.name}"
        )

    # Add metadata
    cue.metadata["created_at"] = datetime.now().isoformat()
    cue.metadata["execution_count"] = 0

    _cue_library[cue.name] = cue

    logger.info(f"Saved cue: {cue.name}")

    return {"status": "saved", "name": cue.name}


@router.get("/library/{cue_name}")
async def get_cue(cue_name: str) -> CoordinatedCue:
    """Get a specific cue from library.

    Args:
        cue_name: Name of the cue

    Returns:
        The coordinated cue
    """
    if cue_name not in _cue_library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue not found: {cue_name}"
        )

    return _cue_library[cue_name]


@router.put("/library/{cue_name}")
async def update_cue(cue_name: str, cue: CoordinatedCue) -> Dict:
    """Update an existing cue.

    Args:
        cue_name: Name of the cue to update
        cue: Updated cue data

    Returns:
        Update confirmation
    """
    if cue_name not in _cue_library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue not found: {cue_name}"
        )

    # Preserve metadata
    cue.metadata = _cue_library[cue_name].metadata
    _cue_library[cue_name] = cue

    logger.info(f"Updated cue: {cue_name}")

    return {"status": "updated", "name": cue_name}


@router.delete("/library/{cue_name}")
async def delete_cue(cue_name: str) -> Dict:
    """Delete a cue from the library.

    Args:
        cue_name: Name of the cue to delete

    Returns:
        Deletion confirmation
    """
    if cue_name not in _cue_library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue not found: {cue_name}"
        )

    del _cue_library[cue_name]

    logger.info(f"Deleted cue: {cue_name}")

    return {"status": "deleted", "name": cue_name}


@router.post("/execute")
async def execute_cue(request: CueExecutionRequest, background_tasks: BackgroundTasks) -> Dict:
    """Execute a coordinated cue.

    Args:
        request: Cue execution request
        background_tasks: FastAPI background tasks

    Returns:
        Execution status
    """
    global _next_execution_id

    if request.cue_name not in _cue_library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue not found: {request.cue_name}"
        )

    # Check concurrent limit
    if len(_active_executions) >= MAX_CONCURRENT_CUES:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Maximum concurrent cues ({MAX_CONCURRENT_CUES}) reached"
        )

    # Create execution status
    execution_id = f"exec_{_next_execution_id}"
    _next_execution_id += 1

    execution_status = CueExecutionStatus(
        cue_name=request.cue_name,
        state=CueState.PENDING,
        started_at=None,
        completed_at=None,
        elapsed=None,
        progress=0.0
    )

    _active_executions[execution_id] = execution_status

    # Start background execution
    if request.background:
        asyncio.create_task(_execute_cue_worker(request.cue_name, execution_id))
    else:
        await _execute_cue_worker(request.cue_name, execution_id)

    logger.info(f"Started cue execution: {request.cue_name}")

    return {
        "status": "started",
        "cue_name": request.cue_name,
        "execution_id": execution_id
    }


@router.post("/stop/{execution_id}")
async def stop_cue(execution_id: str) -> Dict:
    """Stop a running cue.

    Args:
        execution_id: Execution ID to stop

    Returns:
        Stop confirmation
    """
    if execution_id not in _active_executions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )

    _active_executions[execution_id].state = CueState.STOPPED

    logger.info(f"Stopped cue execution: {execution_id}")

    return {"status": "stopped", "execution_id": execution_id}


@router.get("/status")
async def get_cue_status() -> Dict:
    """Get status of all active cue executions.

    Returns:
        Active executions status
    """
    return {
        "active_executions": _active_executions,
        "count": len(_active_executions),
        "max_concurrent": MAX_CONCURRENT_CUES
    }


@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str) -> CueExecutionStatus:
    """Get status of a specific execution.

    Args:
        execution_id: Execution ID

    Returns:
        Execution status
    """
    if execution_id not in _active_executions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )

    return _active_executions[execution_id]


@router.get("/history")
async def get_execution_history(limit: int = 50) -> Dict:
    """Get execution history.

    Args:
        limit: Maximum number of history entries to return

    Returns:
        Execution history
    """
    return {
        "history": _execution_history[-limit:],
        "count": len(_execution_history)
    }


@router.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    """WebSocket endpoint for real-time cue execution updates.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()

    try:
        while True:
            # Send current active executions
            await websocket.send_json({
                "active_executions": {
                    eid: status.dict()
                    for eid, status in _active_executions.items()
                }
            })

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/preset/{preset_name}")
async def load_preset(preset_name: str) -> Dict:
    """Load a preset scene into the cue library.

    Args:
        preset_name: Name of the preset to load

    Returns:
        Load confirmation
    """
    # TODO: Implement preset loading from file
    presets = {
        "blackout": CoordinatedCue(
            name="blackout",
            description="Complete blackout - all lights off, all audio stopped",
            duration=1.0,
            lighting=[],
            sound=[],
            music=MusicCue(action="stop"),
            tags=["emergency", "reset"]
        ),
        "opening": CoordinatedCue(
            name="opening",
            description="Opening scene - warm lights, ambient music",
            duration=5.0,
            lighting=[
                LightingCue(fixture_id="all", intensity=0.7, color="#FFA500", fade_time=3.0)
            ],
            sound=[
                SoundCue(sound_name="ambient-theater", volume=0.3, start_time=0.0)
            ],
            music=MusicCue(action="play", track_id="opening-theme", volume=0.5, fade_time=2.0),
            tags=["opening", "preset"]
        )
    }

    if preset_name not in presets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset not found: {preset_name}"
        )

    cue = presets[preset_name]
    return await save_cue(cue)
