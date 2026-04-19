# Project Chimera - WebSocket Implementation

## Overview

This document describes the WebSocket implementation for Project Chimera real-time updates.

## Architecture

```
Client → Orchestrator WebSocket → Event Stream
                              ↓
                         Service Events
                              ↓
                         Redis Pub/Sub
                              ↓
                         Connected Clients
```

## WebSocket Endpoints

### Connection

```javascript
// Connect to orchestrator WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected to Chimera WebSocket');

    // Subscribe to orchestration updates
    ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'orchestration_updates'
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleWebSocketMessage(message);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('WebSocket connection closed');
    // Implement reconnection logic
    setTimeout(() => connectWebSocket(), 5000);
};
```

## Message Types

### Client → Server Messages

#### Subscribe

```json
{
  "type": "subscribe",
  "channel": "orchestration_updates"
}
```

**Channels:**
- `orchestration_updates` - Real-time orchestration status
- `show_control` - Show control events
- `health_updates` - Service health changes
- `alerts` - Critical alerts

#### Orchestrate Request

```json
{
  "type": "orchestrate",
  "data": {
    "prompt": "User prompt",
    "show_id": "show_001",
    "options": {
      "enable_sentiment": true,
      "enable_safety": true
    }
  }
}
```

#### Unsubscribe

```json
{
  "type": "unsubscribe",
  "channel": "orchestration_updates"
}
```

### Server → Client Messages

#### Orchestration Update

```json
{
  "type": "orchestration_update",
  "data": {
    "orchestration_id": "orch_12345",
    "status": "processing",
    "progress": 0.3,
    "current_step": "analyzing_sentiment",
    "result": null
  }
}
```

**Status values:** `queued`, `processing`, `completed`, `failed`

#### Orchestration Complete

```json
{
  "type": "orchestration_complete",
  "data": {
    "orchestration_id": "orch_12345",
    "status": "completed",
    "result": {
      "dialogue": "Generated dialogue here",
      "sentiment": {"label": "positive", "confidence": 0.92},
      "safety_check": {"safe": true}
    }
  }
}
```

#### Health Update

```json
{
  "type": "health_update",
  "data": {
    "service": "sentiment-agent",
    "status": "healthy",
    "timestamp": "2026-04-19T12:00:00Z"
  }
}
```

#### Alert

```json
{
  "type": "alert",
  "data": {
    "level": "warning",
    "message": "High memory usage on sentiment-agent",
    "service": "sentiment-agent",
    "timestamp": "2026-04-19T12:00:00Z"
  }
}
```

## Implementation

### Server-Side (FastAPI)

```python
# services/openclaw-orchestrator/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscribers: Dict[str, set] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        print(f"Client {client_id} disconnected")

    def subscribe(self, client_id: str, channel: str):
        if channel not in self.subscribers:
            self.subscribers[channel] = set()
        self.subscribers[channel].add(client_id)

    def unsubscribe(self, client_id: str, channel: str):
        if channel in self.subscribers:
            self.subscribers[channel].discard(client_id)

    async def broadcast(self, message: dict, channel: str = None):
        if channel:
            subscribers = self.subscribers.get(channel, set())
        else:
            subscribers = set(self.active_connections.keys())

        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    print(f"Error sending to {client_id}: {e}")
                    self.disconnect(client_id)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = id(websocket)
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "subscribe":
                manager.subscribe(client_id, data["channel"])
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": data["channel"]
                })

            elif data["type"] == "unsubscribe":
                manager.unsubscribe(client_id, data["channel"])
                await websocket.send_json({
                    "type": "unsubscribed",
                    "channel": data["channel"]
                })

            elif data["type"] == "orchestrate":
                # Handle orchestration request
                result = await handle_orchestration(data["data"])
                await websocket.send_json({
                    "type": "orchestration_complete",
                    "data": result
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

### Client-Side (JavaScript)

```javascript
class ChimeraWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectDelay = 5000;
        this.maxReconnectDelay = 30000;
        this.subscriptions = new Set();
        this.handlers = {};
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Connected to Chimera WebSocket');
            this.reconnectDelay = 5000;

            // Re-subscribe to channels
            this.subscriptions.forEach(channel => {
                this.send({ type: 'subscribe', channel });
            });
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        };
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    subscribe(channel, handler) {
        this.subscriptions.add(channel);
        this.handlers[channel] = handler;
        this.send({ type: 'subscribe', channel });
    }

    unsubscribe(channel) {
        this.subscriptions.delete(channel);
        delete this.handlers[channel];
        this.send({ type: 'unsubscribe', channel });
    }

    handleMessage(message) {
        const { type, data } = message;

        if (type === 'orchestration_update' && this.handlers['orchestration_updates']) {
            this.handlers['orchestration_updates'](data);
        } else if (type === 'health_update' && this.handlers['health_updates']) {
            this.handlers['health_updates'](data);
        } else if (type === 'alert' && this.handlers['alerts']) {
            this.handlers['alerts'](data);
        }
    }

    orchestrate(prompt, showId, options = {}) {
        return new Promise((resolve, reject) => {
            const requestId = `req_${Date.now()}`;

            const handler = (data) => {
                if (data.orchestration_id === requestId) {
                    resolve(data.result);
                    this.unsubscribe('orchestration_updates');
                }
            };

            this.subscribe('orchestration_updates', handler);

            this.send({
                type: 'orchestrate',
                data: {
                    prompt,
                    show_id: showId,
                    ...options
                }
            });
        });
    }
}

// Usage
const chimera = new ChimeraWebSocket('ws://localhost:8000/ws');
chimera.connect();

// Subscribe to health updates
chimera.subscribe('health_updates', (data) => {
    console.log('Health update:', data.service, data.status);
});

// Subscribe to alerts
chimera.subscribe('alerts', (data) => {
    console.alert(`[${data.level.toUpperCase()}] ${data.message}`);
});

// Orchestrate with real-time updates
chimera.orchestrate(
    "Create dialogue for excited audience",
    "show_001",
    { enable_sentiment: true }
).then(result => {
    console.log('Orchestration complete:', result);
});
```

## Testing WebSocket

### Python Test

```python
# tests/integration/test_websocket.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from services.openclaw_orchestrator.main import app

@pytest.mark.asyncio
async def test_websocket_connection():
    from services.openclaw_orchestrator.websocket import manager

    # Mock WebSocket connection
    class MockWebSocket:
        async def send_json(self, data):
            print(f"Sent: {data}")

        async def receive_json(self):
            return {"type": "subscribe", "channel": "test"}

    ws = MockWebSocket()
    await manager.connect(ws, "test_client")

    # Test subscription
    ws.send_json({"type": "subscribe", "channel": "test_channel"})

    # Test broadcast
    await manager.broadcast({
        "type": "test_message",
        "data": {"test": "data"}
    })
```

### JavaScript Test

```javascript
// tests/websocket/test_connection.html
<!DOCTYPE html>
<html>
<head>
    <title>Chimera WebSocket Test</title>
</head>
<body>
    <h1>WebSocket Test</h1>
    <div id="messages"></div>
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        const messages = document.getElementById('messages');

        ws.onopen = () => {
            addMessage('Connected!');

            // Subscribe to health updates
            ws.send(JSON.stringify({
                type: 'subscribe',
                channel: 'health_updates'
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            addMessage(`Received: ${JSON.stringify(message, null, 2)}`);
        };

        function addMessage(text) {
            const div = document.createElement('div');
            div.textContent = text;
            messages.appendChild(div);
        }
    </script>
</body>
</html>
```

## Reconnection Strategy

### Exponential Backoff

```javascript
class ReconnectingWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Connected');
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
        };

        this.ws.onclose = () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    this.reconnectDelay *= 2;
                    this.connect();
                }, this.reconnectDelay);
            }
        };
    }
}
```

## Security Considerations

### Authentication

```python
# Add JWT authentication to WebSocket
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Validate token
    user = await validate_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    # Continue with connection...
```

### Rate Limiting

```python
# Limit connections per user
from collections import defaultdict

connection_counts = defaultdict(int)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = websocket.client.host

    if connection_counts[client_id] >= 5:
        await websocket.close(code=1008)
        return

    connection_counts[client_id] += 1

    try:
        # Handle connection
        pass
    finally:
        connection_counts[client_id] -= 1
```

---

**Status:** Planned Feature
**Target Release:** Q2 2026
