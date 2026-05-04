# Project Chimera - CPU/GPU Monitoring Dashboard Design

**Date:** 2026-05-03
**Author:** Design session with user approval
**Status:** Approved - Ready for implementation planning

## Overview

This document describes the design for a comprehensive CPU/GPU monitoring dashboard for Project Chimera. The system provides real-time visibility into system resources (CPU, GPU, memory, I/O, network) and correlates them with application-level metrics from Chimera services.

## Use Cases

The monitoring dashboard supports four primary use cases:
1. **Development debugging** - Monitor resource usage during feature development and testing
2. **Production observability** - Track system health for live deployments and performance tuning
3. **Demo/presentation** - Display real-time resource metrics during system demonstrations
4. **Capacity planning** - Analyze usage patterns over time for scaling decisions

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Project Chimera Stack                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   Netdata        │───▶│   Prometheus     │───▶│   Custom         │  │
│  │   (sidecar)      │    │   (metrics)      │    │   Dashboard      │  │
│  │   Port 19999     │    │   Port 9090      │    │   Port 8007      │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│         │                                                                 │
│         │ metrics collection                                              │
│         ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Docker Host (ARM64 DGX)                        │   │
│  │  • CPU cores • GPU memory • Network interfaces • Disk I/O        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Existing Chimera Services (monitored via cgroups):                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ OpenClaw    │ │ SceneSpeak  │ │ Sentiment   │ │ Operator    │       │
│  │ Orchestrator│ │ Agent       │ │ Agent       │ │ Console     │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
└───────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Netdata runs as a sidecar container** with host access (`pid: host`, `network: host`)
- **Prometheus scrapes Netdata** metrics endpoint every 5 seconds
- **Custom dashboard built into operator-console** fetches from both Prometheus and existing health aggregator
- **Single pane of glass** for both application and infrastructure metrics

## Components

### 1. Netdata Sidecar Container

**Location:** `services/netdata/` (new service)

**Purpose:** High-frequency metrics collection (1s intervals) from host and containers

**Capabilities:**
- **CPU:** Per-core usage, load averages, context switches
- **GPU:** NVIDIA GPU utilization, VRAM usage, temperature, power via `nvidia-smi`
- **Memory:** RAM, swap, per-container memory cgroup stats
- **Disk:** I/O throughput, per-filesystem usage
- **Network:** Interface traffic, connection counts
- **Docker:** Container CPU, memory, network stats via cgroups

**Exposure:** Prometheus exporter on port `19999` at `/api/v1/prometheus.metrics`

### 2. Prometheus Metrics Store

**Location:** New service in `docker-compose` files

**Purpose:** Time-series database storing all metrics for querying and dashboard

**Configuration:**
- Scrape Netdata every 5 seconds
- Retention: 15 days of data
- Storage: `prometheus-data` volume
- Query API: `http://prometheus:9090/api/v1/query`

### 3. Enhanced Dashboard Service

**Location:** Extend `services/dashboard/main.py`

**Purpose:** Unified dashboard combining system metrics from Prometheus + app metrics from health aggregator

**New Endpoints:**
- `GET /api/metrics/summary` - Combined system + app metrics
- `GET /api/metrics/cpu` - CPU utilization data
- `GET /api/metrics/gpu` - GPU utilization data
- `GET /api/metrics/memory` - Memory usage data
- `GET /api/metrics/containers` - Per-container stats
- `GET /api/metrics/history?span=1h` - Time series data

### 4. Frontend Dashboard

**Location:** Extend `services/operator-console/static/dashboard.html`

**Features:**
- Real-time metric cards (current CPU, GPU, memory)
- Time-series charts using Chart.js or Plotly
- Container resource breakdown table
- Correlated view: app health + system resources
- Dark mode support (matching existing Chimera UI)

## Data Flow

```
Host System (DGX ARM64)
    │
    │ • CPU stats (1s interval)
    │ • GPU stats (nvidia-smi)
    │ • Memory stats
    │ • Disk I/O
    │ • Network interfaces
    │ • Docker cgroups
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Netdata Container (host PID mode)                           │
│ │ Collects → Aggregates → Exposes                           │
│ ▼                                                           │
│ /api/v1/prometheus.metrics (text format)                    │
└─────────────────────────────────────────────────────────────┘
    │
    │ Scraped every 5s
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Prometheus Container                                         │
│ │ Stores → Indexes → Queries                                │
│ ▼                                                           │
│ prometheus-data volume                                      │
└─────────────────────────────────────────────────────────────┘
    │
    │ HTTP query (dashboard polls every 3-5s)
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Dashboard Backend (FastAPI)                                 │
│ │                                                            │
│ ├─ PrometheusClient → System metrics                       │
│ └─ HealthAggregatorClient → App service health             │
│ │                                                            │
│ ▼                                                           │
│ /api/metrics/* endpoints (JSON)                             │
└─────────────────────────────────────────────────────────────┘
    │
    │ HTTP poll every 3-5s
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend Dashboard (Browser)                                │
│ │                                                            │
│ ├─ Chart.js/Plotly → Time series charts                    │
│ ├─ Auto-refresh → 5s interval                              │
│ └─ WebSocket (optional) → Real-time alerts                  │
└─────────────────────────────────────────────────────────────┘
```

### Update Intervals

- **Netdata:** 1 second collection (native)
- **Prometheus:** 5 second scrape from Netdata
- **Dashboard poll:** 3-5 second queries to Prometheus
- **Frontend refresh:** 5 second auto-refresh of charts

## Integration Points

### Docker Compose Integration

**Add to `docker-compose.mvp.yml`:**

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: chimera-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'
    networks:
      - chimera-backend
    restart: unless-stopped

  netdata:
    image: netdata/netdata:stable
    container_name: chimera-netdata
    ports:
      - "19999:19999"
    cap_add:
      - SYS_PTRACE
    security_opt:
      - apparmor:unconfined
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - NETDATA_LISTENER_PORT=19999
    networks:
      - chimera-backend
    restart: unless-stopped
```

**Add to `docker-compose.dgx-spark.yml`:**
- Override Netdata with NVIDIA GPU monitoring enabled
- Add `NETDATA_LIBCAP_ENABLE=1` for GPU stats
- Mount `/dev/nvidia0` for GPU access

### Dashboard Backend Integration

**Extend `services/dashboard/main.py`:**

```python
from prometheus_api_client import PrometheusConnect
import httpx

prometheus = PrometheusConnect(url="http://prometheus:9090")

@app.get("/api/metrics/summary")
async def metrics_summary():
    """Combined system + app metrics."""
    cpu_usage = query_prometheus("system.cpu.total_pct")
    gpu_usage = query_prometheus("nvidia_gpu_utilization")
    mem_usage = query_prometheus("system.memory.used_pct")
    app_health = await get_service_health()

    return {
        "system": {"cpu": cpu_usage, "gpu": gpu_usage, "memory": mem_usage},
        "applications": app_health,
        "timestamp": datetime.now().isoformat()
    }
```

### Frontend Integration

**New files in `services/operator-console/static/`:**
- `monitoring-dashboard.html` - System metrics dashboard
- `monitoring-dashboard.js` - Chart rendering, data fetch
- `monitoring-dashboard.css` - Styling

### Environment Variables

**New `.env.monitoring` file:**

```bash
# Monitoring
PROMETHEUS_RETENTION_DAYS=15
NETDATA_UPDATE_INTERVAL=1
METRICS_QUERY_TIMEOUT=30s
DASHBOARD_REFRESH_INTERVAL=5s
```

## Technical Details

### Error Handling & Resilience

**Dashboard backend:**
- Graceful degradation if Prometheus/Netdata unavailable
- Return cached metrics with `stale: true` flag on query timeout
- Circuit breaker pattern: skip unhealthy backends after 3 consecutive failures

**Frontend:**
- Handle missing data points in charts (show gaps)
- Display connection status indicator
- Auto-retry with exponential backoff on fetch failure

### Performance Considerations

**Prometheus query optimization:**
- Use recording rules for expensive aggregations
- Pre-compute per-minute averages for dashboard queries
- Limit query range to 1 hour for initial page load

**Frontend optimization:**
- Lazy load charts (viewport intersection)
- Downsample data points for long time ranges (>1 hour)
- Use Web Workers for heavy chart rendering

**Resource limits:**

```yaml
prometheus:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2'
```

### Security

**Access control:**
- Dashboard endpoints inherit existing FastAPI auth
- Prometheus restricted to internal network (no external exposure)
- Netdata: disable alarm streaming, set read-only mode

**CORS configuration:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8007", "http://127.0.0.1:8007"],
    allow_methods=["GET"],
)
```

### Testing Strategy

**Unit tests:**
```python
# tests/unit/test_monitoring_backend.py
test_metrics_summary_returns_combined_data()
test_prometheus_timeout_returns_cached()
test_gpu_metrics_uses_nvidia_query()
```

**Integration tests:**
```python
# tests/integration/test_monitoring_e2e.py
test_netdata_exposes_prometheus_endpoint()
test_prometheus_scrapes_netdata()
test_dashboard_fetches_from_prometheus()
test_gpu_metrics_available_on_dgx()
```

**E2E with Playwright:**
- Navigate to monitoring dashboard
- Verify charts load without console errors
- Submit test load and verify CPU spike visible

## File Structure

```
Project Chimera (Monitoring additions)
│
├── config/prometheus/
│   └── prometheus.yml           # Prometheus config (scrape targets)
│
├── services/netdata/
│   └── Dockerfile               # Netdata container definition
│
├── services/dashboard/
│   ├── main.py                  # EXTEND: Add metrics endpoints
│   ├── requirements.txt         # ADD: prometheus-api-client
│   └── static/
│       └── monitoring-dashboard.html  # NEW: System metrics UI
│
├── docker-compose.mvp.yml       # ADD: prometheus, netdata services
├── docker-compose.dgx-spark.yml # OVERRIDE: netdata GPU monitoring
└── docker-compose.student.yml   # OPTIONAL: lightweight monitoring

tests/
├── unit/
│   └── test_monitoring_backend.py    # NEW
└── integration/
    └── test_monitoring_e2e.py        # NEW

scripts/
└── setup-monitoring.sh               # NEW: One-click monitoring setup
```

## Implementation Phases

1. **Phase 1:** Add Netdata + Prometheus to Docker Compose, verify metrics flow
2. **Phase 2:** Extend dashboard backend with `/api/metrics/*` endpoints
3. **Phase 3:** Build frontend dashboard with real-time charts
4. **Phase 4:** Add DGX-specific GPU metrics, tests, and documentation

## Success Criteria

The monitoring system is complete when:
- ✅ All resource metrics visible (CPU, GPU, memory, I/O, network)
- ✅ Dashboard updates every 3-5 seconds
- ✅ GPU metrics available on DGX systems
- ✅ Container-level resource correlation
- ✅ Historical data available for capacity planning
- ✅ All tests pass (unit, integration, E2E)
- ✅ Documentation updated
