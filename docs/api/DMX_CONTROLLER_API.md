# Project Chimera Phase 2 - DMX Controller API Documentation

**Version**: 1.0.0
**Service**: DMX Controller
**Port**: 8001
**Protocol**: HTTP/REST
**Base URL**: `http://localhost:8001`

---

## Overview

The DMX Controller service provides REST API endpoints for controlling DMX512 lighting fixtures, managing scenes, and handling emergency procedures.

### Features

- Fixture management (add, remove, update)
- Scene activation and transitions
- Emergency stop functionality
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
  "service": "dmx-controller",
  "version": "1.0.0",
  "uptime_seconds": 1234.56
}
```

#### GET /api/status

Get detailed service status.

**Response**:
```json
{
  "state": "idle",
  "universe": 1,
  "fixture_count": 10,
  "scene_count": 5,
  "current_scene": null,
  "refresh_rate": 44
}
```

---

### Fixtures

#### GET /api/fixtures

List all fixtures.

**Response**:
```json
{
  "fixtures": [
    {
      "id": "mh_1",
      "name": "Moving Head 1",
      "start_address": 1,
      "channel_count": 6,
      "channels": {
        "1": {"name": "intensity", "value": 0},
        "2": {"name": "pan", "value": 0}
      }
    }
  ]
}
```

#### POST /api/fixtures

Add a new fixture.

**Request Body**:
```json
{
  "id": "mh_2",
  "name": "Moving Head 2",
  "start_address": 10,
  "channel_count": 6,
  "channels": {
    "1": {"name": "intensity"},
    "2": {"name": "pan"},
    "3": {"name": "tilt"},
    "4": {"name": "color_red"},
    "5": {"name": "color_green"},
    "6": {"name": "color_blue"}
  }
}
```

**Response**: `201 Created`

```json
{
  "id": "mh_2",
  "name": "Moving Head 2",
  "status": "added"
}
```

#### DELETE /api/fixtures/{fixture_id}

Remove a fixture.

**Parameters**:
- `fixture_id` (path): Fixture identifier

**Response**: `204 No Content`

---

### Channels

#### PUT /api/fixtures/{fixture_id}/channels/{channel_number}

Update a single channel value.

**Parameters**:
- `fixture_id` (path): Fixture identifier
- `channel_number` (path): Channel number (1-512)

**Request Body**:
```json
{
  "value": 128
}
```

**Response**: `200 OK`

```json
{
  "fixture_id": "mh_1",
  "channel_number": 1,
  "old_value": 0,
  "new_value": 128
}
```

**Error Responses**:
- `404 Not Found`: Fixture not found
- `400 Bad Request`: Invalid channel value (must be 0-255)
- `403 Forbidden`: Emergency stop active

---

### Scenes

#### GET /api/scenes

List all scenes.

**Response**:
```json
{
  "scenes": [
    {
      "name": "happy",
      "fixture_count": 10,
      "transition_time_ms": 2000
    }
  ]
}
```

#### POST /api/scenes

Create a new scene.

**Request Body**:
```json
{
  "name": "bright",
  "fixture_values": {
    "mh_1": {
      "1": 255,
      "4": 255
    }
  },
  "transition_time_ms": 3000
}
```

**Response**: `201 Created`

#### POST /api/scenes/{scene_name}/activate

Activate a scene.

**Parameters**:
- `scene_name` (path): Scene name

**Response**: `200 OK`

```json
{
  "scene": "bright",
  "status": "activating",
  "transition_time_ms": 3000,
  "fixtures_affected": 10
}
```

**Error Responses**:
- `404 Not Found`: Scene not found
- `403 Forbidden`: Emergency stop active

---

### Emergency Procedures

#### POST /api/emergency/stop

Execute emergency stop (blackout all channels).

**Response**: `200 OK`

```json
{
  "status": "emergency_stop",
  "all_channels_zero": true,
  "timestamp": "2026-04-09T15:30:00Z"
}
```

#### POST /api/emergency/reset

Reset from emergency stop mode.

**Response**: `200 OK`

```json
{
  "status": "idle",
  "emergency_cleared": true
}
```

---

## Data Models

### Fixture

```python
{
  "id": str,           # Unique identifier
  "name": str,         # Human-readable name
  "start_address": int, # DMX start address (1-512)
  "channel_count": int, # Number of channels
  "channels": {        # Channel definitions
    channel_number: {
      "name": str,      # Channel name
      "value": int      # Current value (0-255)
    }
  }
}
```

### Scene

```python
{
  "name": str,              # Scene name
  "fixture_values": {       # Fixture target values
    fixture_id: {
      channel_number: value  # 0-255
    }
  },
  "transition_time_ms": int # Transition duration
}
```

### ChannelValue

```python
{
  "name": str,   # Channel name
  "value": int   # Channel value (0-255)
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

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
| `FIXTURE_NOT_FOUND` | Fixture does not exist |
| `SCENE_NOT_FOUND` | Scene does not exist |
| `INVALID_CHANNEL_VALUE` | Channel value must be 0-255 |
| `EMERGENCY_ACTIVE` | Operation blocked during emergency stop |
| `INVALID_REQUEST_BODY` | Malformed request JSON |

---

## Rate Limiting

**Current Status**: No rate limiting (development mode)

**Production Recommendation**: Implement rate limiting

```python
# Suggested limits
- /api/fixtures: 100 requests/minute
- /api/scenes/*/activate: 60 requests/minute
- /api/emergency/*: No limit (safety critical)
```

---

## WebSocket Events

The DMX Controller emits WebSocket events for real-time updates.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

### Event Types

#### scene_activating

Emitted when a scene starts activating.

```json
{
  "type": "scene_activating",
  "timestamp": "2026-04-09T15:30:00Z",
  "payload": {
    "scene": "happy",
    "transition_time_ms": 2000
  }
}
```

#### scene_activated

Emitted when a scene activation completes.

```json
{
  "type": "scene_activated",
  "timestamp": "2026-04-09T15:30:02Z",
  "payload": {
    "scene": "happy",
    "fixtures_updated": 10
  }
}
```

#### emergency_stop

Emitted when emergency stop is triggered.

```json
{
  "type": "emergency_stop",
  "timestamp": "2026-04-09T15:31:00Z",
  "payload": {
    "all_channels_zero": true
  }
}
```

---

## Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8001"

# Add a fixture
fixture = {
    "id": "mh_1",
    "name": "Moving Head 1",
    "start_address": 1,
    "channel_count": 6,
    "channels": {
        str(i): {"name": f"channel_{i}"}
        for i in range(1, 7)
    }
}
response = requests.post(f"{BASE_URL}/api/fixtures", json=fixture)
print(response.json())

# Create and activate a scene
scene = {
    "name": "bright",
    "fixture_values": {
        "mh_1": {1: 255, 4: 255}
    },
    "transition_time_ms": 2000
}
requests.post(f"{BASE_URL}/api/scenes", json=scene)
requests.post(f"{BASE_URL}/api/scenes/bright/activate")

# Emergency stop
requests.post(f"{BASE_URL}/api/emergency/stop")
```

### JavaScript Client

```javascript
const BASE_URL = 'http://localhost:8001';

// Add a fixture
async function addFixture(fixture) {
  const response = await fetch(`${BASE_URL}/api/fixtures`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(fixture)
  });
  return await response.json();
}

// Activate a scene
async function activateScene(sceneName) {
  const response = await fetch(`${BASE_URL}/api/scenes/${sceneName}/activate`, {
    method: 'POST'
  });
  return await response.json();
}

// Emergency stop
async function emergencyStop() {
  const response = await fetch(`${BASE_URL}/api/emergency/stop`, {
    method: 'POST'
  });
  return await response.json();
}
```

---

## Monitoring

### Metrics

The DMX Controller exposes Prometheus metrics at `/metrics`:

- `chimera_dmx_requests_total` - Total API requests
- `chimera_dmx_scene_activations_total` - Scene activations
- `chemera_dmx_emergency_stops_total` - Emergency stops
- `chimera_dmx_active_fixtures` - Current active fixtures
- `chimera_dmx_response_time_ms` - Request response time

### Tracing

The service uses OpenTelemetry for distributed tracing. Spans are created for:
- Scene activation
- Channel updates
- Emergency procedures
- API requests

---

## Security Considerations

### Input Validation

- All channel values validated to be 0-255
- Fixture IDs validated to exist
- Scene names validated to exist

### Safety Features

- Emergency stop cannot be overridden
- All operations blocked during emergency state
- Channel values clamped to valid range

### Production Recommendations

1. **Authentication**: Implement API key or JWT authentication
2. **TLS**: Use HTTPS in production
3. **Rate Limiting**: Implement rate limiting on all endpoints
4. **Input Sanitization**: Validate all user inputs
5. **Audit Logging**: Log all emergency procedures

---

## Changelog

### Version 1.0.0 (2026-04-09)
- Initial release
- Basic fixture and scene management
- Emergency stop functionality
- Health monitoring endpoints
- WebSocket event streaming
