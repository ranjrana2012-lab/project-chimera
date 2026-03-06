# Operator Console

Central monitoring and control dashboard for all Project Chimera services with real-time WebSocket updates.

## Overview

The Operator Console provides human oversight and control:
- Real-time service status monitoring (all 8 services)
- WebSocket-based live metrics streaming
- Alert management with thresholds
- Service control (start/stop/restart)
- Integrated web dashboard at `/static/dashboard.html`
- Prometheus metrics aggregation

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Access to all Chimera services (ports 8000-8006)

# Local development setup
cd services/operator-console
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your service URLs

# Run service
uvicorn main:app --reload --port 8007

# Access dashboard
# Open http://localhost:8007 in browser
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `operator-console` | Service identifier |
| `PORT` | `8007` | HTTP server port |
| `OPENCLAW_ORCHESTRATOR_URL` | `http://localhost:8000` | Orchestrator URL |
| `SCENESPEAK_AGENT_URL` | `http://localhost:8001` | SceneSpeak URL |
| `CAPTIONING_AGENT_URL` | `http://localhost:8002` | Captioning URL |
| `BSL_AGENT_URL` | `http://localhost:8003` | BSL URL |
| `SENTIMENT_AGENT_URL` | `http://localhost:8004` | Sentiment URL |
| `LIGHTING_SOUND_MUSIC_URL` | `http://localhost:8005` | Lighting URL |
| `SAFETY_FILTER_URL` | `http://localhost:8006` | Safety URL |
| `METRICS_POLL_INTERVAL` | `5.0` | Metrics poll interval (seconds) |
| `ALERT_CPU_THRESHOLD` | `80.0` | CPU warning threshold (%) |
| `ALERT_MEMORY_THRESHOLD` | `2000.0` | Memory warning threshold (MB) |
| `ALERT_ERROR_RATE_THRESHOLD` | `0.05` | Error rate warning threshold |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks all services)
- `GET /metrics` - Prometheus metrics

### Dashboard
- `GET /` - Redirect to web dashboard
- `GET /static/dashboard.html` - Web dashboard UI

### Service Status
- `GET /api/services` - List all services with status
- `GET /api/metrics` - Get current metrics from all services

### Alerts
- `GET /api/alerts` - Get all active alerts
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert

### Service Control
- `POST /api/control/{service_name}` - Control service (start/stop/restart)

### WebSocket
- `WS /ws` - Real-time updates WebSocket

**Example: Get service status**
```bash
curl http://localhost:8007/api/services
```

**Example: Control service**
```bash
curl -X POST http://localhost:8007/api/control/scenespeak-agent \
  -H "Content-Type: application/json" \
  -d '{"action": "restart", "reason": "Performance degradation"}'
```

## Dashboard Features

The web dashboard at `http://localhost:8007` provides:

1. **Service Status Panel** - 8 service cards with health indicators
2. **Alerts Console** - Real-time alert feed with acknowledge action
3. **Control Panel** - Start/stop/restart controls for all services
4. **Metrics Charts** - CPU, Memory, Request Rate, Error Rate sparklines
5. **Event Feed** - Scrolling log of system events
6. **WebSocket Connection** - Auto-reconnecting real-time updates

## Development

### Code Structure
```
operator-console/
├── main.py              # FastAPI application
├── metrics_collector.py # Metrics polling from services
├── alert_manager.py     # Alert threshold management
├── websocket_manager.py # WebSocket broadcast handler
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
├── static/             # Web dashboard files
│   ├── dashboard.html  # Dashboard UI
│   └── dashboard.js    # Dashboard JavaScript
└── tests/              # Test suite
```

### Adding Features
1. Add new metrics in `metrics_collector.py`
2. Implement new alert types in `alert_manager.py`
3. Update dashboard UI in `static/dashboard.html`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_websocket.py -v
```

## Troubleshooting

### Services Showing as Down
**Symptom:** Service cards show red/offline status
**Solution:** Check service URLs in `.env`, verify services are running

### WebSocket Not Connecting
**Symptom:** Dashboard shows "Disconnected"
**Solution:** Check browser console, verify `/ws` endpoint accessible

### Alerts Not Firing
**Symptom:** Thresholds exceeded but no alerts
**Solution:** Adjust `ALERT_*_THRESHOLD` values in `.env`, check metrics collection

### Dashboard Not Loading
**Symptom:** 404 on dashboard URL
**Solution:** Verify `static/` directory exists, check Dockerfile COPY command

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
