# Operator Console Completion Design

**Date:** March 6, 2026
**Status:** Design
**Goal:** Complete Operator Console with single integrated dashboard

---

## Overview

Create a comprehensive single-page HTML dashboard for the Operator Console that provides real-time monitoring, alerting, and control capabilities for all Project Chimera services.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OPERATOR CONSOLE DASHBOARD                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    HEADER SECTION                            │   │
│  │  Project Chimera Operator Console | Status: All Systems Go  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│           ┌───────────────┼───────────────┐                        │
│           ▼               ▼               ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │   SERVICE    │ │    ALERTS    │ │   CONTROL    │              │
│  │   STATUS     │ │   CONSOLE    │ │   PANEL      │              │
│  │              │ │              │ │              │              │
│  │ • OpenClaw   │ │ • Warnings   │ │ • Start      │              │
│  │ • SceneSpeak │ │ • Critical   │ │ • Stop       │              │
│  │ • Captioning │ │ • Info       │ │ • Restart    │              │
│  │ • BSL        │ │              │ │              │              │
│  │ • Sentiment  │ │ [Acknowledge]│ │              │              │
│  │ • Lighting   │ │ [Filter]     │ │              │              │
│  │ • Safety     │ │              │ │              │              │
│  │ • Console    │ │              │ │              │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
│           │               │               │                        │
│           └───────────────┼───────────────┘                        │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    METRICS SECTION                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │   │
│  │  │   CPU %     │ │  Memory MB  │ │ Request/s   │          │   │
│  │  │  (Sparkline)│ │  (Sparkline)│ │  (Sparkline)│          │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EVENT FEED                               │   │
│  │  [10:23:45] OpenClaw health check passed                    │   │
│  │  [10:23:42] Alert: SceneSpeak CPU > 80%                     │   │
│  │  [10:23:40] Captioning agent started                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

                              │
                              ▼
        ┌─────────────────────────────────────┐
        │      Backend API (FastAPI)          │
        │  • /api/services                   │
        │  • /api/services/{id}/metrics      │
        │  • /api/alerts                     │
        │  • /api/services/{id}/control      │
        │  • /ws (WebSocket for real-time)    │
        └─────────────────────────────────────┘
```

---

## Components

### 1. Dashboard HTML (`services/operator-console/static/dashboard.html`)

**Single file containing:**
- HTML structure
- Embedded CSS (Tailwind via CDN + custom styles)
- Embedded JavaScript (WebSocket client, chart rendering)

**Sections:**

#### Header
- Project Chimera branding
- Overall system status indicator
- Current timestamp (auto-updating)
- Connection status to WebSocket

#### Service Status Panel (Left Column)
- 8 service cards (OpenClaw, SceneSpeak, Captioning, BSL, Sentiment, Lighting, Safety, Console)
- Each card shows:
  - Service name and icon
  - Health status (🟢 Healthy / 🟡 Degraded / 🔴 Unhealthy)
  - CPU/Memory mini sparklines
  - Last update timestamp
  - Quick action buttons (logs, restart)

#### Alerts Console (Center Column)
- Live alert feed
- Severity color coding (Critical=Red, Warning=Yellow, Info=Blue)
- Timestamp and service source
- Acknowledge button per alert
- Filter controls by severity/service
- Auto-refresh via WebSocket

#### Control Panel (Right Column)
- Service control buttons
  - Start/Stop/Restart per service
  - Bulk actions (Start All, Stop All)
- Control confirmation dialogs
- Action result feedback

#### Metrics Section (Bottom)
- CPU usage chart (last 5 minutes, sparkline)
- Memory usage chart (last 5 minutes, sparkline)
- Request rate chart (per service)
- Embedded Grafana iframe link

#### Event Feed (Footer)
- Scrolling log of system events
- Color-coded by type
- Auto-scroll toggle
- Export to clipboard button

### 2. JavaScript Modules (Embedded in HTML)

**WebSocket Manager:**
```javascript
class WSManager {
  connect(url)              // Connect to /ws endpoint
  onMessage(callback)       // Handle incoming updates
  send(action, data)        // Send control commands
  reconnect()               // Auto-reconnect on disconnect
}
```

**Service Monitor:**
```javascript
class ServiceMonitor {
  pollServices()            // HTTP GET /api/services
  updateDisplay(data)       // Update service cards
  checkHealthStatus()       // Determine health badge
}
```

**Alert Manager:**
```javascript
class AlertManager {
  fetchAlerts()             // GET /api/alerts
  renderAlert(alert)        // Create alert DOM element
  acknowledgeAlert(id)      // POST /api/alerts/{id}/acknowledge
}
```

**Chart Renderer:**
```javascript
class ChartRenderer {
  renderSparkline(canvas, data)  // Mini line charts
  updateChart(chart, newData)     // Incremental updates
}
```

### 3. Configuration Files

**`config/prometheus.yml`:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'chimera-services'
    static_configs:
      - targets:
        - 'openclaw-orchestrator:8000'
        - 'scenespeak-agent:8001'
        - 'captioning-agent:8002'
        - 'bsl-agent:8003'
        - 'sentiment-agent:8004'
        - 'lighting-sound-music:8005'
        - 'safety-filter:8006'
        - 'operator-console:8007'
```

**`config/grafana/datasources/prometheus.yml`:**
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**`config/grafana/dashboards/chimera-dashboard.yml`:**
```yaml
apiVersion: 1

providers:
  - name: 'Chimera Services'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

### 4. Dashboard JSON for Grafana

**`config/grafana/dashboards/service-metrics.json`:**
- Pre-configured dashboard panels
- Service health overview
- CPU/Memory usage per service
- Request rate and latency
- Alert frequency

---

## Data Flow

```
┌──────────────────┐
│  Browser         │
│  (Dashboard)     │
└────────┬─────────┘
         │
         │ 1. Initial HTTP GET /api/services
         ▼
┌──────────────────┐
│  FastAPI         │◄────────────────────────────────────────────┐
│  Backend         │                                             │
└────────┬─────────┘                                             │
         │                                                       │
         │ 2. WebSocket connect to /ws                          │
         ▼                                                       │
┌──────────────────┐                                             │
│  WebSocket       │◄──────┐                                     │
│  Manager         │       │                                     │
└────────┬─────────┘       │                                     │
         │                 │                                     │
         │ 3. Receive updates                                  │
         │    (service status, metrics, alerts)                 │
         │                 │                                     │
         ▼                 │                                     │
┌──────────────────┐       │                                     │
│  UI Update       │       │                                     │
│  (DOM refresh)   │       │                                     │
└──────────────────┘       │                                     │
         │                 │                                     │
         │ 4. User clicks control button                        │
         │                 │                                     │
         ▼                 │                                     │
┌──────────────────┐       │                                     │
│  Control Action  │       │                                     │
│  (via WebSocket) │───────┘                                     │
└────────┬─────────┘                                             │
         │                                                       │
         │ 5. Broadcast to services                             │
         ▼                                                       │
┌───────────────────────────────────────────────────────────────┐
│  Services (OpenClaw, SceneSpeak, Captioning, BSL, etc.)       │
│  • Execute control command                                     │
│  • Update status                                               │
│  • Emit state change event                                     │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │ 6. Publish status update
                            ▼
                     ┌─────────────┐
                     │  Metrics    │
                     │  Collector  │
                     └─────────────┘
```

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend** | HTML5 + Vanilla JS | No build step, fast iteration |
| **Styling** | Tailwind CSS (CDN) | Rapid UI development, modern look |
| **Charts** | Chart.js (CDN) | Lightweight, easy sparklines |
| **WebSocket** | Native WebSocket API | Browser built-in, no dependencies |
| **Backend** | FastAPI (existing) | Already implemented |
| **Metrics** | Prometheus + Grafana | Industry standard |
| **Icons** | Heroicons (SVG inline) | No external font dependency |

---

## API Endpoints Used

### GET /api/services
Returns list of all services with status

### GET /api/services/{service_name}/metrics
Returns metrics for specific service

### GET /api/alerts
Returns active alerts

### POST /api/alerts/{alert_id}/acknowledge
Acknowledges an alert

### POST /api/services/{service_name}/control
Controls service (start/stop/restart)

### WS /ws
WebSocket endpoint for real-time updates

---

## Error Handling

### Connection Failures
- **WebSocket disconnect:** Show banner "Disconnected - Reconnecting...", auto-reconnect with exponential backoff
- **HTTP API errors:** Show toast notification, retry with backoff
- **Service unavailable:** Mark service as "Unknown" status, show "Connection Error" badge

### Data Validation
- **Missing fields:** Use default values, log warning
- **Invalid metrics:** Display "N/A", skip rendering
- **Stale data:** Show "Last update: X seconds ago", warn if > 30s

### User Actions
- **Control failure:** Show error modal, suggest manual intervention
- **Acknowledge failure:** Retry button, contact admin link

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Dashboard loads in Chrome/Firefox/Safari
- [ ] WebSocket connection established
- [ ] Service status displays correctly
- [ ] Alerts appear and can be acknowledged
- [ ] Control buttons work (start/stop/restart)
- [ ] Charts render and update
- [ ] Page responsive on mobile/tablet
- [ ] Reconnection works after disconnect

### Integration Testing
- [ ] Start all services via docker-compose
- [ ] Verify dashboard connects to backend
- [ ] Trigger alert conditions (high CPU, etc.)
- [ ] Verify alert appears in dashboard
- [ ] Control service from dashboard
- [ ] Verify Grafana metrics visible

### Load Testing
- [ ] 10 concurrent dashboard connections
- [ ] WebSocket message rate (100 msg/s)
- [ ] Browser memory usage stable

---

## Files to Create

1. `services/operator-console/static/dashboard.html` - Main dashboard (single file)
2. `config/prometheus.yml` - Prometheus configuration
3. `config/grafana/datasources/prometheus.yml` - Grafana datasource
4. `config/grafana/dashboards/dashboard.yml` - Dashboard provider config
5. `config/grafana/dashboards/service-metrics.json` - Pre-configured dashboard

**Files to Modify:**
1. `services/operator-console/main.py` - Add static file serving, ensure all endpoints work
2. `docker-compose.yml` - Add volume mounts for config files

---

## Definition of Done

- [ ] Dashboard HTML file created with all sections
- [ ] WebSocket integration working (real-time updates)
- [ ] All 8 services visible with health status
- [ ] Alert console functional (view, acknowledge, filter)
- [ ] Control panel working (start/stop/restart)
- [ ] Metrics charts rendering (sparklines)
- [ ] Prometheus config created and mounted
- [ ] Grafana config created and provisioned
- [ ] Docker Compose starts all services successfully
- [ ] End-to-end test: Can view status, see alerts, control services
- [ ] Responsive design works on mobile
- [ ] Documentation updated with screenshots

---

*Design Document - Project Chimera v0.4.0 - March 6, 2026*
