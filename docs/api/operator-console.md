# Operator Console API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8007`
**Service:** Human oversight dashboard with real-time WebSocket updates

---

## Overview

The Operator Console provides:
- Real-time oversight of all Chimera services
- WebSocket-based live metrics and alerts
- Manual approval and override controls
- Event streaming and notifications

---

## Endpoints

### 1. Web Dashboard

**Endpoint:** `GET /`

**Response:** HTML dashboard interface

---

### 2. WebSocket: Real-time Updates

Connect to WebSocket for live updates.

**Endpoint:** `WS /ws/realtime`

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8007/ws/realtime');
```

**Subscribe to Channels:**

```json
{
  "action": "subscribe",
  "channels": ["metrics:scenespeak-agent", "alerts"]
}
```

**Available Channels:**

| Channel Pattern | Description |
|-----------------|-------------|
| `metrics:<service>` | Metrics for specific service |
| `alerts` | All alerts |
| `status` | Service status changes |
| `chat` | Chat messages (if enabled) |
| `control` | Control events |

**Message Types:**

#### Metric Update

```json
{
  "type": "metric",
  "service": "scenespeak-agent",
  "metric": "cpu_percent",
  "value": 45.2,
  "unit": "%",
  "timestamp": "2026-03-04T12:00:00Z",
  "metadata": {}
}
```

#### Alert Update

```json
{
  "type": "alert",
  "id": "alert_abc123",
  "severity": "warning",
  "title": "High CPU Usage",
  "message": "scenespeak-agent CPU exceeded 80%",
  "source": "scenespeak-agent",
  "timestamp": "2026-03-04T12:00:00Z",
  "acknowledged": false
}
```

#### Status Update

```json
{
  "type": "status",
  "service": "sentiment-agent",
  "status": "up",
  "health_check": "healthy",
  "last_check": "2026-03-04T12:00:00Z"
}
```

---

### 3. Submit Approval

Manually approve a pending action.

**Endpoint:** `POST /v1/approve`

**Request Body:**

```json
{
  "action_id": "action_123",
  "approved": true,
  "reason": "Content is acceptable",
  "operator": "operator_1"
}
```

**Response:**

```json
{
  "success": true,
  "action_id": "action_123",
  "status": "approved",
  "timestamp": "2026-03-04T12:00:00Z"
}
```

---

### 4. Manual Override

Manually override automated systems.

**Endpoint:** `POST /v1/override`

**Request Body:**

```json
{
  "system": "lighting",
  "override_type": "blackout",
  "parameters": {
    "duration": 10
  },
  "reason": "Emergency stop",
  "operator": "operator_1"
}
```

**Response:**

```json
{
  "success": true,
  "override_id": "override_456",
  "status": "active",
  "expires_at": "2026-03-04T12:10:00Z"
}
```

---

### 5. Get Service Status

Get status of all Chimera services.

**Endpoint:** `GET /v1/services/status`

**Response:**

```json
{
  "services": [
    {
      "name": "openclaw-orchestrator",
      "status": "up",
      "port": 8000,
      "health_check": "healthy",
      "metrics": {
        "cpu_percent": 25.3,
        "memory_mb": 512,
        "request_rate": 45.2
      }
    },
    {
      "name": "scenespeak-agent",
      "status": "up",
      "port": 8001,
      "health_check": "healthy",
      "metrics": {
        "cpu_percent": 67.8,
        "memory_mb": 1024,
        "request_rate": 12.5
      }
    }
  ],
  "total": 8,
  "up": 8,
  "down": 0,
  "degraded": 0
}
```

---

### 6. Get Active Alerts

Get all active alerts.

**Endpoint:** `GET /v1/alerts/active`

**Response:**

```json
{
  "alerts": [
    {
      "id": "alert_001",
      "severity": "warning",
      "title": "High CPU Usage",
      "message": "scenespeak-agent CPU exceeded 80%",
      "source": "scenespeak-agent",
      "timestamp": "2026-03-04T12:00:00Z",
      "acknowledged": false
    },
    {
      "id": "alert_002",
      "severity": "critical",
      "title": "Service Down",
      "message": "sentiment-agent is not responding",
      "source": "sentiment-agent",
      "timestamp": "2026-03-04T11:55:00Z",
      "acknowledged": true
    }
  ],
  "total": 2,
  "unacknowledged": 1
}
```

---

### 7. Acknowledge Alert

Acknowledge an alert.

**Endpoint:** `POST /v1/alerts/{alert_id}/acknowledge`

**Request Body:**

```json
{
  "operator": "operator_1",
  "note": "Investigating the issue"
}
```

**Response:**

```json
{
  "success": true,
  "alert_id": "alert_001",
  "acknowledged": true,
  "timestamp": "2026-03-04T12:00:00Z"
}
```

---

### 8. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

### 9. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format.

---

## Examples

### WebSocket Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8007/ws/realtime');

// Subscribe to updates
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['metrics:*', 'alerts']
  }));
};

// Handle updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Received:', update);

  if (update.type === 'alert') {
    showAlert(update);
  } else if (update.type === 'metric') {
    updateMetricChart(update);
  }
};

// Unsubscribe before closing
ws.onclose = () => {
  ws.send(JSON.stringify({
    action: 'unsubscribe',
    channels: ['all']
  }));
};
```

### Manual Approval

```bash
curl -X POST http://localhost:8007/v1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "action_123",
    "approved": true,
    "reason": "Content is acceptable",
    "operator": "operator_1"
  }'
```

### Get Service Status

```bash
curl http://localhost:8007/v1/services/status
```

---

## Alert Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| `critical` | Service down or critical failure | Immediate action |
| `warning` | Degraded performance or concerning metric | Monitor closely |
| `info` | Informational event | No action required |

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_ACTION_ID",
    "message": "Action not found",
    "details": {}
  }
}
```

---

*Last Updated: March 2026*
*Operator Console v3.0.0*
