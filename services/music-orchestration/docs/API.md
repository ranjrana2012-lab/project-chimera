# Music Orchestration Service - API Documentation

## Base URL
```
http://music-orchestration.chimera.svc.cluster.local:8012
```

## Authentication
All endpoints require JWT bearer token:
```
Authorization: Bearer <token>
```

## Endpoints

### POST /api/v1/music/generate
Generate music with caching and approval.

**Request:**
```json
{
  "prompt": "upbeat electronic background",
  "use_case": "marketing",
  "duration_seconds": 30,
  "format": "mp3",
  "genre": "electronic",
  "mood": "upbeat",
  "tempo": 120
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "music_id": "uuid",
  "status": "cached",
  "audio_url": "https://...",
  "duration_seconds": 30,
  "format": "mp3",
  "was_cache_hit": true
}
```

### GET /api/v1/music/{music_id}
Get music metadata.

### POST /api/v1/music/{music_id}/approve
Approve show music for use.

### WebSocket /ws/music/{request_id}
Real-time progress updates.

**Message:**
```json
{
  "type": "progress",
  "request_id": "uuid",
  "progress": 50,
  "stage": "inference",
  "eta_seconds": 15
}
```
