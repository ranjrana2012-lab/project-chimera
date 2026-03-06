# Operator Console Completion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Complete Operator Console with single integrated dashboard, monitoring configs, and Docker Compose integration

**Architecture:** Single-page HTML dashboard with embedded CSS/JS, WebSocket real-time updates, Prometheus/Grafana observability stack

**Tech Stack:** HTML5, Vanilla JS, Tailwind CSS (CDN), Chart.js (CDN), FastAPI (existing), Prometheus, Grafana

---

## Task 1: Create Prometheus Configuration

**Files:**
- Create: `config/prometheus.yml`

**Step 1: Create config directory**

```bash
mkdir -p config
```

**Step 2: Create prometheus.yml**

```bash
cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

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
    metrics_path: '/metrics'
EOF
```

**Step 3: Verify file created**

```bash
cat config/prometheus.yml
```

Expected: Prometheus configuration with 8 service targets

---

## Task 2: Create Grafana Datasource Configuration

**Files:**
- Create: `config/grafana/datasources/prometheus.yml`

**Step 1: Create Grafana directories**

```bash
mkdir -p config/grafana/datasources
mkdir -p config/grafana/dashboards
```

**Step 2: Create datasource config**

```bash
cat > config/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
```

**Step 3: Verify file created**

```bash
cat config/grafana/datasources/prometheus.yml
```

Expected: Grafana datasource configuration

---

## Task 3: Create Grafana Dashboard Provider

**Files:**
- Create: `config/grafana/dashboards/dashboard.yml`

**Step 1: Create provider config**

```bash
cat > config/grafana/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Chimera Services'
    orgId: 1
    folder: 'Chimera'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
EOF
```

**Step 2: Verify file created**

```bash
cat config/grafana/dashboards/dashboard.yml
```

Expected: Dashboard provider configuration

---

## Task 4: Create Grafana Service Metrics Dashboard

**Files:**
- Create: `config/grafana/dashboards/service-metrics.json`

**Step 1: Create dashboard JSON**

```bash
cat > config/grafana/dashboards/service-metrics.json << 'EOF'
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          }
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "targets": [
        {
          "expr": "up{job=\"chimera-services\"}",
          "legendFormat": "{{instance}}"
        }
      ],
      "title": "Service Health Status",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{instance}}"
        }
      ],
      "title": "Request Rate",
      "type": "graph"
    }
  ],
  "schemaVersion": 27,
  "style": "dark",
  "tags": ["chimera"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Project Chimera Service Metrics",
  "uid": "chimera-metrics",
  "version": 1
}
EOF
```

**Step 2: Verify file created**

```bash
cat config/grafana/dashboards/service-metrics.json | jq .
```

Expected: Valid JSON dashboard configuration

---

## Task 5: Create Static Directory for Dashboard

**Files:**
- Create: `services/operator-console/static/`

**Step 1: Create static directory**

```bash
mkdir -p services/operator-console/static
```

**Step 2: Verify directory created**

```bash
ls -la services/operator-console/ | grep static
```

Expected: static directory exists

---

## Task 6: Create Dashboard HTML Structure

**Files:**
- Create: `services/operator-console/static/dashboard.html`

**Step 1: Create HTML skeleton**

```bash
cat > services/operator-console/static/dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Chimera - Operator Console</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-900 text-white">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div class="flex items-center justify-between">
            <h1 class="text-2xl font-bold">Project Chimera Operator Console</h1>
            <div id="connection-status" class="flex items-center gap-2">
                <span class="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></span>
                <span id="status-text">Connecting...</span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="p-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Service Status Panel -->
            <section class="bg-gray-800 rounded-lg p-4">
                <h2 class="text-xl font-semibold mb-4">Service Status</h2>
                <div id="service-list" class="space-y-3">
                    <!-- Service cards will be injected here -->
                </div>
            </section>

            <!-- Alerts Console -->
            <section class="bg-gray-800 rounded-lg p-4">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-xl font-semibold">Alerts</h2>
                    <select id="alert-filter" class="bg-gray-700 rounded px-3 py-1">
                        <option value="all">All</option>
                        <option value="critical">Critical</option>
                        <option value="warning">Warning</option>
                        <option value="info">Info</option>
                    </select>
                </div>
                <div id="alert-list" class="space-y-2 max-h-96 overflow-y-auto">
                    <!-- Alerts will be injected here -->
                </div>
            </section>

            <!-- Control Panel -->
            <section class="bg-gray-800 rounded-lg p-4">
                <h2 class="text-xl font-semibold mb-4">Control Panel</h2>
                <div id="control-list" class="space-y-2">
                    <!-- Control buttons will be injected here -->
                </div>
                <div class="mt-4 pt-4 border-t border-gray-700">
                    <button id="start-all" class="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded mb-2">Start All</button>
                    <button id="stop-all" class="w-full bg-red-600 hover:bg-red-700 px-4 py-2 rounded">Stop All</button>
                </div>
            </section>
        </div>

        <!-- Metrics Section -->
        <section class="mt-6 bg-gray-800 rounded-lg p-4">
            <h2 class="text-xl font-semibold mb-4">Metrics (Last 5 Minutes)</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <h3 class="text-sm text-gray-400 mb-2">CPU %</h3>
                    <canvas id="cpu-chart" height="100"></canvas>
                </div>
                <div>
                    <h3 class="text-sm text-gray-400 mb-2">Memory MB</h3>
                    <canvas id="memory-chart" height="100"></canvas>
                </div>
                <div>
                    <h3 class="text-sm text-gray-400 mb-2">Requests/sec</h3>
                    <canvas id="requests-chart" height="100"></canvas>
                </div>
            </div>
        </section>

        <!-- Event Feed -->
        <section class="mt-6 bg-gray-800 rounded-lg p-4">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold">Event Feed</h2>
                <button id="export-events" class="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm">Export</button>
            </div>
            <div id="event-feed" class="h-48 overflow-y-auto font-mono text-sm bg-gray-900 rounded p-3">
                <!-- Events will be injected here -->
            </div>
        </section>
    </main>

    <script src="/static/dashboard.js"></script>
</body>
</html>
EOF
```

**Step 2: Verify file created**

```bash
wc -l services/operator-console/static/dashboard.html
```

Expected: ~90 lines

---

## Task 7: Create Dashboard JavaScript

**Files:**
- Create: `services/operator-console/static/dashboard.js`

**Step 1: Create JavaScript file**

```bash
cat > services/operator-console/static/dashboard.js << 'EOF'
// WebSocket connection
let ws = null;
let reconnectTimer = null;
const wsUrl = `ws://${window.location.host}/ws`;

// Chart instances
let cpuChart = null;
let memoryChart = null;
let requestsChart = null;

// Service data
let services = {};
let alerts = [];
let metricsHistory = { cpu: [], memory: [], requests: [] };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    initializeCharts();
    setupEventListeners();
    fetchInitialData();
});

// WebSocket connection
function connectWebSocket() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateConnectionStatus('connected');
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        updateConnectionStatus('disconnected');
        scheduleReconnect();
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('error');
    };
}

function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, 5000);
}

function updateConnectionStatus(status) {
    const statusEl = document.getElementById('connection-status');
    const textEl = document.getElementById('status-text');
    const dotEl = statusEl.querySelector('span:first-child');

    switch (status) {
        case 'connected':
            dotEl.className = 'w-3 h-3 bg-green-500 rounded-full';
            textEl.textContent = 'Connected';
            break;
        case 'disconnected':
            dotEl.className = 'w-3 h-3 bg-yellow-500 rounded-full animate-pulse';
            textEl.textContent = 'Reconnecting...';
            break;
        case 'error':
            dotEl.className = 'w-3 h-3 bg-red-500 rounded-full';
            textEl.textContent = 'Connection Error';
            break;
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'service_update':
            updateService(data.service);
            break;
        case 'alert':
            addAlert(data.alert);
            break;
        case 'metrics':
            updateMetrics(data.metrics);
            break;
        case 'event':
            addEvent(data.event);
            break;
    }
}

// Fetch initial data
async function fetchInitialData() {
    try {
        // Fetch services
        const servicesRes = await fetch('/api/services');
        const servicesData = await servicesRes.json();
        servicesData.services.forEach(s => services[s.name] = s);
        renderServices();

        // Fetch alerts
        const alertsRes = await fetch('/api/alerts');
        const alertsData = await alertsRes.json();
        alerts = alertsData.alerts || [];
        renderAlerts();

        // Fetch initial metrics
        fetchMetrics();
    } catch (error) {
        console.error('Failed to fetch initial data:', error);
        addEvent({ message: `Error loading initial data: ${error.message}`, type: 'error' });
    }
}

// Fetch metrics
async function fetchMetrics() {
    try {
        const res = await fetch('/api/metrics/summary');
        const data = await res.json();
        updateMetrics(data);
    } catch (error) {
        console.error('Failed to fetch metrics:', error);
    }
}

// Update metrics
function updateMetrics(data) {
    // Add to history (keep last 60 data points)
    const timestamp = new Date().toLocaleTimeString();
    metricsHistory.cpu.push({ x: timestamp, y: data.cpu || 0 });
    metricsHistory.memory.push({ x: timestamp, y: data.memory || 0 });
    metricsHistory.requests.push({ x: timestamp, y: data.requests || 0 });

    if (metricsHistory.cpu.length > 60) {
        metricsHistory.cpu.shift();
        metricsHistory.memory.shift();
        metricsHistory.requests.shift();
    }

    updateCharts();
}

// Initialize charts
function initializeCharts() {
    const chartConfig = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { beginAtZero: true, grid: { color: 'rgb(55, 65, 81)' } }
            }
        }
    };

    cpuChart = new Chart(document.getElementById('cpu-chart'), chartConfig);
    memoryChart = new Chart(document.getElementById('memory-chart'), { ...chartConfig });
    requestsChart = new Chart(document.getElementById('requests-chart'), { ...chartConfig });
}

// Update charts
function updateCharts() {
    const updateChart = (chart, data) => {
        chart.data.labels = data.map(d => d.x);
        chart.data.datasets[0].data = data.map(d => d.y);
        chart.update('none');
    };

    updateChart(cpuChart, metricsHistory.cpu);
    updateChart(memoryChart, metricsHistory.memory);
    updateChart(requestsChart, metricsHistory.requests);
}

// Render services
function renderServices() {
    const container = document.getElementById('service-list');
    container.innerHTML = Object.values(services).map(service => `
        <div class="bg-gray-700 rounded p-3">
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="font-semibold">${service.name}</h3>
                    <p class="text-sm text-gray-400">Port: ${service.port}</p>
                </div>
                <span class="w-3 h-3 rounded-full ${getStatusColor(service.health)}"></span>
            </div>
            ${service.metrics ? `
                <div class="mt-2 text-sm text-gray-400">
                    CPU: ${service.metrics.cpu_percent?.toFixed(1) || 'N/A'}% |
                    Memory: ${service.metrics.memory_mb?.toFixed(0) || 'N/A'} MB
                </div>
            ` : ''}
        </div>
    `).join('');
}

function getStatusColor(health) {
    switch (health) {
        case 'healthy': return 'bg-green-500';
        case 'degraded': return 'bg-yellow-500';
        case 'unhealthy': return 'bg-red-500';
        default: return 'bg-gray-500';
    }
}

// Update service
function updateService(service) {
    services[service.name] = service;
    renderServices();
}

// Render alerts
function renderAlerts() {
    const filter = document.getElementById('alert-filter').value;
    const filtered = filter === 'all' ? alerts : alerts.filter(a => a.severity === filter);

    const container = document.getElementById('alert-list');
    container.innerHTML = filtered.map(alert => `
        <div class="bg-gray-700 rounded p-3 border-l-4 ${getAlertBorderColor(alert.severity)}">
            <div class="flex items-center justify-between">
                <div>
                    <h4 class="font-semibold">${alert.title}</h4>
                    <p class="text-sm text-gray-400">${alert.message}</p>
                    <p class="text-xs text-gray-500">${new Date(alert.timestamp).toLocaleString()}</p>
                </div>
                ${!alert.acknowledged ? `
                    <button onclick="acknowledgeAlert('${alert.id}')" class="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-sm">Ack</button>
                ` : '<span class="text-green-500 text-sm">✓ Acknowledged</span>'}
            </div>
        </div>
    `).join('');
}

function getAlertBorderColor(severity) {
    switch (severity) {
        case 'critical': return 'border-red-500';
        case 'warning': return 'border-yellow-500';
        case 'info': return 'border-blue-500';
        default: return 'border-gray-500';
    }
}

// Add alert
function addAlert(alert) {
    alerts.unshift(alert);
    if (alerts.length > 100) alerts.pop();
    renderAlerts();
    addEvent({ message: `Alert: ${alert.title} - ${alert.message}`, type: 'alert' });
}

// Acknowledge alert
async function acknowledgeAlert(alertId) {
    try {
        await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
        const alert = alerts.find(a => a.id === alertId);
        if (alert) alert.acknowledged = true;
        renderAlerts();
    } catch (error) {
        console.error('Failed to acknowledge alert:', error);
    }
}

// Render controls
function renderControls() {
    const container = document.getElementById('control-list');
    container.innerHTML = Object.values(services).map(service => `
        <div class="flex items-center justify-between bg-gray-700 rounded p-2">
            <span class="text-sm">${service.name}</span>
            <div class="flex gap-2">
                <button onclick="controlService('${service.name}', 'start')" class="bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-xs">Start</button>
                <button onclick="controlService('${service.name}', 'stop')" class="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs">Stop</button>
                <button onclick="controlService('${service.name}', 'restart')" class="bg-yellow-600 hover:bg-yellow-700 px-2 py-1 rounded text-xs">Restart</button>
            </div>
        </div>
    `).join('');
}

// Control service
async function controlService(serviceName, action) {
    try {
        const res = await fetch(`/api/services/${serviceName}/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const result = await res.json();
        addEvent({ message: `${serviceName}: ${action} - ${result.status}`, type: 'info' });
    } catch (error) {
        console.error('Failed to control service:', error);
        addEvent({ message: `Error controlling ${serviceName}: ${error.message}`, type: 'error' });
    }
}

// Add event
function addEvent(event) {
    const container = document.getElementById('event-feed');
    const timestamp = new Date().toLocaleTimeString();
    const color = event.type === 'error' ? 'text-red-400' : event.type === 'alert' ? 'text-yellow-400' : 'text-gray-300';
    container.innerHTML += `<div class="${color}">[${timestamp}] ${event.message}</div>`;
    container.scrollTop = container.scrollHeight;
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('alert-filter').addEventListener('change', renderAlerts);
    document.getElementById('start-all').addEventListener('click', () => controlAllServices('start'));
    document.getElementById('stop-all').addEventListener('click', () => controlAllServices('stop'));
    document.getElementById('export-events').addEventListener('click', exportEvents);

    // Initial render
    renderControls();
}

// Control all services
async function controlAllServices(action) {
    for (const service of Object.values(services)) {
        await controlService(service.name, action);
    }
}

// Export events
function exportEvents() {
    const container = document.getElementById('event-feed');
    navigator.clipboard.writeText(container.innerText);
    addEvent({ message: 'Events exported to clipboard', type: 'info' });
}

// Fetch metrics periodically
setInterval(fetchMetrics, 5000);
EOF
```

**Step 2: Verify file created**

```bash
wc -l services/operator-console/static/dashboard.js
```

Expected: ~280 lines

---

## Task 8: Update Operator Console main.py

**Files:**
- Modify: `services/operator-console/main.py`

**Step 1: Read current main.py**

```bash
head -20 services/operator-console/main.py
```

**Step 2: Add static file mounting**

Add to FastAPI app initialization (around line 60-70):

```python
from fastapi.staticfiles import StaticFiles

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Step 3: Add dashboard redirect**

Add root endpoint:

```python
@app.get("/")
async def dashboard_redirect():
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/dashboard.html")
```

**Step 4: Verify changes**

```bash
grep -n "StaticFiles\|dashboard_redirect" services/operator-console/main.py
```

Expected: Static mount and redirect present

---

## Task 9: Update Docker Compose Volume Mounts

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Add config volume mounts**

Edit the prometheus service section:

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: chimera-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
```

**Step 2: Add grafana volume mounts**

Edit the grafana service section:

```yaml
  grafana:
    image: grafana/grafana:latest
    container_name: chimera-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=chimera
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
```

**Step 3: Verify changes**

```bash
grep -A 5 "volumes:" docker-compose.yml | head -20
```

Expected: Config file mounts present

---

## Task 10: Build and Start Services

**Step 1: Build all containers**

```bash
docker-compose build
```

Expected: All services build successfully

**Step 2: Start services**

```bash
docker-compose up -d
```

Expected: All services started

**Step 3: Check service status**

```bash
docker-compose ps
```

Expected: All 13 services running/healthy

---

## Task 11: Verify Dashboard Connectivity

**Step 1: Check operator console is running**

```bash
docker-compose logs operator-console | tail -20
```

Expected: Service started, no errors

**Step 2: Test HTTP endpoint**

```bash
curl -s http://localhost:8007/ | head -20
```

Expected: HTML response (redirect to dashboard)

**Step 3: Test dashboard HTML**

```bash
curl -s http://localhost:8007/static/dashboard.html | grep "Project Chimera"
```

Expected: Dashboard HTML returned

**Step 4: Test API endpoints**

```bash
curl -s http://localhost:8007/api/services | jq .
```

Expected: JSON with services array

---

## Task 12: Verify Grafana Dashboard

**Step 1: Check Grafana is running**

```bash
curl -s http://localhost:3000/api/health | jq .
```

Expected: {"database":"ok"}

**Step 2: Login to Grafana**

```bash
curl -s -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"chimera"}' | jq .
```

Expected: Successful login response

**Step 3: Verify datasource**

```bash
curl -s http://admin:chimera@localhost:3000/api/datasources | jq '.[] | .name'
```

Expected: "Prometheus" datasource present

---

## Task 13: End-to-End Test

**Step 1: Open dashboard in browser**

Navigate to: http://localhost:8007

**Step 2: Verify WebSocket connection**

Check browser console for: "WebSocket connected"

**Step 3: Verify service status**

Check that all 8 services show health status

**Step 4: Test alert acknowledgment**

1. Trigger an alert (e.g., high CPU)
2. Verify alert appears in console
3. Click Acknowledge button
4. Verify alert marked acknowledged

**Step 5: Test service control**

1. Click Stop on a service
2. Verify service stops
3. Click Start on same service
4. Verify service starts

**Step 6: Verify metrics charts**

Check that CPU/Memory/Requests charts display

---

## Task 14: Commit and Push

**Step 1: Check git status**

```bash
git status
```

**Step 2: Add all files**

```bash
git add config/ services/operator-console/ docker-compose.yml
```

**Step 3: Commit**

```bash
git commit -m "feat: complete Operator Console with integrated dashboard

- Add single-page HTML dashboard with real-time WebSocket updates
- Create Prometheus configuration for metrics scraping
- Create Grafana datasource and dashboard provisioning
- Implement service status, alerts, and control panels
- Add metrics visualization with Chart.js sparklines
- Configure Docker Compose volume mounts for configs
- Full end-to-end testing completed"
```

**Step 4: Push to GitHub**

```bash
git push origin main
```

Expected: Push successful

---

## Definition of Done

- [ ] Prometheus config created and mounted
- [ ] Grafana configs created and provisioned
- [ ] Dashboard HTML with all sections
- [ ] Dashboard JavaScript with WebSocket
- [ ] Static file serving configured
- [ ] Docker Compose builds and starts all services
- [ ] Dashboard accessible at localhost:8007
- [ ] WebSocket connection works
- [ ] All 8 services visible with status
- [ ] Alerts display and can be acknowledged
- [ ] Service controls work (start/stop/restart)
- [ ] Metrics charts render
- [ ] Grafana accessible at localhost:3000
- [ ] All changes committed and pushed

---

*Implementation Plan - Project Chimera v0.4.0 - March 6, 2026*
