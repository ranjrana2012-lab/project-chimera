"""
Business metrics for Lighting-Sound-Music Service.

Provides Prometheus metrics for lighting, audio, and synchronization tracking.
"""

from prometheus_client import Gauge, Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Lighting cue execution duration
lighting_cue_duration = Histogram(
    'lsm_lighting_cue_duration_seconds',
    'Time spent executing lighting cues',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

# Lighting cue success rate
lighting_cue_success = Counter(
    'lsm_lighting_cue_success_total',
    'Successful lighting cue executions',
    ['scene_id']
)

lighting_cue_failure = Counter(
    'lsm_lighting_cue_failure_total',
    'Failed lighting cue executions',
    ['scene_id']
)

# DMX channel usage
dmx_channels_used = Gauge(
    'lsm_dmx_channels_used',
    'Number of DMX channels currently in use',
    ['universe']
)

# Audio cue execution duration
audio_cue_duration = Histogram(
    'lsm_audio_cue_duration_seconds',
    'Time spent executing audio cues',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

# Audio cue success rate
audio_cue_success = Counter(
    'lsm_audio_cue_success_total',
    'Successful audio cue executions',
    ['cue_id']
)

audio_cue_failure = Counter(
    'lsm_audio_cue_failure_total',
    'Failed audio cue executions',
    ['cue_id']
)

# Audio playback duration
audio_playback_time = Counter(
    'lsm_audio_playback_time_seconds_total',
    'Total time audio has been playing',
    ['cue_id']
)

# Sync scene execution duration
sync_scene_duration = Histogram(
    'lsm_sync_scene_duration_seconds',
    'Time spent executing synchronized scenes',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Sync offset measurement
sync_offset_ms = Histogram(
    'lsm_sync_offset_milliseconds',
    'Synchronization offset between lighting and audio in milliseconds',
    buckets=[1, 5, 10, 25, 50, 100, 200, 500]
)

# Sync success rate (within tolerance)
sync_success = Counter(
    'lsm_sync_success_total',
    'Successful synchronized scenes (within tolerance)',
    ['scene_id']
)

sync_failure = Counter(
    'lsm_sync_failure_total',
    'Failed synchronized scenes (outside tolerance or error)',
    ['scene_id']
)


def record_lighting_cue(
    scene_id: str,
    channel_count: int,
    duration: float,
    success: bool
) -> None:
    """
    Record a lighting cue execution event.

    Args:
        scene_id: The scene identifier
        channel_count: Number of DMX channels used
        duration: Time taken for execution in seconds
        success: Whether the cue executed successfully
    """
    try:
        lighting_cue_duration.observe(duration)

        if success:
            lighting_cue_success.labels(scene_id=scene_id).inc()
            dmx_channels_used.labels(universe=1).set(channel_count)
        else:
            lighting_cue_failure.labels(scene_id=scene_id).inc()

        logger.debug(
            f"Recorded lighting cue: scene={scene_id}, "
            f"channels={channel_count}, duration={duration:.3f}s, success={success}"
        )
    except Exception as e:
        logger.error(f"Failed to record lighting cue metrics: {e}")


def record_audio_cue(
    cue_id: str,
    duration: float,
    success: bool
) -> None:
    """
    Record an audio cue execution event.

    Args:
        cue_id: The cue identifier
        duration: Time taken for execution in seconds
        success: Whether the cue executed successfully
    """
    try:
        audio_cue_duration.observe(duration)

        if success:
            audio_cue_success.labels(cue_id=cue_id).inc()
        else:
            audio_cue_failure.labels(cue_id=cue_id).inc()

        logger.debug(
            f"Recorded audio cue: cue={cue_id}, "
            f"duration={duration:.3f}s, success={success}"
        )
    except Exception as e:
        logger.error(f"Failed to record audio cue metrics: {e}")


def record_audio_playback_time(cue_id: str, seconds: float) -> None:
    """
    Record audio playback time.

    Args:
        cue_id: The cue identifier
        seconds: Time spent playing in seconds
    """
    try:
        audio_playback_time.labels(cue_id=cue_id).inc(seconds)

        logger.debug(
            f"Recorded audio playback time: cue={cue_id}, seconds={seconds:.1f}"
        )
    except Exception as e:
        logger.error(f"Failed to record audio playback time: {e}")


def record_sync_scene(
    scene_id: str,
    duration: float,
    success: bool,
    offset_ms: float = 0.0
) -> None:
    """
    Record a synchronized scene execution event.

    Args:
        scene_id: The scene identifier
        duration: Time taken for execution in seconds
        success: Whether the sync was successful
        offset_ms: Synchronization offset in milliseconds
    """
    try:
        sync_scene_duration.observe(duration)

        if offset_ms > 0:
            sync_offset_ms.observe(offset_ms)

        if success:
            sync_success.labels(scene_id=scene_id).inc()
        else:
            sync_failure.labels(scene_id=scene_id).inc()

        logger.debug(
            f"Recorded sync scene: scene={scene_id}, "
            f"duration={duration:.3f}s, success={success}, offset={offset_ms:.1f}ms"
        )
    except Exception as e:
        logger.error(f"Failed to record sync scene metrics: {e}")


__all__ = [
    "lighting_cue_duration",
    "lighting_cue_success",
    "lighting_cue_failure",
    "dmx_channels_used",
    "audio_cue_duration",
    "audio_cue_success",
    "audio_cue_failure",
    "audio_playback_time",
    "sync_scene_duration",
    "sync_offset_ms",
    "sync_success",
    "sync_failure",
    "record_lighting_cue",
    "record_audio_cue",
    "record_audio_playback_time",
    "record_sync_scene",
]
