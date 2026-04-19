# Project Chimera Production Runbook

**Version:** 1.0
**Last Updated:** April 19, 2026
**Target Environment:** Self-hosted university/organization infrastructure

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment](#deployment)
4. [Service Management](#service-management)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Overview

Project Chimera is an AI-powered live theatre platform with 8 core microservices. This runbook covers operational procedures for deployment, monitoring, and maintenance in a production environment.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Project Chimera MVP Services                   │
├─────────────────────────────────────────────────────────────┤
│ Operator Console (8007)  →  Web UI for control               │
│       ↓                                                    │
│ OpenClaw Orchestrator (8000) →  Central coordination          │
│       ↓                                                    │
│  ┌────┬────┬────┬────┬────┬─────────┐                      │
│  ↓    ↓    ↓    ↓    ↓    ↓         ↓                      │
│ SceneSpeak  Trans Sentiment  Safety  Dashboard  Health        │
│  (8001)    (8002)(8004)    (8006)    (8013)     (8012)        │
│  (LLM)     (API) (ML)      (Rules)   (Stats)     (Status)      │
│                                                             │
│  Redis Cache (6379) ← Shared caching layer                   │
└─────────────────────────────────────────────────────────────┘
```

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| OpenClaw Orchestrator | 8000 | Central coordination |
| SceneSpeak Agent | 8001 | LLM dialogue generation |
| Translation Agent | 8002 | Multi-language translation |
| Sentiment Agent | 8004 | Audience sentiment analysis |
| Safety Filter | 8006 | Content moderation |
| Operator Console | 8007 | Web UI |
| Health Aggregator | 8012 | Health status aggregation |
| Dashboard | 8013 | Metrics dashboard |
| Redis | 6379 | Request caching |

---

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD

**Recommended (Production):**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- GPU: Optional (for local LLM acceleration)

### Software Requirements

- **Docker:** 24.0 or later
- **Docker Compose:** 2.20 or later
- **Systemd:** For auto-start on boot (Linux)
- **curl:** For health checks

### Network Requirements

- Firewall ports: 8000-8007, 6379
- Outbound internet access (for ML model downloads, translation API)

### User Setup

Create a dedicated user for running Chimera:

```bash
sudo useradd -m -s /bin/bash chimera
sudo usermod -aG docker chimera
```

---

## Deployment

### Initial Deployment

**Step 1: Prepare the environment**

```bash
# Clone or update repository
cd /opt  # or your preferred location
sudo git clone https://github.com/ranjrana2012-lab/project-chimera.git
sudo chown -R chimera:chimera project-chimera
cd project-chimera
```

**Step 2: Configure environment variables**

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

Key environment variables:
- `GOOGLE_TRANSLATE_API_KEY`: For translation agent
- `SENTIMENT_ML_MODEL_PATH`: Path to ML models (if using local)
- `LOG_LEVEL`: Logging level (INFO, WARNING, ERROR)

**Step 3: Run deployment script**

```bash
./scripts/deploy-production.sh
```

The deployment script will:
1. Check prerequisites (Docker, ports availability)
2. Build all Docker images
3. Start services in dependency order
4. Wait for health checks to pass
5. Verify ML model loading (may take 30-60s on first startup)
6. Run smoke tests

### Verification

**Check service health:**

```bash
# All services health status
curl http://localhost:8000/health/ready
curl http://localhost:8001/health
curl http://localhost:8004/health
curl http://localhost:8006/health
curl http://localhost:8007/health
```

**Verify orchestration works:**

```bash
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The hero enters the dark room",
    "show_id": "test_show",
    "context": {"genre": "thriller"}
  }'
```

Expected response time: <5 seconds

---

## Service Management

### Starting Services

**Automatic start (recommended):**

```bash
./scripts/deploy-production.sh
```

**Manual start:**

```bash
docker compose -f docker-compose.mvp.yml up -d
```

### Stopping Services

**Graceful stop:**

```bash
./scripts/stop-production.sh
```

**Force stop:**

```bash
./scripts/stop-production.sh --force
```

### Restarting Services

```bash
# Restart all services
docker compose -f docker-compose.mvp.yml restart

# Restart specific service
docker compose -f docker-compose.mvp.yml restart orchestrator
```

### Viewing Logs

**All services:**

```bash
docker compose -f docker-compose.mvp.yml logs -f
```

**Specific service:**

```bash
docker compose -f docker-compose.mvp.yml logs -f orchestrator
docker compose -f docker-compose.mvp.yml logs -f sentiment-agent
```

**Last 100 lines:**

```bash
docker compose -f docker-compose.mvp.yml logs --tail=100 orchestrator
```

### Auto-Start on Boot

**Install systemd service:**

```bash
sudo cp scripts/systemd/project-chimera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable project-chimera.service
```

**Control service:**

```bash
# Start service
sudo systemctl start project-chimera

# Stop service
sudo systemctl stop project-chimera

# Check status
sudo systemctl status project-chimera

# View logs
sudo journalctl -u project-chimera -f
```

---

## Monitoring

### Performance Monitoring Script

Run continuous monitoring:

```bash
# Monitor for 1 hour (default)
./scripts/monitor-performance.sh

# Monitor for 8 hours
./scripts/monitor-performance.sh 28800

# Monitor for 1 day with 60s intervals
./scripts/monitor-performance.sh 86400 60
```

The monitoring script tracks:
- Service health status
- End-to-end orchestration latency (target: <5s)
- Cache hit performance (target: <100ms)
- Threshold-based alerting

### Grafana Dashboard

**Import dashboard:**

1. Open Grafana (http://your-grafana:3000)
2. Navigate to Dashboards → Import
3. Upload `scripts/monitor/grafana-dashboard.json`

**Dashboard panels:**
- Response time (p95) with 5s threshold alert
- Requests per second by service
- Cache hit rate percentage
- Connection pool utilization
- Service health status
- ML model load time
- Error rate

### Prometheus Metrics

All services expose metrics on `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8004/metrics
```

---

## Troubleshooting

### Services Won't Start

**Check Docker daemon:**

```bash
sudo systemctl status docker
sudo systemctl start docker
```

**Check port conflicts:**

```bash
sudo netstat -tulpn | grep -E ':(8000|8001|8002|8004|8006|8007)'
```

**Check logs:**

```bash
docker compose -f docker-compose.mvp.yml logs
```

### Slow First Request

**ML model loading (first request only):**

On first startup, ML models download and load. This can take 30-60 seconds for the sentiment agent. Subsequent requests will be fast.

**Verify model is loaded:**

```bash
curl http://localhost:8004/health | jq .model_loaded
```

Expected: `true`

### High Memory Usage

**Check container resource usage:**

```bash
docker stats
```

**Cleanup unused resources:**

```bash
docker system prune -a
```

### Translation Not Working

**Check API key configuration:**

```bash
docker compose -f docker-compose.mvp.yml logs translation-agent | grep -i api
```

**Verify Google Translate API key:**

```bash
curl http://localhost:8002/health | jq .engine.google_api_configured
```

### Orchestration Timeout

**Check agent connectivity:**

```bash
curl http://localhost:8000/health/ready
```

Expected: All agents show `"true"`

**Check individual agents:**

```bash
curl http://localhost:8001/health    # SceneSpeak
curl http://localhost:8004/health    # Sentiment
curl http://localhost:8006/health    # Safety
```

### Cache Not Working

**Check Redis is running:**

```bash
docker compose -f docker-compose.mvp.yml ps redis
```

**Test Redis connection:**

```bash
docker compose -f docker-compose.mvp.yml exec redis redis-cli ping
```

Expected: `PONG`

---

## Maintenance

### Updating Services

**Zero-downtime deployment (rolling update):**

```bash
# Pull latest code
git pull

# Rebuild specific service
docker compose -f docker-compose.mvp.yml build orchestrator

# Restart with minimal downtime
docker compose -f docker-compose.mvp.yml up -d orchestrator
```

### Backup and Restore

**Backup data:**

```bash
# Backup Redis data
docker compose -f docker-compose.mvp.yml exec redis redis-cli SAVE

# Copy Redis backup file
docker cp chimera-redis:/data/dump.rdb ./backup.rdb
```

**Restore data:**

```bash
# Stop Redis
docker compose -f docker-compose.mvp.yml stop redis

# Copy backup file
docker cp ./backup.rdb chimera-redis:/data/dump.rdb

# Start Redis
docker compose -f docker-compose.mvp.yml start redis
```

### Log Rotation

**Configure log rotation (systemd):**

```bash
sudo nano /etc/logrotate.d/project-chimera
```

Contents:

```
/opt/project-chimera/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 chimera chimera
}
```

### Security Updates

**Update base images:**

```bash
docker compose -f docker-compose.mvp.yml pull
docker compose -f docker-compose.mvp.yml build --no-cache
docker compose -f docker-compose.mvp.yml up -d
```

**Scan for vulnerabilities:**

```bash
docker scan ghcr.io/example/chimera/orchestrator:latest
```

---

## Emergency Procedures

### Complete System Failure

**Emergency shutdown:**

```bash
./scripts/stop-production.sh --force
sudo systemctl stop project-chimera
```

**Emergency restart:**

```bash
sudo systemctl restart project-chimera
# OR
./scripts/deploy-production.sh
```

### Rollback to Previous Version

```bash
# View previous commits
git log --oneline

# Reset to previous version
git reset --hard <previous-commit-hash>

# Rebuild and deploy
./scripts/deploy-production.sh
```

### Data Recovery

**Redis cache recovery:**

If Redis cache is lost, services will continue operating (with degraded performance until cache warms up). No manual recovery needed.

**Show state recovery:**

Show state is maintained in memory and resets on restart. No persistence needed.

---

## Support

**Documentation:** https://github.com/ranjrana2012-lab/project-chimera

**Issues:** https://github.com/ranjrana2012-lab/project-chimera/issues

**For urgent issues during university performances:**
1. Check service status: `curl http://localhost:8000/health/ready`
2. Check logs: `docker compose -f docker-compose.mvp.yml logs -f`
3. Restart affected service: `docker compose -f docker-compose.mvp.yml restart <service>`

---

**End of Runbook**
