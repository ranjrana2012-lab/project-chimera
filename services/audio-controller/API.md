# Audio Controller API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8002`

## Endpoints

### Health Check

```http
GET /health
```

### Get Controller Status

```http
GET /api/status
```

**Response:**

```json
{
  "sample_rate": 48000,
  "bit_depth": 24,
  "state": "playing",
  "track_count": 3,
  "playing_tracks": ["dialogue", "music"],
  "muted_tracks": []
}
```

### List Tracks

```http
GET /api/tracks
```

### Play Track

```http
POST /api/tracks/{track_id}/play
```

**Request Body:**

```json
{
  "fade_in_ms": 500
}
```

### Stop Track

```http
POST /api/tracks/{track_id}/stop
```

**Request Body:**

```json
{
  "fade_out_ms": 1000
}
```

### Set Track Volume

```http
PUT /api/tracks/{track_id}/volume
```

**Request Body:**

```json
{
  "volume_db": -15.0,
  "ramp_ms": 500
}
```

### Set Master Volume

```http
PUT /api/master/volume
```

**Request Body:**

```json
{
  "volume_db": -10.0,
  "ramp_ms": 1000
}
```

### Mute Track

```http
POST /api/tracks/{track_id}/mute
```

### Unmute Track

```http
POST /api/tracks/{track_id}/unmute
```

### Mute All

```http
POST /api/mute-all
```

### Unmute All

```http
POST /api/unmute-all
```

### Emergency Mute

```http
POST /api/emergency-mute
```

### Reset from Emergency

```http
POST /api/emergency-mute/reset
```

## WebSocket Events

| Event | Description |
|-------|-------------|
| `track_started` | Track started playing |
| `track_stopped` | Track stopped |
| `volume_changed` | Volume changed |
| `track_muted` | Track muted |
| `emergency_mute` | Emergency mute activated |

## Examples

### Python

```python
import requests

# Play track
requests.post('http://localhost:8002/api/tracks/dialogue/play',
              json={'fade_in_ms': 500})

# Set volume
requests.put('http://localhost:8002/api/tracks/dialogue/volume',
             json={'volume_db': -15.0})
```

### JavaScript

```javascript
// Play track
fetch('http://localhost:8002/api/tracks/dialogue/play', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({fade_in_ms: 500})
});
```
