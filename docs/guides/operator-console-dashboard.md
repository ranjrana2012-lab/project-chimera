# Operator Console Dashboard Guide

**Version:** v0.5.0
**Last Updated:** March 6, 2026

---

## Dashboard Overview

The Operator Console Dashboard is a single-page web application that provides real-time monitoring and control of all Project Chimera services. Accessible at `http://localhost:8007`, the dashboard offers:

- Live service status monitoring
- Real-time metrics visualization
- Alert management and acknowledgment
- Service control capabilities
- WebSocket-based auto-updating UI

---

## Accessing the Dashboard

### Local Development

1. Start the operator-console service:
   ```bash
   cd services/operator-console
   uvicorn main:app --reload --port 8007
   ```

2. Open your browser to: `http://localhost:8007`

### Docker Deployment

1. Ensure operator-console container is running:
   ```bash
   docker ps | grep operator-console
   ```

2. Access dashboard at: `http://localhost:8007`

### Authentication

Currently, no authentication is required (development mode). Production deployments should implement authentication via reverse proxy.

---

## Dashboard Sections

### 1. Header Section

The top header displays:
- **Project Chimera** branding
- **Operator Console** title
- **Connection Status** indicator:
  - 🟢 Green: Connected (receiving real-time updates)
  - 🔴 Red: Disconnected (will auto-reconnect)
- **Current Time** (updates every second)

### 2. Service Status Panel

Displays 8 service cards (one per Chimera service):

**Services Monitored:**
- OpenClaw Orchestrator (port 8000)
- SceneSpeak Agent (port 8001)
- Captioning Agent (port 8002)
- BSL Agent (port 8003)
- Sentiment Agent (port 8004)
- Lighting-Sound-Music (port 8005)
- Safety Filter (port 8006)
- Operator Console (port 8007)

**Each Card Shows:**
- Service name with icon
- Health status indicator:
  - 🟢 **Online**: Service responding and healthy
  - 🟡 **Degraded**: Service up but performance issues detected
  - 🔴 **Offline**: Service not responding
- Current metrics (CPU %, Memory MB)
- Last update timestamp
- Quick action buttons (Logs, Restart)

### 3. Alerts Console

Displays active alerts requiring attention:

**Alert Severity Levels:**
- 🔴 **Critical**: Service down or critical failure - Immediate action required
- 🟡 **Warning**: Degraded performance or concerning metric - Monitor closely
- 🔵 **Info**: Informational event - No action required

**Alert Card Shows:**
- Severity color-coding (left border)
- Alert title and message
- Source service
- Timestamp
- Acknowledge button (click to dismiss)

**Alert Actions:**
- Click **Acknowledge** to dismiss alert
- Filter by severity using the filter controls
- Auto-refreshes via WebSocket

### 4. Control Panel

Provides bulk service control actions:

**Control Buttons:**
- **Start All Services** - Start all stopped services
- **Stop All Services** - Stop all running services
- **Restart Degraded** - Restart only degraded services
- **Refresh Status** - Force immediate status refresh

**Confirmation Dialog:**
- Control actions require confirmation
- Dialog shows action and affected services
- Click **Confirm** to execute, **Cancel** to abort

### 5. Metrics Charts

Four real-time sparkline charts display system metrics:

**Chart Types:**
1. **CPU Usage (%)** - CPU percentage across all services
2. **Memory Usage (MB)** - Memory consumption in megabytes
3. **Request Rate (req/s)** - Requests per second per service
4. **Error Rate (%)** - Error rate percentage

**Chart Features:**
- Live updates via WebSocket (every 5 seconds)
- Scroll back shows last 5 minutes of data
- Hover for exact values at data points
- Color-coded lines per service

### 6. Event Feed

Scrolling log of system events at the bottom of the dashboard:

**Event Types:**
- Service status changes (up/down/degraded)
- Alerts triggered/acknowledged
- Control actions executed
- Threshold violations

**Event Display:**
- Timestamp (HH:MM:SS format)
- Event message
- Color-coded by type (green=info, yellow=warning, red=error)

**Feed Controls:**
- Auto-scroll toggle (default: on)
- Export to clipboard button
- Max 100 events displayed (older events auto-removed)

---

## WebSocket Connection

### Connection Behavior

The dashboard uses WebSocket (`/ws` endpoint) for real-time updates:

**Connection Flow:**
1. Dashboard opens WebSocket connection on load
2. Sends subscription message for all channels
3. Receives continuous updates for:
   - Service status changes
   - Metrics updates
   - New alerts
   - Control action results

**Auto-Reconnect:**
- If connection drops, dashboard automatically reconnects
- Exponential backoff: 1s, 2s, 4s, 8s, 15s (max)
- Connection status indicator shows current state

**WebSocket Message Types:**
```javascript
// Metric update
{
  "type": "metric",
  "service": "scenespeak-agent",
  "metric": "cpu_percent",
  "value": 45.2
}

// Alert update
{
  "type": "alert",
  "id": "alert_abc123",
  "severity": "warning",
  "title": "High CPU Usage",
  "message": "CPU exceeded 80%"
}

// Status update
{
  "type": "status",
  "service": "sentiment-agent",
  "status": "degraded"
}
```

---

## Troubleshooting

### Dashboard Won't Load

**Problem:** Browser shows "Unable to connect" or 404 error

**Solutions:**
1. Verify operator-console service is running:
   ```bash
   curl http://localhost:8007/health/live
   ```
2. Check static files exist:
   ```bash
   ls -la services/operator-console/static/
   ```
3. Verify port 8007 is not in use by another service
4. Check browser console for JavaScript errors

### Services Showing as Offline

**Problem:** All service cards show red/offline status

**Solutions:**
1. Verify services are running:
   ```bash
   docker ps | grep -E "8000|8001|8002|8003|8004|8005|8006"
   ```
2. Check `.env` file has correct service URLs
3. Test individual service health:
   ```bash
   curl http://localhost:8000/health/live
   curl http://localhost:8001/health/live
   # ... etc
   ```

### WebSocket Not Connecting

**Problem:** Connection status shows "Disconnected"

**Solutions:**
1. Check browser console for WebSocket errors
2. Verify WebSocket endpoint is accessible:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8007/ws
   ```
3. Check firewall/proxy settings (may block WebSocket)
4. Try accessing dashboard from different browser

### Metrics Not Updating

**Problem:** Charts show stale data, no new values

**Solutions:**
1. Check metrics poll interval in `.env` (`METRICS_POLL_INTERVAL`)
2. Verify services are exposing `/metrics` endpoints
3. Check browser console for WebSocket messages
4. Force refresh using **Refresh Status** button

### Alerts Not Firing

**Problem:** Metrics exceed thresholds but no alerts appear

**Solutions:**
1. Verify alert thresholds in `.env`:
   - `ALERT_CPU_THRESHOLD`
   - `ALERT_MEMORY_THRESHOLD`
   - `ALERT_ERROR_RATE_THRESHOLD`
2. Check alert manager is initialized (see logs)
3. Test alert manually by triggering threshold condition

---

## Advanced Usage

### Custom Alert Thresholds

Edit `.env` file to adjust alert thresholds:

```bash
# CPU threshold (percentage)
ALERT_CPU_THRESHOLD=80.0

# Memory threshold (megabytes)
ALERT_MEMORY_THRESHOLD=2000.0

# Error rate threshold (0.0-1.0)
ALERT_ERROR_RATE_THRESHOLD=0.05
```

### Polling Interval Adjustment

Adjust how often metrics are collected:

```bash
# Collect metrics every 5 seconds (default)
METRICS_POLL_INTERVAL=5.0

# Collect metrics every 10 seconds (lower CPU usage)
METRICS_POLL_INTERVAL=10.0
```

### Exporting Dashboard State

Use browser DevTools to export current dashboard state:

```javascript
// In browser console
copy(JSON.stringify(window.dashboardState, null, 2))
```

---

## Related Documentation

- [Operator Console API Reference](../api/operator-console.md)
- [Monitoring Runbook](../runbooks/monitoring.md)
- [Incident Response Guide](../runbooks/incident-response.md)

---

*Dashboard Guide - Project Chimera v0.5.0 - March 6, 2026*
