# Project Chimera Service Status Reference

This document describes the expected states of all Project Chimera services for a healthy demo environment.

## Service Overview

### Core AI Services

| Service | Port | Health Endpoint | Expected Status | Dependencies |
|---------|------|-----------------|-----------------|--------------|
| OpenClaw Orchestrator | 8000 | `/health/live` | HTTP 200 | NATS, SceneSpeak |
| SceneSpeak | 8001 | `/health/live` | HTTP 200 | NATS |
| Captioning Service | 8002 | `/health/live` | HTTP 200 | NATS |
| BSL Agent | 8003 | `/health/live` | HTTP 200 | NATS |
| Sentiment Analysis | 8004 | `/health/live` | HTTP 200 | NATS |
| LSM Service | 8005 | `/health/live` | HTTP 200 | NATS |
| Safety Filter | 8006 | `/health/live` | HTTP 200 | NATS |
| Operator Console | 8007 | `/health/live` | HTTP 200 | All services |

### Infrastructure Services

| Service | Port | Type | Expected Status |
|---------|------|------|-----------------|
| NATS | 4222 | Message Broker | Accepting connections |
| NATS Streaming | 8222 | Stream Server | Accepting connections |
| Prometheus | 9090 | Metrics | Scraping all services |
| Grafana | 3000 | Visualization | Dashboard accessible |
| Jaeger Agent | 5775 | Tracing | Accepting traces |
| Jaeger Collector | 14268 | Tracing | Collecting traces |
| Jaeger UI | 16686 | Tracing | UI accessible |

## Expected Health Check Responses

### OpenClaw Orchestrator

```bash
$ curl http://localhost:8000/health/live
{"status":"healthy","services":{"dialogue_generator":"available","captioning":"available","bsl":"available","sentiment":"available","safety":"available"}}
```

**Expected metrics:**
- Uptime: > 0 seconds
- Memory: < 512MB
- CPU: < 50%
- Response time: < 100ms

### SceneSpeak

```bash
$ curl http://localhost:8001/health/live
{"status":"healthy","model":"loaded","queue_size":0}
```

**Expected metrics:**
- Model: Loaded and ready
- Queue: Empty or < 5 items
- Last request: < 60 seconds ago

### Captioning Service

```bash
$ curl http://localhost:8002/health/live
{"status":"healthy","stt":"ready","streaming":false}
```

**Expected metrics:**
- STT engine: Ready
- Active streams: 0 (unless demo is running)
- Audio buffer: Empty

### BSL Agent

```bash
$ curl http://localhost:8003/health/live
{"status":"healthy","translator":"active","supported_languages":["en-bsl"]}
```

**Expected metrics:**
- Translator: Active
- Cache hits: > 0 (if requests made)
- Translation queue: Empty

### Sentiment Analysis

```bash
$ curl http://localhost:8004/health/live
{"status":"healthy","model":"sentiment-v1","accuracy":"high"}
```

**Expected metrics:**
- Model: Loaded
- Processing time: < 200ms per request
- Cache: Available

### LSM Service

```bash
$ curl http://localhost:8005/health/live
{"status":"healthy","matcher":"active","styles_available":["formal","casual","dramatic"]}
```

**Expected metrics:**
- Style matcher: Active
- Available styles: 3+
- Last optimization: < 24 hours

### Safety Filter

```bash
$ curl http://localhost:8006/health/live
{"status":"healthy","policies":["family","teen","adult"],"default":"family"}
```

**Expected metrics:**
- Policies loaded: 3
- Rule cache: Populated
- Last update: < 7 days

### Operator Console

```bash
$ curl http://localhost:8007/health/live
{"status":"healthy","dashboard":"accessible","services_connected":8}
```

**Expected metrics:**
- Connected services: 8
- Dashboard: Loading without errors
- WebSocket: Connected (for real-time updates)

## Docker Compose Status

### Expected Output

```bash
$ docker-compose ps
NAME                     STATUS          PORTS
chimera-orchestrator     Up 2 hours      0.0.0.0:8000->8000/tcp
chimera-scenespeak       Up 2 hours      0.0.0.0:8001->8001/tcp
chimera-captioning       Up 2 hours      0.0.0.0:8002->8002/tcp
chimera-bsl              Up 2 hours      0.0.0.0:8003->8003/tcp
chimera-sentiment        Up 2 hours      0.0.0.0:8004->8004/tcp
chimera-lsm              Up 2 hours      0.0.0.0:8005->8005/tcp
chimera-safety           Up 2 hours      0.0.0.0:8006->8006/tcp
chimera-console          Up 2 hours      0.0.0.0:8007->8007/tcp
chimera-nats             Up 2 hours      0.0.0.0:4222->4222/tcp, 0.0.0.0:8222->8222/tcp
chimera-prometheus       Up 2 hours      0.0.0.0:9090->9090/tcp
chimera-grafana          Up 2 hours      0.0.0.0:3000->3000/tcp
chimera-jaeger           Up 2 hours      0.0.0.0:16686->16686/tcp
```

### What to Look For

- All services should show "Up" status
- No services in "Restarting" state
- No services with "Exit" status
- All port mappings correct
- Uptime should be reasonable (> 1 minute)

## NATS Status

### Expected State

```bash
$ nc -zv localhost 4222
Connection to localhost 4222 port [tcp/nats] succeeded!

$ nc -zv localhost 8222
Connection to localhost 8222 port [tcp/*] succeeded!
```

### Connection Test

```bash
$ curl http://localhost:8222/varz
{
  "server_id": "NATS...",
  "version": "2.x.x",
  "connections": 8,
  "subscriptions": 24,
  "messages": 150
}
```

**Expected:**
- Connections: 8 (one per service)
- Subscriptions: > 0
- Messages: > 0 (if requests made)

## Prometheus Metrics

### Expected Targets

Visit http://localhost:9090/targets

All services should show:
- **State**: UP
- **Health**: green
- **Last Scrape**: < 15 seconds ago

### Key Metrics to Check

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response times
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Service health
up{job="chimera"}
```

## Grafana Status

### Expected State

- **Login**: admin/admin
- **Data Sources**: Prometheus connected
- **Dashboards**: All loaded without errors
- **Refresh**: Working (auto-refresh every 10s)

### Dashboards to Verify

1. **System Overview**
   - CPU usage graph visible
   - Memory usage graph visible
   - Network I/O graph visible

2. **Service Health**
   - All 8 services showing green
   - Request rate visible
   - Response time visible

3. **AI Performance**
   - Model accuracy metrics
   - Token generation rate
   - Inference time

## Jaeger Status

### Expected State

- **UI Accessible**: http://localhost:16686
- **Services Listed**: All 8 core services
- **Recent Traces**: Visible (after demo requests)
- **Search**: Working

### Trace Verification

After making a test request, you should be able to:
1. Search for traces by service name
2. See trace details with spans
3. View trace timeline
4. See tags and logs for each span

## Common Health Issues

### Service Not Responding

**Symptoms:**
- Health endpoint times out
- Docker container shows "Restarting"

**Diagnosis:**
```bash
docker logs chimera-<service-name>
docker inspect chimera-<service-name>
```

**Common causes:**
- Port conflict
- Missing environment variables
- Dependency service down
- Out of memory

### High Memory Usage

**Symptoms:**
- Container using > 1GB RAM
- OOM kills in logs

**Expected memory per service:**
- Orchestrator: 256MB
- SceneSpeak: 512MB (AI model)
- Other AI services: 256MB each
- Console: 128MB

### Slow Response Times

**Expected response times:**
- Health checks: < 50ms
- Simple requests: < 500ms
- AI generation: < 2s

If slower:
- Check CPU usage
- Check network latency
- Check AI model loading
- Review Jaeger traces for bottlenecks

## Pre-Demo Verification Checklist

```bash
#!/bin/bash
# Run this before every demo

echo "Checking service health..."
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health/live | jq -r '.status'
done

echo "Checking infrastructure..."
echo -n "NATS: "
nc -zv localhost 4222 2>&1 | grep -q succeeded && echo "OK" || echo "FAIL"

echo -n "Prometheus: "
curl -s http://localhost:9090/-/healthy | jq -r '.status'

echo -n "Grafana: "
curl -s http://localhost:3000/api/health | jq -r '.database'

echo "Checking Docker..."
docker-compose ps | grep -q "Exit" && echo "WARNING: Some services exited!" || echo "All services running"
```

## Post-Demo Status

After demo completion, services should still be:
- Running normally
- No error spikes in logs
- Metrics returning to baseline
- No memory leaks (memory usage stable)

If shutting down:
```bash
docker-compose down
# Verify all containers stopped
docker-compose ps
```

---

**Status Reference Version:** 1.0
**Last Updated:** 2026-03-06
**Next Review:** After each demo
