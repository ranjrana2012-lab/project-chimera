# Hardware Integration Specification

**Project**: Project Chimera Phase 2 - Live Theatre Hardware Integration
**Components**: DMX Lighting Control, Audio System Control
**Version**: 1.0
**Date**: April 9, 2026

---

## Overview

### Purpose
This specification defines the hardware integration requirements for Project Chimera Phase 2, enabling AI-controlled DMX lighting and audio systems for live theatrical performances.

### Scope

**In Scope**:
- DMX512 lighting control via software API
- Audio system control via software API
- Safety protocols and emergency stop
- Integration testing and validation
- Operator control interfaces

**Out of Scope**:
- Hardware procurement (venue provides)
- Physical installation (venue handles)
- Hardware maintenance (venue responsible)
- Custom hardware fabrication

---

## System Architecture

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Operator Console                            │
│                  (Human Oversight Interface)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Hardware Integration Service                    │
│         (DMX Controller + Audio Controller)                   │
└─────┬───────────────────────────────────────────┬───────────┘
      │                                           │
┌─────▼─────────┐                         ┌──────▼────────┐
│  DMX Lighting │                         │  Audio System │
│  Controller   │                         │  Controller   │
└─────┬─────────┘                         └──────┬────────┘
      │                                         │
┌─────▼─────────┐                         ┌──────▼────────┐
│  DMX Universe │                         │  Audio Mixer  │
│     (512)     │                         │   & Amps      │
└─────┬─────────┘                         └──────┬────────┘
      │                                         │
┌─────▼─────────┐                         ┌──────▼────────┐
│   Lighting    │                         │   Speakers    │
│   Fixtures    │                         │   (Various)    │
└───────────────┘                         └───────────────┘

Emergency Stop: ────────────────────────────────────────┐
                └──> Immediate shutdown of all DMX/audio │
                └──> Venue emergency protocols          │
                └──> Manual control fallback              │
```

---

## DMX Lighting Control

### DMX512 Protocol

**Standard**: DMX512 (1990) or DMX512-A (2008)
**Data Rate**: 250 kbps
**Connector**: XLR 3-pin or 5-pin
**Max Universe**: 512 channels per universe
**Refresh Rate**: 30-44 Hz typical

### Universe Allocation

**Universe 1**: Stage Lighting (Channels 1-512)
- Channels 1-512: Stage fixtures (moving heads, PARs, etc.)

**Universe 2** (if needed): House/Accent Lighting
- Channels 1-512: House lights, accent lighting

**Universe 3** (if needed): Special Effects
- Channels 1-512: Haze, strobe, practicals

### Fixture Control

**Channel Types**:
1. **Intensity**: Brightness (0-100% or 0-255)
2. **Color**: RGB, CMY, or color wheel (0-255)
3. **Position**: Pan/Tilt (0-255 or 16-bit)
4. **Focus**: Zoom, edge (0-255)
5. **Effects**: Gobo, prism, shutter (0-255)

**Control Commands**:

```json
{
  "universe": 1,
  "fixture": "moving_head_1",
  "channel_start": 1,
  "channels": {
    "intensity": 255,
    "color_red": 200,
    "color_green": 100,
    "color_blue": 50,
    "pan": 128,
    "tilt": 128,
    "focus": 255,
    "gobo": 5
  }
}
```

### API Specification

**Set Fixture State**:
```http
POST /api/lighting/set
Content-Type: application/json

{
  "universe": 1,
  "fixtures": [
    {
      "id": "moving_head_1",
      "channels": {
        "intensity": 255,
        "pan": 128
      }
    }
  ]
}
```

**Set Scene**:
```http
POST /api/lighting/scene
Content-Type: application/json

{
  "scene_name": "happy_scene",
  "universe": 1,
  "transition_time_ms": 1000,
  "fixtures": [
    {
      "id": "all",
      "channels": {
        "intensity": 200,
        "color_red": 255,
        "color_blue": 100
      }
    }
  ]
}
```

**Get Fixture State**:
```http
GET /api/lighting/state?universe=1&fixture=moving_head_1
```

### Safety Requirements

**Emergency Stop**:
- Physical button: Cuts DMX output immediately
- Software command: `/api/lighting/emergency_stop`
- Automatic triggers: Overheat, fault detection

**Fail-Safe States**:
- **Startup**: All fixtures to 50% intensity, white
- **Emergency**: All fixtures to 0% intensity
- **Communication Loss**: Hold last known state (or fade to 0% in 30 seconds)

**Safety Interlocks**:
- Verify venue emergency stop integration
- Test emergency stop procedures weekly
- Document all emergency protocols
- Train all operators on emergency procedures

---

## Audio System Control

### Audio Protocols

**Primary Control**: MIDI Show Control (MSC)
**Secondary**: OSC (Open Sound Control)
**Fallback**: Analog audio (no control)

### Audio Architecture

```
AI System (Audio Output)
     │
     ▼
┌─────────────────────┐
│  Audio Controller   │
│  (Software Service) │
└──────┬──────────────┘
       │
   ┌───┴────┬──────────┬──────────┐
   ▼        ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Track 1│ │Track 2│ │Track 3│ │Track 4│
│Output │ │Output │ │Output │ │Output │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │          │          │
    └─────────┴──────────┴──────────┘
                      │
                ┌───────▼────────┐
                │  Audio Mixer    │
                │ (Hardware)      │
                └───────┬────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
       ┌─────────┐             ┌─────────┐
       │   Main   │             │ Monitor  │
       │ Speakers │             │ Speakers │
       └─────────┘             └─────────┘
```

### Audio Channels

**Input Channels** (from AI system):
- Channel 1: Main dialogue (AI speech synthesis)
- Channel 2: Background music
- Channel 3: Sound effects
- Channel 4: Audience interaction audio

**Output Channels** (to venue):
- Output 1: Main speakers (L/R)
- Output 2: Monitor speakers (L/R)
- Output 3: Subwoofer (LFE)
- Output 4: Assistive listening (if available)

### API Specification

**Play Audio**:
```http
POST /api/audio/play
Content-Type: application/json

{
  "track": "dialogue",
  "volume_db": -6,
  "fade_in_ms": 500,
  "output": "main"
}
```

**Stop Audio**:
```http
POST /api/audio/stop
Content-Type: application/json

{
  "track": "dialogue",
  "fade_out_ms": 1000
}
```

**Set Volume**:
```http
POST /api/audio/volume
Content-Type: application/json

{
  "track": "music",
  "volume_db": -12,
  "ramp_ms": 500
}
```

**Get Audio State**:
```http
GET /api/audio/state
```

### Safety Requirements

**Volume Limits**:
- Maximum: 95 dB SPL (C-weighted, slow)
- Typical: 75-85 dB SPL
- Minimum: 60 dB SPL (for intelligibility)

**Emergency Mute**:
- Physical button: Mutes all audio immediately
- Software command: `/api/audio/emergency_mute`
- Automatic triggers: Clipping, feedback, fault detection

**Fail-Safe States**:
- **Startup**: All audio muted, volume -20 dB
- **Emergency**: All audio muted immediately
- **Communication Loss**: Fade out over 2 seconds, then mute

---

## Integration Requirements

### Software Requirements

**DMX Controller Service**:
- Language: Python 3.10+ or Node.js
- Libraries:
  - Python: `pyftdi`, `dmxl` or `sACN` (for Art-Net)
  - Node.js: `dmxnet` or `node-dmx`
- API: RESTful endpoints for fixture control
- Latency: <100ms from command to fixture response

**Audio Controller Service**:
- Language: Python 3.10+ or Node.js
- Libraries:
  - Python: `mido` (MIDI), `pyo` or `sounddevice` (audio)
  - Node.js: `easymidi`, `web-audio-api`
- API: RESTful endpoints for audio control
- Latency: <50ms from command to audio output

### Hardware Requirements

**DMX Interface**:
- USB-to-DMX interface (Enttec Open DMX, DMXKing, etc.)
- OR Art-Net node (for network-based DMX)
- OR sACN node (for streaming ACN)
- Minimum 1 universe (512 channels)

**Audio Interface**:
- USB audio interface (Focusrite, Scarlett, etc.)
- OR network audio (Dante, Ravenna, etc.)
- Minimum 4 output channels
- 24-bit/48kHz minimum quality

### Network Requirements

**Bandwidth**:
- Minimum: 100 Mbps (for DMX Art-Net/sACN)
- Recommended: 1 Gbps (for multiple universes + audio)
- Latency: <10ms (for real-time control)

**Reliability**:
- Wired network preferred (not WiFi)
- Redundant connections (if available)
- Backup power supply (UPS)

---

## Testing and Validation

### Unit Testing

**DMX Controller Tests**:
- [ ] Connect to DMX interface
- [ ] Send single channel command
- [ ] Send multiple channel command
- [ ] Verify fixture response
- [ ] Test emergency stop

**Audio Controller Tests**:
- [ ] Connect to audio interface
- [ ] Play test audio
- [ ] Adjust volume
- [ ] Test fade in/out
- [ ] Test emergency mute

### Integration Testing

**End-to-End Tests**:
- [ ] AI system → DMX control → lighting response
- [ ] AI system → Audio control → sound output
- [ ] Combined lighting + audio scene
- [ ] Emergency stop from operator console
- [ ] Fallback to manual control

**Performance Tests**:
- [ ] Latency measurement (command → response)
- [ ] Throughput test (multiple simultaneous commands)
- [ ] Reliability test (continuous operation)
- [ ] Load test (maximum fixture/channel count)

### Venue Testing

**On-Site Tests**:
- [ ] Test with venue DMX system
- [ ] Test with venue audio system
- [ ] Verify all fixtures respond correctly
- [ ] Test emergency stop integration
- [ ] Test manual control fallback

**Rehearsal Tests**:
- [ ] Full system rehearsal
- [ ] Scene transitions
- [ ] Emergency procedures
- [ ] Operator training
- [ ] Timing verification

---

## Safety and Emergency Procedures

### Emergency Stop Protocol

**Activation Methods**:
1. **Physical Button**: Red emergency stop button at operator console
2. **Software Command**: `/api/emergency_stop`
3. **Voice Command**: "Emergency stop" (if enabled)
4. **Venue Integration**: Tie into venue emergency stop system

**Emergency Stop Actions**:
1. Immediately halt all DMX output (fade to 0 in <1 second)
2. Immediately mute all audio
3. Engage manual control mode
4. Notify venue staff
5. Follow venue emergency protocols
6. Document incident

### Fail-Safe Design

**Communication Loss**:
- DMX: Hold last state for 30 seconds, then fade to 0
- Audio: Fade out over 2 seconds, then mute
- Operator: Alert on console, attempt reconnection

**Hardware Fault**:
- DMX interface fault: Switch to backup (if available) or manual mode
- Audio interface fault: Switch to backup (if available) or mute
- Network fault: Switch to local control mode

**Software Fault**:
- Service crash: Automatic restart, hold last safe state
- API timeout: Fallback to safe defaults (50% intensity, muted)
- Control loop error: Emergency stop triggered

### Safety Certifications

**Required Certifications**:
- [ ] Electrical safety inspection
- [ ] Equipment PAT testing
- [ ] Risk assessment completed
- [ ] Emergency procedures documented
- [ ] Staff training completed

---

## Operator Interface

### Control Dashboard

**Lighting Controls**:
- Scene selection dropdown
- Individual fixture controls
- Master intensity slider
- Color temperature control
- Emergency stop button

**Audio Controls**:
- Track selection (dialogue, music, SFX)
- Volume sliders per track
- Mute buttons per track
- Master volume control
- Emergency mute button

**Status Displays**:
- DMX connection status
- Audio connection status
- Current scene name
- Active tracks
- System health indicators

**Emergency Controls**:
- Emergency stop (DMX + Audio)
- Manual mode toggle
- Reset to defaults
- Venue emergency stop integration

---

## Maintenance and Monitoring

### Routine Maintenance

**Daily** (during performance period):
- Test DMX connection
- Test audio output
- Verify emergency stop functionality
- Check cable connections

**Weekly**:
- Full system test
- Backup configuration
- Update firmware/software
- Clean connectors and cables

**Monthly**:
- Calibrate fixtures
- Test all emergency procedures
- Review logs for issues
- Preventive maintenance

### Monitoring

**System Metrics**:
- DMX command latency
- Audio output latency
- Error rates
- Uptime percentage
- Emergency stop activations

**Alerts**:
- Connection lost
- High latency (>200ms)
- Error rate >1%
- Emergency stop activated
- Hardware fault detected

---

## Documentation and Training

### Required Documentation

**Technical Documentation**:
- [ ] System architecture diagram
- [ ] API documentation
- [ ] Configuration guide
- [ ] Troubleshooting guide
- [ ] Emergency procedures

**User Documentation**:
- [ ] Operator guide
- [ ] Quick reference card
- [ ] Emergency procedures
- [ ] Contact information

### Training Requirements

**Operator Training**:
- [ ] System overview (1 hour)
- [ ] Hands-on practice (2 hours)
- [ ] Emergency procedures (1 hour)
- [ ] Assessment (30 minutes)

**Refresher Training**:
- [ ] Before first performance
- [ ] Monthly during performance run
- [ ] After any incident
- [ ] After any system changes

---

## Appendix A: Equipment Checklist

### DMX Equipment

- [ ] USB-to-DMX interface
- [ ] DMX cables (5-pin XLR, various lengths)
- [ ] DMX terminator (if required)
- [ ] Backup DMX interface (recommended)

### Audio Equipment

- [ ] USB audio interface
- [ ] Audio cables (various types)
- [ ] Headphones for monitoring
- [ ] Backup audio interface (recommended)

### Network Equipment

- [ ] Network switch (if required)
- [ ] Network cables (CAT6)
- [ ] UPS (uninterruptible power supply)

### Safety Equipment

- [ ] Emergency stop button
- [ ] First aid kit
- [ ] Flashlight
- [ ] Two-way radio

---

## Appendix B: Configuration Examples

### DMX Controller Configuration

```python
# config/dmx_controller.py

DMX_CONFIG = {
    "interface": "enttec_open_dmx",
    "port": "/dev/ttyUSB0",
    "universe": 1,
    "refresh_rate": 44,  # Hz

    "fixtures": {
        "moving_head_1": {
            "address": 1,
            "channels": 16
        },
        "moving_head_2": {
            "address": 17,
            "channels": 16
        }
    },

    "safety": {
        "emergency_stop_pin": 4,  # GPIO pin
        "max_intensity": 255,
        "startup_intensity": 128,  # 50%
        "communication_timeout": 30  # seconds
    }
}
```

### Audio Controller Configuration

```python
# config/audio_controller.py

AUDIO_CONFIG = {
    "interface": "focusrite_scarlett_2i2",
    "sample_rate": 48000,
    "bit_depth": 24,
    "channels": {
        "dialogue": 1,
        "music": 2,
        "sfx": 3,
        "interaction": 4
    },

    "outputs": {
        "main": [1, 2],
        "monitor": [3, 4],
        "subwoofer": [5]
    },

    "safety": {
        "max_volume_db": -6,
        "startup_volume_db": -20,
        "emergency_mute_pin": 5,  # GPIO pin
        "communication_timeout": 5  # seconds
    }
}
```

---

**Hardware Integration Specification Version: 1.0**
**For: Project Chimera Phase 2**
**Date: April 9, 2026**
