# Project Chimera - Service Status Dashboard

Quick reference guide for all Project Chimera services, ports, endpoints, and health checks.

## Core Services (8 Services)

| Service | Port | Health Endpoint | API Endpoints | GPU/CPU | Status |
|---------|------|-----------------|---------------|---------|--------|
| **OpenClaw Orchestrator** | 8000 | `/health/live`, `/health/ready` | `/v1/orchestrate`, `/skills`, `/metrics` | CPU | ✅ Built |
| **SceneSpeak Agent** | 8001 | `/health`, `/` | `/v1/generate`, `/metrics` | GPU (1) | ✅ Built |
| **Captioning Agent** | 8002 | `/health`, `/` | `/api/v1/transcribe`, `/api/v1/stream`, `/metrics` | CPU | ✅ Built |
| **BSL Text2Gloss Agent** | 8003 | `/health`, `/` | `/api/v1/translate`, `/api/v1/translate/batch`, `/metrics` | CPU | ✅ Built |
| **Sentiment Agent** | 8004 | `/health`, `/` | `/api/v1/analyze`, `/api/v1/analyze-batch`, `/api/v1/trend`, `/metrics` | CPU | ✅ Built |
| **Lighting Control** | 8005 | `/health`, `/` | `/v1/lighting/*`, `/v1/cues/*`, `/v1/presets/*`, `/metrics` | CPU | ✅ Built |
| **Safety Filter** | 8006 | `/health`, `/` | `/api/v1/check`, `/api/v1/filter`, `/api/v1/policies`, `/stats`, `/metrics` | CPU | ✅ Built |
| **Operator Console** | 8007 | `/health`, `/` | `/console`, `/events`, `/approvals`, `/` (UI) | CPU | ✅ Built |

## Infrastructure Services

| Service | Port | Access | Health Check | Purpose |
|---------|------|--------|--------------|---------|
| **Redis** | 6379 | `localhost:6379` | `redis-cli ping` | Caching & Pub/Sub |
| **Kafka** | 9092, 9093 | `localhost:9092` | `kafka-topics.sh --list` | Event Streaming |
| **Prometheus** | 9090 | `http://localhost:9090` | `/-/healthy` | Metrics Collection |
| **Grafana** | 3000 | `http://localhost:3000` | `/api/health` | Visualization |
| **Jaeger** | 16686 (UI) | `http://localhost:16686` | `/` | Distributed Tracing |
| **Milvus Vector DB** | 19530 | `localhost:19530` | Health endpoint | Vector Storage |
| **MinIO** | 9000 | `localhost:9000` | `/minio/health/live` | Object Storage |
| **Etcd** | 2379 | `localhost:2379` | Health endpoint | Configuration |

## Quick Health Check Script

Save as `check_services.sh`:

```bash
#!/bin/bash

# Project Chimera Service Health Check
# Usage: ./check_services.sh

echo "🔍 Project Chimera Service Status"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Core services
SERVICES=(
  "8000:OpenClaw Orchestrator"
  "8001:SceneSpeak Agent"
  "8002:Captioning Agent"
  "8003:BSL Text2Gloss Agent"
  "8004:Sentiment Agent"
  "8005:Lighting Control"
  "8006:Safety Filter"
  "8007:Operator Console"
)

# Infrastructure services
INFRA=(
  "6379:Redis"
  "9092:Kafka"
  "9090:Prometheus"
  "3000:Grafana"
  "16686:Jaeger"
)

check_service() {
  local port=$1
  local name=$2

  if curl -s "http://localhost:${port}/health" > /dev/null 2>&1 || \
     curl -s "http://localhost:${port}/health/live" > /dev/null 2>&1 || \
     curl -s "http://localhost:${port}/" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} $name (${port})"
    return 0
  else
    echo -e "${RED}✗${NC} $name (${port})"
    return 1
  fi
}

echo "🎯 Core Services"
echo "----------------"
for service in "${SERVICES[@]}"; do
  IFS=':' read -r port name <<< "$service"
  check_service "$port" "$name"
done

echo ""
echo "🏗️  Infrastructure"
echo "-------------------"
for infra in "${INFRA[@]}"; do
  IFS=':' read -r port name <<< "$infra"
  if nc -z localhost "$port" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} $name (${port})"
  else
    echo -e "${RED}✗${NC} $name (${port})"
  fi
done

echo ""
echo "📊 Quick Commands"
echo "----------------"
echo "View logs: kubectl logs -f -n live deployment/<service-name>"
echo "Restart: kubectl rollout restart deployment/<service-name> -n live"
echo "Metrics: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/chimera)"
echo "Jaeger: http://localhost:16686"
```

Make it executable:
```bash
chmod +x check_services.sh
./check_services.sh
```

## Quick Curl Commands

### Check All Services
```bash
# OpenClaw Orchestrator
curl http://localhost:8000/health/ready

# SceneSpeak Agent
curl http://localhost:8001/health

# Captioning Agent
curl http://localhost:8002/health

# BSL Text2Gloss Agent
curl http://localhost:8003/health

# Sentiment Agent
curl http://localhost:8004/health

# Lighting Control
curl http://localhost:8005/health

# Safety Filter
curl http://localhost:8006/health

# Operator Console
curl http://localhost:8007/health
```

### Infrastructure Health Checks
```bash
# Redis
redis-cli ping

# Kafka
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health

# All service metrics
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  echo "Port $port metrics:"
  curl -s http://localhost:$port/metrics | head -5
  echo ""
done
```

## Troubleshooting

### Service Won't Start

**1. Check port conflicts:**
```bash
# Check if port is in use
lsof -i :8000
netstat -tulpn | grep 8000
```

**2. Check k3s/Docker logs:**
```bash
# View logs for a specific service
kubectl logs -n live deployment/openclaw-orchestrator

# Follow logs in real-time
kubectl logs -f -n live deployment/openclaw-orchestrator

# View all service logs
kubectl logs -f -n live --all-containers=true
```

**3. Check service health:**
```bash
# Direct health check
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready

# With details
curl -s http://localhost:8000/health/ready | jq .
```

### Connection Issues

**1. Verify network:**
```bash
# Check Docker network
docker network inspect chimera-network

# Check if containers can reach each other
docker exec chimera-openclaw ping chimera-redis
```

**2. Test Redis connection:**
```bash
# From host
redis-cli -h localhost -p 6379 ping

# From container
docker exec chimera-openclaw redis-cli -h redis -p 6379 ping
```

**3. Test Kafka connection:**
```bash
# List topics
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Create test topic
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test --partitions 1 --replication-factor 1
```

### GPU Issues

**1. Check GPU availability:**
```bash
# List GPUs
nvidia-smi

# Check GPU usage by containers
docker exec chimera-scenespeak nvidia-smi
```

**2. Verify GPU access in container:**
```bash
# Check if GPU is accessible
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check SceneSpeak GPU access
docker exec chimera-scenespeak python -c "import torch; print(torch.cuda.is_available())"
```

### Memory/CPU Issues

**1. Check resource usage:**
```bash
# Container stats
docker stats

# Specific container
docker stats chimera-openclaw

# All Chimera containers
docker stats --no-stream | grep chimera
```

**2. View resource limits:**
```bash
# Check container limits
docker inspect chimera-openclaw | grep -A 10 "Memory"

# System resources
free -h
top -bn1 | head -20
```

## Service Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Operator Console (8007)                   │
│                   (Human Oversight & Control)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 OpenClaw Orchestrator (8000)                 │
│              (Skill Routing & GPU Scheduling)                │
└───┬───────────┬───────────┬───────────┬───────────┬─────────┘
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
┌─────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
│Scene│  │Captioning│  │   BSL    │  │Sentiment │  │  Safety   │
│Speak│  │  Agent   │  │  Agent   │  │  Agent   │  │  Filter   │
│(8001)│  │  (8002)  │  │  (8003)  │  │  (8004)  │  │  (8006)   │
└─────┘  └──────────┘  └──────────┘  └──────────┘  └─────┬─────┘
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │  Lighting Control │
                                                    │      (8005)        │
                                                    └───────────────────┘

Shared Infrastructure:
- Redis (6379): Caching & Pub/Sub
- Kafka (9092): Event Streaming
- Prometheus (9090): Metrics
- Grafana (3000): Dashboards
- Jaeger (16686): Tracing
```

## Development Quick Start

```bash
# Start all services (k3s bootstrap)
make bootstrap

# Start only infrastructure
kubectl apply -k infrastructure/kubernetes/base/

# Start specific service
kubectl apply -f infrastructure/kubernetes/services/<service>/

# View logs
kubectl logs -f -n live deployment/<service-name>

# Stop all services
make bootstrap-destroy

# Restart specific service
kubectl rollout restart deployment/<service-name> -n live
```

## Dashboard URLs

| Dashboard | URL | Credentials |
|-----------|-----|-------------|
| Prometheus | http://localhost:9090 | None |
| Grafana | http://localhost:3000 | admin/chimera |
| Jaeger | http://localhost:16686 | None |
| API Docs (SceneSpeak) | http://localhost:8001/docs | None |
| API Docs (Captioning) | http://localhost:8002/docs | None |
| API Docs (Sentiment) | http://localhost:8004/docs | None |
| API Docs (Safety) | http://localhost:8006/docs | None |
| Operator Console | http://localhost:8007 | None |

## Status Legend

- ✅ **Built** - Service code is complete and Dockerfile exists
- 🚧 **In Progress** - Service is under development
- ⏳ **Planned** - Service is planned but not started
- ❌ **Blocked** - Service is blocked by dependencies

## Service Build Status

All 8 core services are built and ready:
1. ✅ OpenClaw Orchestrator
2. ✅ SceneSpeak Agent
3. ✅ Captioning Agent
4. ✅ BSL Text2Gloss Agent
5. ✅ Sentiment Agent
6. ✅ Lighting Control
7. ✅ Safety Filter
8. ✅ Operator Console

## Next Steps

- Run `./check_services.sh` to verify all services are running
- Access Grafana dashboards at http://localhost:3000
- Check Jaeger traces at http://localhost:16686
- Review Prometheus metrics at http://localhost:9090
