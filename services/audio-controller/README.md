# Audio Controller Service

Project Chimera Phase 2 - Audio system control service for live theatrical performances.

## Overview

The Audio Controller Service provides safe audio system control with emergency mute functionality for live theatrical performances. It manages audio tracks, volume control, and provides real-time mixing with safety features.

## Features

- **Multi-Track Support**: Control multiple audio tracks independently
- **Safe Volume Control**: Automatic volume limiting and safe defaults
- **Emergency Mute**: Instant mute for all audio (safety critical)
- **Fade In/Out**: Smooth transitions with configurable fade times
- **Master Volume**: Control all tracks simultaneously
- **Output Management**: Support for multiple audio outputs
- **Callback System**: Register callbacks for emergency events

## Installation

```bash
# Install dependencies
pip install -e .[audio]

# Or install with all Phase 2 dependencies
pip install -e .[all]
```

## Quick Start

```python
from audio_controller import AudioController, AudioTrack

# Create controller
controller = AudioController(sample_rate=48000, bit_depth=24)

# Create and add tracks
dialogue = AudioTrack(
    id="dialogue",
    name="AI Dialogue",
    url="/assets/dialogue.mp3",
    volume_db=-20.0
)
music = AudioTrack(
    id="music",
    name="Background Music",
    url="/assets/music.mp3",
    volume_db=-30.0
)

controller.add_track(dialogue)
controller.add_track(music)

# Control playback
controller.play_track("dialogue", fade_in_ms=500)
controller.set_track_volume("dialogue", -15.0)
controller.stop_track("dialogue", fade_out_ms=1000)
```

## Usage Examples

See `examples/audio_example.py` for comprehensive usage examples including:
- Basic audio playback
- Volume control
- Mute/unmute functionality
- Emergency mute scenarios
- Complete audio sequences

Run the example:
```bash
cd services/audio-controller
python examples/audio_example.py
```

## Testing

```bash
# Run all tests
pytest tests/test_audio_controller.py -v

# Run with coverage
pytest tests/test_audio_controller.py --cov=audio_controller --cov-report=html

# Run specific test
pytest tests/test_audio_controller.py::TestAudioController::test_emergency_mute -v
```

## API Reference

### AudioController

Main controller class for audio system control.

**Parameters:**
- `sample_rate` (int): Audio sample rate in Hz (default: 48000)
- `bit_depth` (int): Audio bit depth (default: 24)

**Methods:**
- `add_track(track)`: Add an audio track
- `remove_track(track_id)`: Remove a track
- `play_track(track_id, fade_in_ms)`: Play a track with fade in
- `stop_track(track_id, fade_out_ms)`: Stop a track with fade out
- `stop_all(fade_out_ms)`: Stop all playing tracks
- `set_track_volume(track_id, volume_db, ramp_ms)`: Set track volume
- `set_master_volume(volume_db, ramp_ms)`: Set all track volumes
- `mute_track(track_id)`: Mute a specific track
- `unmute_track(track_id)`: Unmute a specific track
- `mute_all()`: Mute all tracks
- `unmute_all()`: Unmute all tracks
- `emergency_mute()`: Activate emergency mute (instant)
- `reset_from_emergency()`: Reset from emergency mute state
- `get_status()`: Get controller status

### AudioTrack

Represents an audio track.

**Attributes:**
- `id` (str): Track identifier
- `name` (str): Track name
- `url` (str): Audio file URL or path
- `volume_db` (float): Volume in decibels (-60 to 0)
- `max_volume_db` (float): Maximum safe volume
- `is_playing` (bool): Playing status
- `is_muted` (bool): Mute status

**Methods:**
- `set_volume(volume_db)`: Set volume (with automatic clamping)
- `adjust_volume(adjustment_db)`: Adjust volume relatively
- `play()`: Start playing
- `stop(fade_out_ms)`: Stop playing
- `mute()`: Mute the track
- `unmute()`: Unmute the track

### AudioOutput

Represents an audio output destination.

**Attributes:**
- `id` (str): Output identifier
- `name` (str): Output name
- `output_type` (str): Type (stereo, mono, etc.)
- `channels` (list): Channel assignments

## Safety Features

### Emergency Mute

The emergency mute feature provides instant silence for safety:

```python
# Activate emergency mute
controller.emergency_mute()

# All tracks muted instantly
# System state = EMERGENCY_MUTE
# Commands are blocked until reset

# Reset from emergency
controller.reset_from_emergency()
# All volumes reset to safe default (-20 dB)
```

### Safe Volume Limits

Volume limits are enforced automatically:
- **Minimum**: -60 dB
- **Default Maximum**: -6 dB (configurable per track)
- **Safe Default**: -20 dB (used after emergency reset)

### Volume Clamping

All volume changes are automatically clamped:
```python
# Will be clamped to max_volume_db
track.set_volume(0.0)  # Too loud!

# Will be clamped to minimum
track.set_volume(-100.0)  # Too quiet!
```

## Audio Configuration

### Sample Rate

Default: 48000 Hz
Common values: 44100, 48000, 96000 Hz

### Bit Depth

Default: 24-bit
Common values: 16, 24, 32-bit

### Default Outputs

Three outputs are created by default:
1. **Main** (stereo): Channels 1-2
2. **Monitor** (stereo): Channels 3-4
3. **Subwoofer** (mono): Channel 5

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=audio_controller --cov-report=term-missing
```

### Code Formatting

```bash
# Format code
black audio_controller.py

# Check linting
ruff check audio_controller.py

# Type checking
mypy audio_controller.py
```

## Hardware Requirements

### Audio Interface

- Audio interface with appropriate I/O
- Driver support for your operating system
- Sample rate and bit depth support

### Speakers/Amps

- Appropriate speakers for venue size
- Power amplifiers if needed
- Proper gain staging

## Troubleshooting

### No audio output

1. Check audio interface connection
2. Verify track is playing: `get_track_state(track_id)`
3. Check track is not muted
4. Verify volume levels
5. Check audio interface drivers

### Emergency mute not resetting

1. Check if system is in EMERGENCY_MUTE state
2. Call `reset_from_emergency()` explicitly
3. Verify no hardware issues

### Volume changes not working

1. Check if in EMERGENCY_MUTE state
2. Verify track ID is correct
3. Check volume limits (max_volume_db)
4. Ensure track exists in controller

## Best Practices

### Volume Management

1. **Start Low**: Begin with conservative volumes (-20 dB)
2. **Test Levels**: Sound check before performance
3. **Headroom**: Leave headroom for dynamic content
4. **Monitor**: Use monitor speakers for operator

### Emergency Preparedness

1. **Test Emergency Mute**: Regularly test emergency mute
2. **Accessible Controls**: Keep emergency controls accessible
3. **Document Procedure**: Have clear emergency procedures
4. **Practice Drills**: Regular emergency drills

### Track Organization

1. **Descriptive IDs**: Use clear track identifiers
2. **Logical Grouping**: Group related tracks
3. **Consistent Naming**: Use consistent naming conventions
4. **Volume Balance**: Set appropriate relative volumes

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/ranjrana2012-lab/project-chimera
- Issues: https://github.com/ranjrana2012-lab/project-chimera/issues

## Project Chimera

This service is part of Project Chimera, an AI-powered adaptive live theatre framework.

For more information:
- Documentation: https://github.com/ranjrana2012-lab/project-chimera/docs
- Phase 2 Plan: See `docs/PHASE_2_IMPLEMENTATION_PLAN.md`
