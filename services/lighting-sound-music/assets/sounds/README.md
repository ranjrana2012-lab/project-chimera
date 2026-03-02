# Sound Effects Library

This directory contains the sound effects library for the Lighting, Sound and Music Integration service.

## Directory Structure

```
sounds/
├── effects/        # Short, event-triggered sound effects
├── ambient/        # Background and atmospheric sounds
├── transitions/    # Transition and movement sounds
└── catalog.yaml    # Sound metadata catalog
```

## Categories

### Effects (`effects/`)
Short, one-shot sound effects triggered by specific events:
- UI interactions (clicks, hover sounds)
- Game events (scoring, achievements, power-ups)
- Environmental effects (footsteps, object impacts)
- Notifications and alerts

**Naming Convention:** `{category}_{action}_{variant}.{ext}`
- Examples:
  - `ui_click_default.wav`
  - `game_score_01.wav`
  - `env_footstep_grass.wav`

### Ambient (`ambient/`)
Background and atmospheric sounds that loop continuously:
- Environmental ambience (rain, wind, forest, city)
- Room tones (indoor hums, air conditioning)
- Crowd sounds (cheering, murmuring)
- Mechanical hums and drones

**Naming Convention:** `ambient_{location}_{condition}_{time}.{ext}`
- Examples:
  - `ambient_forest_calm_day.wav`
  - `ambient_city_busy_night.wav`
  - `ambient_room_quiet.wav`

### Transitions (`transitions/`)
Sounds for scene changes, movements, and state transitions:
- Fade effects (fade in, fade out, crossfade)
- Movement transitions (whooshes, sweeps)
- Scene changes (warp, teleport, level change)
- State changes (power up, power down)

**Naming Convention:** `transition_{type}_{direction}_{variant}.{ext}`
- Examples:
  - `transition_fade_in_soft.wav`
  - `transition_whoosh_fast_left.wav`
  - `transition_warp_magical.wav`

## File Format Guidelines

### Supported Formats
- **WAV** (Preferred): Lossless, high quality, best for short effects
- **OGG**: Compressed, good for longer ambient loops
- **MP3**: Compressed, acceptable for music and longer tracks

### Audio Quality Specifications
- **Sample Rate**: 44.1 kHz or 48 kHz
- **Bit Depth**: 16-bit or 24-bit
- **Channels**: Mono for effects, Stereo for ambient and transitions
- **Format**: PCM for WAV, Vorbis for OGG

### Volume Guidelines
- Normalize all audio to -3 dB to -6 dB
- Leave 3-6 dB of headroom
- Avoid clipping and distortion
- Test target volume in context of other sounds

## Metadata Catalog

All sounds should be registered in `catalog.yaml` with the following metadata:
- `id`: Unique identifier for the sound
- `name`: Display name
- `filename`: Actual file name
- `category`: effects/ambient/transitions
- `tags`: Array of searchable tags
- `duration`: Length in seconds
- `loop`: Whether the sound should loop (boolean)
- `volume`: Default volume level (0.0-1.0)
- `description`: Brief description of the sound

## Adding New Sounds

1. Place the audio file in the appropriate category directory
2. Follow the naming convention for that category
3. Add metadata entry to `catalog.yaml`
4. Test the sound in context
5. Update this README if adding new subcategories

## Best Practices

- Keep file sizes reasonable (compress long ambient sounds)
- Use consistent volume levels within categories
- Provide multiple variants for frequently used sounds
- Test sounds on different devices and speakers
- Document any special requirements or context in metadata

## Maintenance

- Periodically review and update catalog metadata
- Remove unused sounds to keep library manageable
- Maintain backup of original uncompressed audio files
- Document any licensing or attribution requirements
