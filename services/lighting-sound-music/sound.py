"""Sound Module - Sound effects, playback, and mixing.

This module provides sound effects playback, volume control, and audio mixing
for theatrical productions. Supports multiple concurrent sounds with
independent volume and looping controls.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import asyncio
import os
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Configuration
SOUNDS_DIR = Path("./assets/sounds/")
MAX_CONCURRENT_SOUNDS = 8


class SoundCategory(str, Enum):
    """Sound effect categories."""
    EFFECTS = "effects"
    AMBIENT = "ambient"
    TRANSITIONS = "transitions"


# Request/Response Models
class SoundPlayRequest(BaseModel):
    """Request to play a sound effect."""
    sound_name: str
    category: SoundCategory = SoundCategory.EFFECTS
    volume: float = 1.0  # 0.0 to 1.0
    loop: bool = False
    duration: Optional[float] = None  # For ambient sounds, seconds


class VolumeRequest(BaseModel):
    """Request to set volume."""
    volume: float  # 0.0 to 1.0


class SoundInfo(BaseModel):
    """Information about a sound file."""
    name: str
    category: SoundCategory
    file_path: str
    duration: Optional[float] = None
    tags: List[str] = []


class ActiveSound(BaseModel):
    """Information about an actively playing sound."""
    sound_id: str
    sound_name: str
    volume: float
    loop: bool
    start_time: float


# In-memory state
_active_sounds: Dict[str, ActiveSound] = {}
_sound_catalog: Dict[str, SoundInfo] = {}
_master_volume = 1.0
_next_sound_id = 1


async def _load_sound_catalog():
    """Load sound effects catalog from disk.

    Scans the SOUNDS_DIR for audio files and builds the catalog.
    """
    global _sound_catalog

    for category in SoundCategory:
        category_path = SOUNDS_DIR / category.value
        if not category_path.exists():
            continue

        for audio_file in category_path.glob("*"):
            if audio_file.suffix in [".wav", ".mp3", ".flac", ".ogg"]:
                sound_name = audio_file.stem
                _sound_catalog[sound_name] = SoundInfo(
                    name=sound_name,
                    category=category,
                    file_path=str(audio_file),
                    tags=[]
                )

    logger.info(f"Loaded {len(_sound_catalog)} sounds into catalog")


async def _play_sound_worker(sound_id: str, sound_info: SoundInfo, volume: float, loop: bool, duration: Optional[float]):
    """Worker function to play sound in background.

    TODO: Implement actual audio playback using soundfile/pyaudio.
    """
    try:
        # TODO: Load and play audio file
        # import soundfile as sf
        # import pyaudio

        logger.info(f"Playing sound: {sound_info.name} (id={sound_id})")

        # Simulate playback
        play_duration = duration if duration else 2.0  # Default 2 seconds

        while loop or sound_id in _active_sounds:
            await asyncio.sleep(play_duration)
            if not loop:
                break

    except Exception as e:
        logger.error(f"Error playing sound {sound_id}: {e}")
    finally:
        # Clean up if not looping
        if sound_id in _active_sounds and not _active_sounds[sound_id].loop:
            del _active_sounds[sound_id]


@router.get("/status")
async def get_status() -> Dict:
    """Get current sound system status.

    Returns:
        Current status of sound subsystem
    """
    return {
        "status": "ready",
        "master_volume": _master_volume,
        "active_sounds_count": len(_active_sounds),
        "catalog_size": len(_sound_catalog),
        "max_concurrent": MAX_CONCURRENT_SOUNDS,
        "active_sounds": list(_active_sounds.values())
    }


@router.get("/sounds")
async def list_sounds(category: Optional[SoundCategory] = None) -> Dict:
    """List all available sounds.

    Args:
        category: Optional filter by category

    Returns:
        Dictionary of sounds by category
    """
    if category:
        return {
            "sounds": [
                s for s in _sound_catalog.values() if s.category == category
            ],
            "count": len([s for s in _sound_catalog.values() if s.category == category])
        }

    # Group by category
    result = {
        "effects": [],
        "ambient": [],
        "transitions": []
    }

    for sound in _sound_catalog.values():
        result[sound.category.value].append(sound)

    return result


@router.post("/play")
async def play_sound(request: SoundPlayRequest, background_tasks: BackgroundTasks) -> Dict:
    """Play a sound effect.

    Args:
        request: Sound play request
        background_tasks: FastAPI background tasks

    Returns:
        Playback status
    """
    global _next_sound_id

    # Validate volume
    if not 0.0 <= request.volume <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volume must be between 0.0 and 1.0"
        )

    # Check if sound exists
    if request.sound_name not in _sound_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sound not found: {request.sound_name}"
        )

    # Check concurrent sound limit
    if len(_active_sounds) >= MAX_CONCURRENT_SOUNDS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Maximum concurrent sounds ({MAX_CONCURRENT_SOUNDS}) reached"
        )

    # Create active sound record
    sound_id = f"sound_{_next_sound_id}"
    _next_sound_id += 1

    sound_info = _sound_catalog[request.sound_name]
    import time
    active_sound = ActiveSound(
        sound_id=sound_id,
        sound_name=request.sound_name,
        volume=request.volume * _master_volume,
        loop=request.loop,
        start_time=time.time()
    )
    _active_sounds[sound_id] = active_sound

    # Start background playback
    background_tasks.add_task(
        _play_sound_worker,
        sound_id,
        sound_info,
        active_sound.volume,
        request.loop,
        request.duration
    )

    logger.info(f"Started sound: {request.sound_name} (id={sound_id})")

    return {
        "status": "playing",
        "sound_id": sound_id,
        "sound_name": request.sound_name,
        "volume": active_sound.volume
    }


@router.post("/stop")
async def stop_sound(sound_id: Optional[str] = None) -> Dict:
    """Stop playing sound(s).

    Args:
        sound_id: Optional specific sound ID to stop. If None, stops all sounds.

    Returns:
        Stop status
    """
    if sound_id:
        if sound_id not in _active_sounds:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sound not found: {sound_id}"
            )
        del _active_sounds[sound_id]
        logger.info(f"Stopped sound: {sound_id}")
        return {"status": "stopped", "sound_id": sound_id}
    else:
        # Stop all sounds
        stopped_ids = list(_active_sounds.keys())
        _active_sounds.clear()
        logger.info(f"Stopped all sounds: {stopped_ids}")
        return {"status": "stopped_all", "stopped_sounds": stopped_ids}


@router.post("/volume")
async def set_volume(request: VolumeRequest) -> Dict:
    """Set master volume.

    Args:
        request: Volume request

    Returns:
        New volume setting
    """
    global _master_volume

    if not 0.0 <= request.volume <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volume must be between 0.0 and 1.0"
        )

    _master_volume = request.volume
    logger.info(f"Set master volume to {_master_volume}")

    return {"volume": _master_volume}


@router.get("/volume")
async def get_volume() -> Dict:
    """Get current master volume.

    Returns:
        Current volume
    """
    return {"volume": _master_volume}


@router.get("/catalog/reload")
async def reload_catalog() -> Dict:
    """Reload the sound effects catalog from disk.

    Returns:
        Updated catalog count
    """
    await _load_sound_catalog()
    return {
        "status": "reloaded",
        "catalog_size": len(_sound_catalog)
    }


@router.delete("/catalog/{sound_name}")
async def delete_sound(sound_name: str) -> Dict:
    """Remove a sound from the catalog (doesn't delete file).

    Args:
        sound_name: Name of sound to remove

    Returns:
        Deletion status
    """
    if sound_name not in _sound_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sound not found: {sound_name}"
        )

    del _sound_catalog[sound_name]
    logger.info(f"Removed sound from catalog: {sound_name}")

    return {"status": "removed", "sound_name": sound_name}


@router.post("/catalog")
async def add_sound(sound_name: str, category: SoundCategory, file_path: str, tags: List[str] = []) -> Dict:
    """Add a sound to the catalog.

    Args:
        sound_name: Name for the sound
        category: Sound category
        file_path: Path to audio file
        tags: Optional tags

    Returns:
        Added sound info
    """
    if sound_name in _sound_catalog:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sound already exists: {sound_name}"
        )

    _sound_catalog[sound_name] = SoundInfo(
        name=sound_name,
        category=category,
        file_path=file_path,
        tags=tags
    )

    logger.info(f"Added sound to catalog: {sound_name}")

    return {
        "status": "added",
        "sound": _sound_catalog[sound_name]
    }
