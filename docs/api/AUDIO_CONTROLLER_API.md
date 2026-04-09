# Project Chimera Phase 2 - Audio Controller API Documentation

**Version**: 1.0.0
**Service**: Audio Controller
**Port**: 8002
**Protocol**: HTTP/REST
**Base URL**: `http://localhost:8002`

---

## Overview

The Audio Controller service provides REST API endpoints for managing audio playback, volume control, and emergency muting.

### Features

- Track management (add, remove, update)
- Playback control (play, stop, pause)
- Volume control with ramping
- Emergency mute functionality
- Health monitoring endpoints
- Distributed tracing support

---

## Authentication

**Current Status**: No authentication required (development mode)

**Production Recommendation**: Implement API key or JWT authentication

```python
# Example API key header
Authorization: Bearer YOUR_API_KEY
```

---

## API Endpoints

### Health & Status

#### GET /health

Check service health status.

**Response**:
```json
{
  "status": "healthy",
  "service": "audio-controller",
  "version": "1.0.0",
  "uptime_seconds": 1234.56
}
```

#### GET /api/status

Get detailed service status.

**Response**:
```json
{
  "state": "playing",
  "sample_rate": 48000,
  "bit_depth": 24,
  "track_count": 5,
  "active_tracks": ["music", "dialogue"],
  "master_volume_db": -15.0
}
```

---

### Tracks

#### GET /api/tracks

List all tracks.

**Response**:
```json
{
  "tracks": [
    {
      "id": "dialogue",
      "name": "AI Dialogue",
      "url": "/assets/dialogue.mp3",
      "volume_db": -20.0,
      "is_playing": true,
      "is_muted": false
    }
  ]
}
```

#### POST /api/tracks

Add a new track.

**Request Body**:
```json
{
  "id": "sfx",
  "name": "Sound Effect",
  "url": "/assets/sfx.mp3",
  "volume_db": -15.0
}
```

**Response**: `201 Created`

```json
{
  "id": "sfx",
  "name": "Sound Effect",
  "status": "added"
}
```

#### DELETE /api/tracks/{track_id}

Remove a track.

**Parameters**:
- `track_id` (path): Track identifier

**Response**: `204 No Content`

---

### Playback Control

#### POST /api/tracks/{track_id}/play

Play a track.

**Parameters**:
- `track_id` (path): Track identifier

**Request Body**:
```json
{
  "fade_in_ms": 1000,
  "start_time_ms": 0
}
```

**Response**: `200 OK`

```json
{
  "track_id": "dialogue",
  "status": "playing",
  "fade_in_ms": 1000
}
```

#### POST /api/tracks/{track_id}/stop

Stop a track.

**Parameters**:
- `track_id` (path): Track identifier

**Request Body**:
```json
{
  "fade_out_ms": 2000
}
```

**Response**: `200 OK`

```json
{
  "track_id": "dialogue",
  "status": "stopped",
  "fade_out_ms": 2000
}
```

#### POST /api/tracks/{track_id}/pause

Pause a track.

**Parameters**:
- `track_id` (path): Track identifier

**Response**: `200 OK`

```json
{
  "track_id": "dialogue",
  "status": "paused"
}
```

---

### Volume Control

#### PUT /api/tracks/{track_id}/volume

Set track volume with optional ramp.

**Parameters**:
- `track_id` (path): Track identifier

**Request Body**:
```json
{
  "volume_db": -15.0,
  "ramp_ms": 2000
}
```

**Response**: `200 OK`

```json
{
  "track_id": "dialogue",
  "old_volume_db": -20.0,
  "new_volume_db": -15.0,
  "ramp_ms": 2000
}
```

#### PUT /api/volume/master

Set master volume for all tracks.

**Request Body**:
```json
{
  "volume_db": -10.0,
  "ramp_ms": 3000
}
```

**Response**: `200 OK`

```json
{
  "master_volume_db": -10.0,
  "affected_tracks": 5
}
```

---

### Emergency Procedures

#### POST /api/emergency/mute

Execute emergency mute (mute all tracks).

**Response**: `200 OK`

```json
{
  "status": "emergency_mute",
  "all_tracks_muted": true,
  "timestamp": "2026-04-09T15:30:00Z"
}
```

#### POST /api/emergency/reset

Reset from emergency mute mode.

**Response**: `200 OK`

```json
{
  "status": "idle",
  "emergency_cleared": true
}
```

---

## Data Models

### Track

```python
{
  "id": str,           # Unique identifier
  "name": str,         # Human-readable name
  "url": str,          # Audio file URL
  "volume_db": float,  # Volume in decibels (-60 to 0)
  "is_playing": bool,  # Currently playing
  "is_muted": bool     # Currently muted
}
```

### VolumeChange

```python
{
  "volume_db": float,  # Target volume in dB
  "ramp_ms": int       # Transition duration (optional)
}
```

---

## Error Responses

All endpoints may return error responses:

```json
{
  "error": {
    "code": str,
    "message": str,
    "details": Any
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `TRACK_NOT_FOUND` | Track does not exist |
| `INVALID_VOLUME` | Volume must be -60 to 0 dB |
| `EMERGENCY_ACTIVE` | Operation blocked during emergency mute |
| `INVALID_REQUEST_BODY` | Malformed request JSON |

---

## Rate Limiting

**Current Status**: No rate limiting (development mode)

**Production Recommendation**:
```python
# Suggested limits
- /api/tracks: 100 requests/minute
- /api/tracks/*/play: 60 requests/minute
- /api/emergency/*: No limit (safety critical)
```

---

## WebSocket Events

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8002/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

### Event Types

#### track_playing

Emitted when a track starts playing.

```json
{
  "type": "track_playing",
  "timestamp": "2026-04-09T15:30:00Z",
  "payload": {
    "track_id": "dialogue",
    "volume_db": -20.0
  }
}
```

#### volume_changed

Emitted when volume changes.

```json
{
  "type": "volume_changed",
  "timestamp": "2026-04-09T15:30:01Z",
  "payload": {
    "track_id": "dialogue",
    "old_volume_db": -20.0,
    "new_volume_db": -15.0
  }
}
```

#### emergency_mute

Emitted when emergency mute is triggered.

```json
{
  "type": "emergency_mute",
  "timestamp": "2026-04-09T15:31:00Z",
  "payload": {
    "all_tracks_muted": true
  }
}
```

---

## Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8002"

# Add a track
track = {
    "id": "dialogue",
    "name": "AI Dialogue",
    "url": "/assets/dialogue.mp3",
    "volume_db": -20.0
}
response = requests.post(f"{BASE_URL}/api/tracks", json=track)
print(response.json())

# Play track with fade in
requests.post(f"{BASE_URL}/api/tracks/dialogue/play", json={
    "fade_in_ms": 1000
})

# Set volume with ramp
requests.put(f"{BASE_URL}/api/tracks/dialogue/volume", json={
    "volume_db": -15.0,
    "ramp_ms": 2000
})

# Emergency mute
requests.post(f"{BASE_URL}/api/emergency/mute")
```

### JavaScript Client

```javascript
const BASE_URL = 'http://localhost:8002';

// Add a track
async function addTrack(track) {
  const response = await fetch(`${BASE_URL}/api/tracks`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(track)
  });
  return await response.json();
}

// Play track
async function playTrack(trackId, fadeInMs = 0) {
  const response = await fetch(`${BASE_URL}/api/tracks/${trackId}/play`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({fade_in_ms: fadeInMs})
  });
  return await response.json();
}

// Emergency mute
async function emergencyMute() {
  const response = await fetch(`${BASE_URL}/api/emergency/mute`, {
    method: 'POST'
  });
  return await response.json();
}
```

---

## Monitoring

### Metrics

The Audio Controller exposes Prometheus metrics at `/metrics`:

- `chimera_audio_requests_total` - Total API requests
- `chimera_audio_track_plays_total` - Track plays
- `chimera_audio_volume_changes_total` - Volume changes
- `chimera_audio_emergency_mutes_total` - Emergency mutes
- `chimera_audio_active_tracks` - Current active tracks
- `chimera_audio_response_time_ms` - Request response time

### Tracing

Spans are created for:
- Track playback operations
- Volume changes with ramps
- Emergency procedures
- API requests

---

## Security Considerations

### Input Validation

- All volume values validated to be -60 to 0 dB
- Track IDs validated to exist
- File URLs validated

### Safety Features

- Emergency mute cannot be overridden
- All operations blocked during emergency state
- Volume values clamped to valid range

### Production Recommendations

1. **Authentication**: Implement API key or JWT
2. **File Validation**: Validate audio file URLs
3. **Rate Limiting**: Implement on all endpoints
4. **Audit Logging**: Log all emergency procedures

---

## Changelog

### Version 1.0.0 (2026-04-09)
- Initial release
- Track management
- Playback control
- Volume control with ramping
- Emergency mute functionality
- WebSocket events
