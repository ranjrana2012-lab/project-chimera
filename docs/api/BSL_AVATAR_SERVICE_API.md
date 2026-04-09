# Project Chimera Phase 2 - BSL Avatar Service API Documentation

**Version**: 1.0.0
**Service**: BSL Avatar Service
**Port**: 8003
**Protocol**: HTTP/REST
**Base URL**: `http://localhost:8003`

---

## Overview

The BSL Avatar Service provides REST API endpoints for translating text to British Sign Language (BSL) gestures, managing gesture libraries, and rendering avatars.

### Features

- Text-to-BSL translation
- Gesture library management
- Avatar rendering control
- Linguistic feature support
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
  "service": "bsl-avatar-service",
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
  "gesture_library_size": 100,
  "renderer_status": "ready",
  "translation_cache_size": 50
}
```

---

### Translation

#### POST /api/translate

Translate text to BSL gestures.

**Request Body**:
```json
{
  "text": "Hello, welcome to the show",
  "include_fingerspelling": false,
  "speed": 1.0
}
```

**Parameters**:
- `text` (string, required): Text to translate
- `include_fingerspelling` (boolean, optional): Include fingerspelling for unknown words
- `speed` (float, optional): Animation speed (0.5-2.0)

**Response**: `200 OK`

```json
{
  "translation_id": "trans_123456",
  "gestures": [
    {
      "word": "hello",
      "gesture_id": "hello",
      "part_of_speech": "interjection",
      "handshape": "open_hand",
      "orientation": "palm_out",
      "location": "forehead",
      "movement": "wave"
    },
    {
      "word": "welcome",
      "gesture_id": "welcome",
      "part_of_speech": "verb",
      "handshape": "open_hand",
      "orientation": "palm_up",
      "location": "chest",
      "movement": "circular"
    }
  ],
  "fingerspelled": [],
  "translation_time_ms": 150,
  "library_hit_rate": 1.0
}
```

#### POST /api/translate/render

Translate and render BSL with avatar.

**Request Body**:
```json
{
  "text": "Thank you for watching",
  "render_options": {
    "avatar_id": "default",
    "quality": "high",
    "include_facial_expressions": true
  }
}
```

**Response**: `200 OK`

```json
{
  "translation_id": "trans_123457",
  "render_id": "render_987654",
  "gestures": [...],
  "render_time_ms": 2500,
  "avatar_url": "/renders/render_987654.mp4"
}
```

---

### Gesture Library

#### GET /api/gestures

List all gestures in the library.

**Query Parameters**:
- `limit` (integer, optional): Number of results to return
- `offset` (integer, optional): Offset for pagination

**Response**:
```json
{
  "gestures": [
    {
      "id": "hello",
      "word": "hello",
      "part_of_speech": "interjection",
      "handshape": "open_hand",
      "orientation": "palm_out",
      "location": "forehead",
      "movement": "wave",
      "non_manual_features": {}
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/gestures/{gesture_id}

Get details of a specific gesture.

**Parameters**:
- `gesture_id` (path): Gesture identifier

**Response**: `200 OK`

```json
{
  "id": "hello",
  "word": "hello",
  "part_of_speech": "interjection",
  "handshape": "open_hand",
  "orientation": "palm_out",
  "location": "forehead",
  "movement": "wave",
  "non_manual_features": {
    "facial_expression": "friendly",
    "body_language": "open"
  }
}
```

#### POST /api/gestures

Add a new gesture to the library.

**Request Body**:
```json
{
  "id": "thankyou",
  "word": "thank you",
  "part_of_speech": "verb",
  "handshape": "open_hand",
  "orientation": "palm_out",
  "location": "chest",
  "movement": "circular",
  "non_manual_features": {
    "facial_expression": "grateful"
  }
}
```

**Response**: `201 Created`

```json
{
  "id": "thankyou",
  "status": "added"
}
```

#### PUT /api/gestures/{gesture_id}

Update an existing gesture.

**Parameters**:
- `gesture_id` (path): Gesture identifier

**Request Body**: (same as POST)

**Response**: `200 OK`

#### DELETE /api/gestures/{gesture_id}

Remove a gesture from the library.

**Parameters**:
- `gesture_id` (path): Gesture identifier

**Response**: `204 No Content`

---

## Avatar Rendering

#### POST /api/avatar/render

Render a specific gesture sequence.

**Request Body**:
```json
{
  "gesture_sequence": ["hello", "welcome", "thankyou"],
  "render_options": {
    "avatar_id": "default",
    "quality": "high",
    "fps": 30,
    "include_facial_expressions": true
  }
}
```

**Response**: `200 OK`

```json
{
  "render_id": "render_123456",
  "status": "rendering",
  "estimated_time_ms": 3000,
  "gestures_count": 3
}
```

#### GET /api/avatar/render/{render_id}

Get render status and result.

**Parameters**:
- `render_id` (path): Render identifier

**Response**: `200 OK`

```json
{
  "render_id": "render_123456",
  "status": "complete",
  "video_url": "/renders/render_123456.mp4",
  "duration_ms": 2850,
  "thumbnail_url": "/renders/render_123456_thumb.jpg"
}
```

---

## Data Models

### Gesture

```python
{
  "id": str,                         # Unique identifier
  "word": str,                       # English word
  "part_of_speech": str,             # Grammatical category
  "handshape": str,                  # Hand configuration
  "orientation": str,                 # Palm orientation
  "location": str,                    # Body position
  "movement": str,                    # Movement pattern
  "non_manual_features": {           # Facial/body expressions
    "facial_expression": str,
    "body_language": str
  }
}
```

### TranslationRequest

```python
{
  "text": str,                       # Text to translate
  "include_fingerspelling": bool,     # Include fingerspelling
  "speed": float                      # Animation speed
}
```

### TranslationResponse

```python
{
  "translation_id": str,              # Unique translation ID
  "gestures": List[Gesture],           # BSL gestures
  "fingerspelled": List[str],         # Fingerspelled words
  "translation_time_ms": int,         # Processing time
  "library_hit_rate": float           # Gesture library hit rate
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
| `TEXT_REQUIRED` | Text field is required |
| `GESTURE_NOT_FOUND` | Gesture does not exist |
| `INVALID_SPEED` | Speed must be 0.5-2.0 |
| `RENDER_FAILED` | Avatar rendering failed |
| `TRANSLATION_FAILED` | Text translation failed |

---

## Rate Limiting

**Current Status**: No rate limiting (development mode)

**Production Recommendation**:
```python
# Suggested limits
- /api/translate: 30 requests/minute
- /api/gestures: 100 requests/minute
- /api/avatar/render: 10 requests/minute
```

---

## WebSocket Events

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8003/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

### Event Types

#### translation_complete

Emitted when translation completes.

```json
{
  "type": "translation_complete",
  "timestamp": "2026-04-09T15:30:00Z",
  "payload": {
    "translation_id": "trans_123456",
    "gesture_count": 3,
    "translation_time_ms": 150
  }
}
```

#### render_complete

Emitted when avatar rendering completes.

```json
{
  "type": "render_complete",
  "timestamp": "2026-04-09T15:31:00Z",
  "payload": {
    "render_id": "render_987654",
    "video_url": "/renders/render_987654.mp4",
    "duration_ms": 2850
  }
}
```

---

## Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8003"

# Translate text to BSL
response = requests.post(f"{BASE_URL}/api/translate", json={
    "text": "Hello, welcome to the show",
    "include_fingerspelling": False,
    "speed": 1.0
})
result = response.json()
print(f"Gestures: {len(result['gestures'])}")
print(f"Time: {result['translation_time_ms']}ms")

# Translate and render
response = requests.post(f"{BASE_URL}/api/translate/render", json={
    "text": "Thank you for watching",
    "render_options": {
        "quality": "high",
        "include_facial_expressions": True
    }
})
result = response.json()
print(f"Render ID: {result['render_id']}")
print(f"Video URL: {result['avatar_url']}")
```

### JavaScript Client

```javascript
const BASE_URL = 'http://localhost:8003';

// Translate text
async function translateToBSL(text, options = {}) {
  const response = await fetch(`${BASE_URL}/api/translate`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text,
      include_fingerspelling: false,
      speed: 1.0,
      ...options
    })
  });
  return await response.json();
}

// Render avatar
async function renderAvatar(text, renderOptions = {}) {
  const response = await fetch(`${BASE_URL}/api/translate/render`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text,
      render_options: {
        quality: 'high',
        include_facial_expressions: true,
        ...renderOptions
      }
    })
  });
  return await response.json();
}
```

---

## Monitoring

### Metrics

The BSL Avatar Service exposes Prometheus metrics at `/metrics`:

- `chimera_bsl_requests_total` - Total API requests
- `chimera_bsl_translations_total` - Translations performed
- `chimera_bsl_renders_total` - Avatar renders
- `chimera_bsl_library_hit_rate` - Gesture library hit rate
- `chimera_bsl_avg_gestures_per_translation` - Average gestures per translation
- `chimera_bsl_render_time_ms` - Render duration

### Tracing

Spans are created for:
- Translation operations
- Avatar rendering
- Gesture library lookups
- API requests

---

## Security Considerations

### Input Validation

- Text input length validated (max 1000 characters)
- Speed parameter validated (0.5-2.0 range)
- Gesture IDs validated to exist

### Performance

- Translation caching to improve response time
- Library hit rate monitoring
- Render queue management

### Production Recommendations

1. **Authentication**: Implement API key or JWT
2. **Input Sanitization**: Sanitize all text input
3. **Rate Limiting**: Implement strict limits on translation/render
4. **Content Moderation**: Validate input text for inappropriate content
5. **Audit Logging**: Log all translations for research purposes

---

## BSL-Specific Considerations

### Linguistic Accuracy

The service uses a gesture library with linguistic features:
- **Part of Speech**: Grammatical category of words
- **Handshape**: Configuration of hand
- **Orientation**: Palm and finger orientation
- **Location**: Position on body
- **Movement**: Motion pattern
- **Non-Manual Features**: Facial expressions, body language

### Regional Variations

**Current**: Uses standard BSL
**Future Enhancement**: Support for regional variations

### Accessibility

**Current**: Text-to-BSL translation
**Future Enhancement**: Sign-to-text for deaf audience input

---

## Changelog

### Version 1.0.0 (2026-04-09)
- Initial release
- Text-to-BSL translation
- Gesture library management
- Avatar rendering
- WebSocket events
- Linguistic features support
