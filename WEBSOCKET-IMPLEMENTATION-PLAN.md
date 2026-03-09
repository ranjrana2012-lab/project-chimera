# WebSocket Implementation Plan - E2E Tests

## Current Status

### WebSocket Endpoints Status

| Service | Expected Path | Current Status | Tests Affected |
|---------|---------------|----------------|----------------|
| Orchestrator | `ws://localhost:8000/ws/show` | ✅ Implemented | 20+ tests |
| Sentiment | `ws://localhost:8004/ws/sentiment` | ❌ Missing | 5 tests |
| Captioning | `ws://localhost:8002/ws/captions` | ⚠️ Has `/v1/stream` | 3 tests |
| BSL Avatar | `ws://localhost:8003/ws/avatar` | ✅ Implemented | 5 tests |

## Orchestrator WebSocket (Port 8000)

**Status**: Already implemented at `/ws/show`

**Features**:
- Connection management with client tracking
- Initial state broadcast on connect
- Message echo for testing
- Broadcasting to all connected clients
- Sentiment update broadcasting
- Show state management

**Code Location**: `services/openclaw-orchestrator/main.py:292`

## Required Implementations

### 1. Sentiment Agent WebSocket (`ws://localhost:8004/ws/sentiment`)

**Purpose**: Broadcast real-time sentiment analysis results to connected clients

**Requirements from E2E tests**:
```typescript
// Test expects to connect and receive sentiment updates
const wsClient = await createWebSocketClient('ws://localhost:8004/ws/sentiment');
```

**Implementation needed**:

```python
# Add to services/sentiment-agent/src/sentiment_agent/main.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json

# Connection manager
class SentimentConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_sentiment(self, sentiment_data: dict):
        """Broadcast sentiment update to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "sentiment_update",
                    "data": sentiment_data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception:
                disconnected.add(connection)
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = SentimentConnectionManager()

@app.websocket("/ws/sentiment")
async def websocket_sentiment(websocket: WebSocket):
    """WebSocket endpoint for real-time sentiment updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive ping messages
            data = await websocket.receive_text()
            # Could handle ping/pong here
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
```

**Integration**: Update the `/api/analyze` endpoint to broadcast results:

```python
@app.post("/api/analyze")
async def analyze_sentiment_api(request: dict):
    # ... existing analysis code ...

    # Broadcast to WebSocket clients
    await manager.broadcast_sentiment({
        "sentiment": result["sentiment"],
        "score": result["score"],
        "confidence": result["confidence"],
        "emotions": result["emotions"]
    })

    return response
```

### 2. Captioning Agent WebSocket (`ws://localhost:8002/ws/captions`)

**Purpose**: Stream real-time caption updates to connected clients

**Current state**: Has `/v1/stream` endpoint, but tests expect `/ws/captions`

**Implementation needed**:

```python
# Add to services/captioning-agent/main.py

from typing import Set

class CaptioningConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_caption(self, caption_data: dict):
        """Broadcast caption update to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "caption_update",
                    "data": caption_data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception:
                disconnected.add(connection)
        for conn in disconnected:
            self.disconnect(conn)

caption_manager = CaptioningConnectionManager()

@app.websocket("/ws/captions")
async def websocket_captions(websocket: WebSocket):
    """WebSocket endpoint for real-time caption updates"""
    await caption_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        caption_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        caption_manager.disconnect(websocket)
```

## Test Files Using These WebSockets

1. `tests/e2e/websocket/sentiment-updates.spec.ts`:
   - Line 30: `ws://localhost:8000/ws/show` ✅
   - Line 166: `ws://localhost:8003/ws/avatar` ✅
   - Line 433: `ws://localhost:8002/ws/captions` ❌ Needs implementation
   - Line 460: `ws://localhost:8004/ws/sentiment` ❌ Needs implementation

## Implementation Order

1. **Sentiment Agent WebSocket** (Priority 1)
   - Add connection manager
   - Add `/ws/sentiment` endpoint
   - Integrate with `/api/analyze` to broadcast results
   - Rebuild and test

2. **Captioning Agent WebSocket** (Priority 2)
   - Add connection manager
   - Add `/ws/captions` endpoint
   - Integrate with `/api/transcribe` to broadcast results
   - Rebuild and test

## Files to Modify

### Sentiment Agent
- `services/sentiment-agent/src/sentiment_agent/main.py`
  - Add `SentimentConnectionManager` class
  - Add `@app.websocket("/ws/sentiment")` endpoint
  - Update `/api/analyze` to broadcast results

### Captioning Agent
- `services/captioning-agent/main.py`
  - Add `CaptioningConnectionManager` class
  - Add `@app.websocket("/ws/captions")` endpoint
  - Update `/api/transcribe` to broadcast results

## Testing After Implementation

```bash
# Test sentiment WebSocket
wscat -c ws://localhost:8004/ws/sentiment

# Test captioning WebSocket
wscat -c ws://localhost:8002/ws/captions

# Run WebSocket E2E tests
cd tests/e2e
npm run test -- --grep "@websocket" --reporter=list
```

## Notes

- The orchestrator WebSocket implementation can serve as a reference
- Connection managers should handle disconnections gracefully
- Broadcasting should be non-blocking (don't fail if a client disconnects)
- Consider adding ping/pong for connection health monitoring
