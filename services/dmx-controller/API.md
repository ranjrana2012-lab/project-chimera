# DMX Controller API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8001`

## Overview

The DMX Controller API provides REST endpoints for controlling DMX512 lighting fixtures in live theatrical performances.

---

## Endpoints

### Health Check

Check if the service is running.

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "service": "dmx-controller",
  "version": "1.0.0"
}
```

---

### Get Controller Status

Get current controller status and statistics.

```http
GET /api/status
```

**Response:** `200 OK`

```json
{
  "universe": 1,
  "state": "active",
  "refresh_rate": 44,
  "fixture_count": 3,
  "scene_count": 5,
  "current_scene": "happy_scene",
  "last_update": "2026-04-09T12:00:00Z"
}
```

---

### List Fixtures

Get all fixtures registered with the controller.

```http
GET /api/fixtures
```

**Response:** `200 OK`

```json
{
  "fixtures": [
    {
      "id": "mh_1",
      "name": "Moving Head 1",
      "start_address": 1,
      "channel_count": 8,
      "channels": {
        "1": {"value": 128, "label": "intensity"},
        "2": {"value": 64, "label": "pan"},
        "3": {"value": 32, "label": "tilt"}
      }
    }
  ]
}
```

---

### Get Fixture State

Get current state of a specific fixture.

```http
GET /api/fixtures/{fixture_id}
```

**Parameters:**
- `fixture_id` (path): Fixture identifier

**Response:** `200 OK`

```json
{
  "id": "mh_1",
  "channels": {
    "1": 128,
    "2": 64,
    "3": 32
  }
}
```

**Error Response:** `404 Not Found`

```json
{
  "error": "Fixture not found",
  "fixture_id": "nonexistent"
}
```

---

### Set Fixture Channel

Set a single fixture channel value.

```http
PUT /api/fixtures/{fixture_id}/channels/{channel}
```

**Parameters:**
- `fixture_id` (path): Fixture identifier
- `channel` (path): Channel number

**Request Body:**

```json
{
  "value": 255
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "fixture_id": "mh_1",
  "channel": 1,
  "value": 255
}
```

---

### Set Multiple Fixture Channels

Set multiple fixture channel values at once.

```http
PUT /api/fixtures/{fixture_id}/channels
```

**Parameters:**
- `fixture_id` (path): Fixture identifier

**Request Body:**

```json
{
  "channels": {
    "1": 255,
    "2": 128,
    "3": 64
  }
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "fixture_id": "mh_1",
  "channels_updated": 3
}
```

---

### Create Scene

Create a new lighting scene.

```http
POST /api/scenes
```

**Request Body:**

```json
{
  "name": "happy_scene",
  "fixtures": {
    "mh_1": {
      "1": 255,
      "4": 200
    },
    "mh_2": {
      "1": 255,
      "5": 180
    }
  },
  "transition_time_ms": 2000
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "scene_name": "happy_scene",
  "fixture_count": 2
}
```

---

### Activate Scene

Activate a lighting scene.

```http
POST /api/scenes/{scene_name}/activate
```

**Parameters:**
- `scene_name` (path): Scene name

**Response:** `200 OK`

```json
{
  "success": true,
  "scene_name": "happy_scene",
  "transition_time_ms": 2000
}
```

---

### Emergency Stop

Activate emergency stop (instant blackout).

```http
POST /api/emergency-stop
```

**Response:** `200 OK`

```json
{
  "success": true,
  "state": "emergency_stop",
  "timestamp": "2026-04-09T12:00:00Z"
}
```

---

### Reset from Emergency

Reset from emergency stop state.

```http
POST /api/emergency-stop/reset
```

**Response:** `200 OK`

```json
{
  "success": true,
  "state": "idle",
  "message": "Reset from emergency stop"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid channel value: must be 0-255"
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Fixture not found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## WebSocket Events

The service also provides WebSocket events for real-time updates:

### Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

// Listen for state changes
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event, data.data);
};
```

### Events

| Event | Description | Data |
|-------|-------------|------|
| `channel_changed` | A channel value changed | `{fixture_id, channel, value}` |
| `scene_activated` | A scene was activated | `{scene_name, transition_time_ms}` |
| `emergency_stop` | Emergency stop activated | `{timestamp}` |
| `state_changed` | Controller state changed | `{old_state, new_state}` |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Default:** 100 requests per minute
- **Burst:** 10 requests per second

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617990000
```

---

## Authentication

(Currently not implemented - will be added for Phase 2 production)

---

## Examples

### Python

```python
import requests

# Get status
response = requests.get('http://localhost:8001/api/status')
print(response.json())

# Set channel
requests.put('http://localhost:8001/api/fixtures/mh_1/channels/1', json={'value': 255})

# Activate scene
requests.post('http://localhost:8001/api/scenes/happy/activate')
```

### JavaScript

```javascript
// Get status
fetch('http://localhost:8001/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Set channel
fetch('http://localhost:8001/api/fixtures/mh_1/channels/1', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({value: 255})
});

// Activate scene
fetch('http://localhost:8001/api/scenes/happy/activate', {
  method: 'POST'
});
```

---

## Changelog

### Version 1.0.0 (2026-04-09)
- Initial release
- Basic fixture control
- Scene management
- Emergency stop functionality
- WebSocket events
