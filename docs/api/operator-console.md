# Operator Console API Documentation

**Version:** 3.1.0
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

**Endpoint:** `GET /` or `GET /static/dashboard.html`

**Response:** HTML dashboard interface

**Description:** Single-page web dashboard with real-time service monitoring, alerts console, metrics charts, and service control panel.

**Features:**
- 8 service status cards with health indicators
- Real-time alerts console with acknowledge action
- Metrics charts (CPU, Memory, Request Rate, Error Rate)
- Control panel for start/stop/restart operations
- Event feed with system activity log
- WebSocket auto-reconnecting updates

**Access:** Open `http://localhost:8007` in browser

---

### 2. WebSocket: Real-time Updates

Connect to WebSocket for live updates.

**Endpoint:** `WS /ws`

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8007/ws');
```

**Subscribe to Channels:**

```json
{
  "action": "subscribe",
  "channels": ["metrics:SceneSpeak Agent", "alerts"]
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
  "service": "SceneSpeak Agent",
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
  "message": "SceneSpeak Agent CPU exceeded 80%",
  "source": "SceneSpeak Agent",
  "timestamp": "2026-03-04T12:00:00Z",
  "acknowledged": false
}
```

#### Status Update

```json
{
  "type": "status",
  "service": "Sentiment Agent",
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
      "name": "SceneSpeak Agent",
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

### 5.1. Get Services List

Get list of all monitored services with their status.

**Endpoint:** `GET /api/services`

**Response:**

```json
{
  "services": [
    {
      "name": "openclaw-orchestrator",
      "url": "http://localhost:8000",
      "status": "up",
      "health_check_url": "http://localhost:8000/health/live",
      "metrics_url": "http://localhost:8000/metrics"
    }
  ],
  "total": 8,
  "up": 7,
  "down": 0,
  "degraded": 1
}
```

---

### 5.2. Get All Metrics

Get current metrics from all services.

**Endpoint:** `GET /api/metrics`

**Response:**

```json
{
  "metrics": {
    "openclaw-orchestrator": {
      "service_name": "openclaw-orchestrator",
      "cpu_percent": 25.3,
      "memory_mb": 512,
      "request_rate": 45.2,
      "error_rate": 0.01
    }
  }
}
```

---

### 5.3. Control Service

Manually control a service (start, stop, restart).

**Endpoint:** `POST /api/control/{service_name}`

**Request Body:**

```json
{
  "action": "restart",
  "reason": "Performance degradation"
}
```

**Response:**

```json
{
  "service": "scenespeak-agent",
  "action": "restart",
  "status": "success",
  "message": "Service scenespeak-agent restart successful"
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
      "message": "SceneSpeak Agent CPU exceeded 80%",
      "source": "SceneSpeak Agent",
      "timestamp": "2026-03-04T12:00:00Z",
      "acknowledged": false
    },
    {
      "id": "alert_002",
      "severity": "critical",
      "title": "Service Down",
      "message": "Sentiment Agent is not responding",
      "source": "Sentiment Agent",
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

## Configuration

The Operator Console uses environment-based configuration with pydantic-settings. All parameters can be set via environment variables or in a `.env` file.

### Service Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `operator-console` | Service identifier for logging and tracing |
| `PORT` | `8007` | HTTP server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | `development` | Deployment environment |

### Service URLs

The Operator Console requires URLs to all Chimera services for health checks and metrics collection:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_ORCHESTRATOR_URL` | `http://localhost:8000` | Orchestrator service URL |
| `SCENESPEAK_AGENT_URL` | `http://localhost:8001` | SceneSpeak Agent URL |
| `CAPTIONING_AGENT_URL` | `http://localhost:8002` | Captioning Agent URL |
| `BSL_AGENT_URL` | `http://localhost:8003` | BSL Agent URL |
| `SENTIMENT_AGENT_URL` | `http://localhost:8004` | Sentiment Agent URL |
| `LIGHTING_SOUND_MUSIC_URL` | `http://localhost:8005` | Lighting/Sound/Music service URL |
| `SAFETY_FILTER_URL` | `http://localhost:8006` | Safety Filter URL |

**Note:** In Docker deployments, use service names instead of localhost (e.g., `http://openclaw-orchestrator:8000`).

### Metrics Collection

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_POLL_INTERVAL` | `5.0` | Seconds between metrics collection cycles |

### Alert Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT_CPU_THRESHOLD` | `80.0` | CPU percentage that triggers warning alert |
| `ALERT_MEMORY_THRESHOLD` | `2000.0` | Memory usage (MB) that triggers warning alert |
| `ALERT_ERROR_RATE_THRESHOLD` | `0.05` | Error rate (5%) that triggers warning alert |
| `ALERT_REQUEST_RATE_MINIMUM` | `0.1` | Minimum requests/second before low-rate alert |

### OpenTelemetry

| Variable | Default | Description |
|----------|---------|-------------|
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry Protocol endpoint for traces |

### Example Configuration File

```bash
# Service Configuration
SERVICE_NAME=operator-console
PORT=8007
LOG_LEVEL=INFO
ENVIRONMENT=production

# Service URLs
OPENCLAW_ORCHESTRATOR_URL=http://openclaw-orchestrator:8000
SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
CAPTIONING_AGENT_URL=http://captioning-agent:8002
BSL_AGENT_URL=http://bsl-agent:8003
SENTIMENT_AGENT_URL=http://sentiment-agent:8004
LIGHTING_SOUND_MUSIC_URL=http://lighting-sound-music:8005
SAFETY_FILTER_URL=http://safety-filter:8006

# Metrics Collection
METRICS_POLL_INTERVAL=5.0

# Alert Thresholds
ALERT_CPU_THRESHOLD=80.0
ALERT_MEMORY_THRESHOLD=2000.0
ALERT_ERROR_RATE_THRESHOLD=0.05
ALERT_REQUEST_RATE_MINIMUM=0.1

# OpenTelemetry
OTLP_ENDPOINT=http://jaeger:4317
```

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
*Operator Console v0.4.0*

---

## Code Examples

### WebSocket Connection (Python)

```python
import asyncio
import websockets
import json

async def connect_operator_console():
    """Connect to Operator Console WebSocket."""
    uri = "ws://localhost:8007/ws/realtime"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to channels
        subscribe_msg = {
            "action": "subscribe",
            "channels": ["metrics:SceneSpeak Agent", "alerts", "status"]
        }
        await websocket.send(json.dumps(subscribe_msg))
        
        # Listen for messages
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.recv(), 
                    timeout=30.0
                )
                data = json.loads(message)
                
                # Handle different message types
                if data["type"] == "metric":
                    print(f"Metric: {data['service']} - {data['metric']}: {data['value']}")
                elif data["type"] == "alert":
                    print(f"ALERT: {data['title']} - {data['message']}")
                elif data["type"] == "status":
                    print(f"Status: {data['service']} - {data['status']}")
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send(json.dumps({"action": "ping"}))

# Run the connection
asyncio.run(connect_operator_console())
```

### WebSocket Connection (JavaScript)

```javascript
// Connect to Operator Console WebSocket
const ws = new WebSocket('ws://localhost:8007/ws/realtime');

// Connection opened
ws.onopen = () => {
  console.log('Connected to Operator Console');
  
  // Subscribe to channels
  const subscribeMsg = {
    action: 'subscribe',
    channels: ['metrics:SceneSpeak Agent', 'alerts', 'status']
  };
  ws.send(JSON.stringify(subscribeMsg));
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'metric':
      updateMetricDisplay(data);
      break;
    case 'alert':
      showAlert(data);
      break;
    case 'status':
      updateStatusDisplay(data);
      break;
    default:
      console.log('Unknown message type:', data.type);
  }
};

// Connection closed
ws.onclose = () => {
  console.log('Disconnected from Operator Console');
};

// Connection error
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Update metric display function
function updateMetricDisplay(data) {
  const metricElement = document.getElementById(`metric-${data.service}-${data.metric}`);
  if (metricElement) {
    metricElement.textContent = `${data.value} ${data.unit}`;
    metricElement.className = getMetricClass(data.value);
  }
}

// Show alert function
function showAlert(data) {
  const alertBox = document.getElementById('alert-box');
  alertBox.innerHTML = `
    <div class="alert alert-${data.severity}">
      <strong>${data.title}</strong><br>
      ${data.message}<br>
      <small>${data.source} - ${new Date(data.timestamp).toLocaleString()}</small>
    </div>
  `;
}

// Update status display function
function updateStatusDisplay(data) {
  const statusBadge = document.getElementById(`status-${data.service}`);
  if (statusBadge) {
    statusBadge.className = `badge badge-${data.status}`;
    statusBadge.textContent = data.status;
  }
}
```

### REST API Examples

#### Get Dashboard Data

```python
import requests

# Get dashboard summary
response = requests.get("http://localhost:8007/api/dashboard")
dashboard = response.json()

print(f"Overall Health: {dashboard['overall_health']}")
print(f"Active Shows: {dashboard['active_shows']}")
print(f"Alerts: {dashboard['alerts']}")
```

#### Get Service Status

```python
import requests

# Get all service status
response = requests.get("http://localhost:8007/api/services/status")
services = response.json()

for service in services['services']:
    print(f"{service['name']}: {service['status']} (Port: {service['port']})")
```

#### Approve Pending Item

```python
import requests

# Approve a pending safety approval
item_id = "approval-abc123"
response = requests.post(
    f"http://localhost:8007/api/approvals/{item_id}/approve",
    json={"approver": "operator-name", "notes": "Looks good"}
)

if response.status_code == 200:
    print(f"Approved item {item_id}")
else:
    print(f"Approval failed: {response.text}")
```

### Error Handling Examples

#### Python with retry logic

```python
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with retry logic
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Connect with retry
try:
    response = session.get("http://localhost:8007/api/dashboard", timeout=10)
    response.raise_for_status()
    dashboard = response.json()
    
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.ConnectionError:
    print("Connection failed - is the service running?")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
```

#### JavaScript with fetch and async/await

```javascript
async function getDashboardData() {
  try {
    const response = await fetch('http://localhost:8007/api/dashboard');
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const dashboard = await response.json();
    console.log('Overall Health:', dashboard.overall_health);
    console.log('Active Shows:', dashboard.active_shows);
    
    return dashboard;
    
  } catch (error) {
    console.error('Failed to fetch dashboard:', error);
    throw error;
  }
}

// Auto-refresh dashboard every 5 seconds
setInterval(async () => {
  try {
    const dashboard = await getDashboardData();
    updateDashboardUI(dashboard);
  } catch (error) {
    console.error('Auto-refresh failed:', error);
  }
}, 5000);
```

