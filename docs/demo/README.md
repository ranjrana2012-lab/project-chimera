# Project Chimera Demo Guide

**Demo Date:** Monday, March 10, 2026
**Audience:** 15 Students
**Duration:** 30 minutes

## Overview

This guide contains everything needed to prepare and execute the Project Chimera demo. Project Chimera is an AI-powered live theatre platform that provides real-time accessibility features including dialogue generation, captioning, British Sign Language (BSL) translation, and sentiment analysis.

## Demo Structure

The 30-minute demo covers:

1. **System Overview (5 min)** - Architecture and service responsibilities
2. **Orchestrator Demo (5 min)** - Central routing and skill dispatch
3. **AI Agents Demo (10 min)** - Individual AI capabilities
4. **Operator Console (5 min)** - Real-time monitoring
5. **Observability (5 min)** - Metrics, logs, and tracing

## Quick Start

### Pre-Demo Setup

```bash
# Navigate to project directory
cd /home/ranj/Project_Chimera

# Run the pre-demo setup script
./scripts/demo-prep.sh

# Start all services
./scripts/demo-start.sh

# Check service status
./scripts/demo-status.sh
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Operator Console | http://localhost:8007 | None |
| Grafana Dashboards | http://localhost:3000 | admin/admin |
| Jaeger Tracing | http://localhost:16686 | None |
| Prometheus | http://localhost:9090 | None |

## Demo Checklist

Run through this checklist before the demo:

### Infrastructure
- [ ] Docker and Docker Compose installed
- [ ] All services running (`docker-compose ps`)
- [ ] No containers in error state
- [ ] Sufficient disk space (>5GB)

### Service Health
- [ ] OpenClaw Orchestrator responding (localhost:8000)
- [ ] SceneSpeak Dialogue Generator responding (localhost:8001)
- [ ] Captioning Service responding (localhost:8002)
- [ ] BSL Agent responding (localhost:8003)
- [ ] Sentiment Analysis responding (localhost:8004)
- [ ] LSM Service responding (localhost:8005)
- [ ] Safety Filter responding (localhost:8006)
- [ ] Operator Console responding (localhost:8007)

### Observability
- [ ] Grafana accessible and dashboards loaded
- [ ] Jaeger accessible and showing traces
- [ ] Prometheus scraping metrics
- [ ] Logs flowing to console/stdout

### Demo Materials
- [ ] Demo script printed ([demo-script.md](demo-script.md))
- [ ] Sample requests ready ([sample-request.py](../../examples/sample-request.py))
- [ ] Demo scenario data loaded ([demo-scenario.json](../../examples/demo-scenario.json))
- [ ] Troubleshooting guide available ([troubleshooting.md](troubleshooting.md))

### Audio/Visual
- [ ] Projector/monitor connected
- [ ] Audio working (for captioning demo)
- [ ] Browser tabs prepared
- [ ] Font size readable from back of room

## Services Overview

### Core Services

| Service | Port | Purpose |
|---------|------|---------|
| OpenClaw Orchestrator | 8000 | Central routing and skill dispatch |
| SceneSpeak | 8001 | AI dialogue generation |
| Captioning Service | 8002 | Real-time speech-to-text |
| BSL Agent | 8003 | British Sign Language translation |
| Sentiment Analysis | 8004 | Emotional tone analysis |
| LSM Service | 8005 | Language Style Matching |
| Safety Filter | 8006 | Content moderation |
| Operator Console | 8007 | Monitoring dashboard |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| NATS | 4222 | Message broker |
| NATS Streaming | 8222 | Stream processing |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Metrics visualization |
| Jaeger | 16686 | Distributed tracing |

## Sample Requests

### Generate Dialogue
```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "dialogue_generator",
    "input": {
      "prompt": "A dramatic monologue about discovering a hidden secret",
      "style": "dramatic"
    }
  }'
```

### Analyze Sentiment
```bash
curl -X POST http://localhost:8004/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I absolutely love this amazing platform!"
  }'
```

### Check Safety
```bash
curl -X POST http://localhost:8006/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to the show!",
    "policy": "family"
  }'
```

## Troubleshooting

If you encounter issues during the demo, refer to [troubleshooting.md](troubleshooting.md) for common problems and solutions.

Quick fixes:

```bash
# Restart a specific service
docker-compose restart <service-name>

# View service logs
docker-compose logs -f <service-name>

# Restart all services
./scripts/demo-start.sh

# Check system status
./scripts/demo-status.sh
```

## Post-Demo

After the demo:

1. **Stop Services**: `docker-compose down`
2. **Collect Feedback**: Distribute feedback forms
3. **Document Issues**: Note any problems encountered
4. **Clean Up**: Remove temporary demo data

## Contact

For issues during the demo:
- Check the [troubleshooting guide](troubleshooting.md)
- Review service logs: `docker-compose logs -f`
- Check [service status documentation](service-status.md)

---

**Demo Version:** 1.0
**Last Updated:** 2026-03-06
**Next Review:** Post-demo debrief
