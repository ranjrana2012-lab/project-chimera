# BSL Avatar Service API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8003`

## Endpoints

### Health Check

```http
GET /health
```

### Get Service Status

```http
GET /api/status
```

**Response:**

```json
{
  "state": "idle",
  "gesture_library_size": 10,
  "current_sign_sequence": false
}
```

### Translate Text

```http
POST /api/translate
```

**Request Body:**

```json
{
  "text": "hello thank you"
}
```

**Response:**

```json
{
  "success": true,
  "gestures": [
    {"word": "hello", "timing_ms": 1000},
    {"word": "thank", "timing_ms": 1000},
    {"word": "you", "timing_ms": 1000}
  ],
  "non_manual_features": [
    {"facial_expression": "friendly", "eyebrows": "raised"},
    {"facial_expression": "grateful", "eyebrows": "relaxed"},
    {"facial_expression": "neutral", "eyebrows": "relaxed"}
  ]
}
```

### Translate and Render

```http
POST /api/translate-and-render
```

**Request Body:**

```json
{
  "text": "what is your name?"
}
```

**Response:**

```json
{
  "success": true,
  "rendering": true,
  "gestures_count": 4
}
```

### Get Gesture Library Info

```http
GET /api/gestures
```

**Response:**

```json
{
  "total_gestures": 10,
  "gestures": [
    {"word": "hello", "part_of_speech": "interjection"},
    {"word": "thank", "part_of_speech": "verb"}
  ]
}
```

### Add Gesture to Library

```http
POST /api/gestures
```

**Request Body:**

```json
{
  "word": "welcome",
  "part_of_speech": "interjection",
  "handshape": "open_hand",
  "orientation": "palm_up",
  "location": "side",
  "movement": "sweep_in",
  "non_manual_features": {
    "facial_expression": "friendly",
    "eyebrows": "raised"
  }
}
```

## WebSocket Events

| Event | Description |
|-------|-------------|
| `translation_start` | Translation started |
| `gesture_render` | Gesture being rendered |
| `translation_complete` | Translation complete |
| `rendering_complete` | Rendering complete |

## Examples

### Python

```python
import requests

# Translate text
response = requests.post('http://localhost:8003/api/translate',
                          json={'text': 'hello thank you'})
data = response.json()
print(f"Gestures: {len(data['gestures'])}")
```

### JavaScript

```javascript
// Translate and render
fetch('http://localhost:8003/api/translate-and-render', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'what is your name?'})
})
.then(response => response.json())
.then(data => console.log('Rendering:', data.rendering));
```
