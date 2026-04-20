# Deployment Guide

**Version:** 1.0.0 (MVP)
**Last Updated:** April 11, 2026

---

## Overview

This guide covers deploying Project Chimera MVP using Docker Compose. The MVP architecture simplifies deployment by using synchronous orchestration with local infrastructure, removing dependencies on Kafka, Milvus, and Kubernetes.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment Options](#deployment-options)
3. [MVP Deployment (Docker Compose)](#mvp-deployment-docker-compose)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Scaling & Performance](#scaling--performance)

---

## Quick Start

### 5-Minute Deployment

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Start MVP services
docker-compose -f docker-compose.mvp.yml up -d

# Verify deployment
curl http://localhost:8000/health
curl http://localhost:8007/health
```

That's it! Project Chimera MVP is now running.

---

## Deployment Options

### 1. MVP Development (Recommended for Testing)

**Best for:** Development, testing, demos

**Pros:**
- Single command deployment
- Minimal resource requirements (8GB RAM)
- No external dependencies
- Fast startup (<5 minutes)

**Cons:**
- Single node deployment
- Limited scalability
- Development-grade infrastructure

### 2. Production Deployment (Docker Compose)

**Best for:** Small productions, single-venue deployments

**Pros:**
- Production-ready configuration
- External Redis support
- Monitoring integration
- Easy maintenance

**Cons:**
- Limited horizontal scaling
- Manual failover required

### 3. Kubernetes Deployment (Future)

**Best for:** Large-scale, multi-venue deployments

**Note:** Kubernetes deployment is planned for Phase 2. Currently, use Docker Compose.

---

## MVP Deployment (Docker Compose)

### Architecture

The MVP uses `docker-compose.mvp.yml` which includes:

```
Services:
├── openclaw-orchestrator (8000)    # Core orchestration
├── scenespeak-agent (8001)          # Dialogue generation
├── sentiment-agent (8004)           # Sentiment analysis
├── safety-filter (8005)             # Content moderation
├── translation-agent (8006)         # Translation
├── operator-console (8007)          # Control UI
├── hardware-bridge (8008)           # DMX simulation
└── redis (6379)                     # State management
```

### Step 1: Prerequisites

**System Requirements:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Linux/macOS/Windows | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 20 GB | 50+ GB SSD |

**Software Requirements:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Step 2: Environment Configuration

Create `.env` file:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum Configuration:**

```bash
# Service Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Redis Configuration
REDIS_URL=redis://redis:6379

# Optional: LLM Configuration
# GLM_API_KEY=your_api_key_here
# GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4/
```

### Step 3: Deploy Services

```bash
# Start all services
docker-compose -f docker-compose.mvp.yml up -d

# Check service status
docker-compose -f docker-compose.mvp.yml ps

# View logs
docker-compose -f docker-compose.mvp.yml logs -f
```

### Step 4: Verify Deployment

```bash
# Health check script
for port in 8000 8001 8004 8005 8006 8007 8008; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health | jq '.status' 2>/dev/null || echo "Service not ready"
done

# Expected output: "ok" for all services
```

### Service Access

Once deployed, services are available at:

| Service | URL | Purpose |
|---------|-----|---------|
| Operator Console | http://localhost:8007 | Main UI |
| OpenClaw Orchestrator | http://localhost:8000 | Core API |
| SceneSpeak Agent | http://localhost:8001 | Dialogue API |
| Sentiment Agent | http://localhost:8004 | Sentiment API |
| Safety Filter | http://localhost:8005 | Moderation API |
| Translation Agent | http://localhost:8006 | Translation API |
| Hardware Bridge | http://localhost:8008 | DMX simulation |

---

## Production Deployment

### Production Docker Compose

For production deployment, use `docker-compose.prod.yml`:

```bash
# Deploy with production configuration
docker-compose -f docker-compose.mvp.yml -f docker-compose.prod.yml up -d
```

### Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

# Production overrides for MVP
services:
  # Use external Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - chimera-redis-prod:/data
    restart: always

  # Add resource limits
  openclaw-orchestrator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: always

  scenespeak-agent:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: always

  # Add health checks
  sentiment-agent:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: always

volumes:
  chimera-redis-prod:
    driver: local
```

### Environment Variables for Production

Create `.env.production`:

```bash
# Production Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Security
REDIS_PASSWORD=your_secure_redis_password

# LLM Configuration (Required for production)
GLM_API_KEY=your_production_api_key
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4/

# Local LLM Fallback
LOCAL_LLM_ENABLED=true
LOCAL_LLM_URL=http://host.docker.internal:8012
LOCAL_LLM_MODEL=nemotron-3-super-120b-a12b-nvfp4

# Service URLs (Internal Docker Network)
SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
SENTIMENT_AGENT_URL=http://sentiment-agent:8004
SAFETY_FILTER_URL=http://safety-filter:8005
TRANSLATION_AGENT_URL=http://translation-agent:8006

# Timeouts
LLM_TIMEOUT=120
SERVICE_TIMEOUT=30
```

### Production Deployment Steps

```bash
# 1. Set environment
export COMPOSE_FILE=docker-compose.mvp.yml:docker-compose.prod.yml
export ENV_FILE=.env.production

# 2. Deploy infrastructure
docker-compose -f docker-compose.mvp.yml -f docker-compose.prod.yml up -d redis

# 3. Wait for Redis to be ready
sleep 10

# 4. Deploy services
docker-compose -f docker-compose.mvp.yml -f docker-compose.prod.yml up -d

# 5. Verify deployment
docker-compose ps
./scripts/health-check-all.sh

# 6. Enable service monitoring
docker-compose -f docker-compose.mvp.yml -f docker-compose.prod.yml logs -f
```

### External Services

For production, consider using external services:

**External Redis:**

```yaml
# In docker-compose.prod.yml
services:
  openclaw-orchestrator:
    environment:
      - REDIS_URL=redis://your-external-redis:6379
```

**Load Balancer:**

```nginx
# nginx.conf
upstream chimera {
    server localhost:8000;
    server localhost:8001 backup;
}

server {
    listen 80;
    location / {
        proxy_pass http://chimera;
    }
}
```

---

## Configuration

### Service Configuration

All services use consistent configuration:

```yaml
environment:
  - SERVICE_NAME=openclaw-orchestrator
  - PORT=8000
  - ENVIRONMENT=production
  - LOG_LEVEL=INFO
```

### Network Configuration

Services communicate via Docker networks:

```yaml
networks:
  chimera-backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
  chimera-frontend:
    driver: bridge
```

### Volume Management

Persistent data volumes:

```yaml
volumes:
  chimera-redis-data:
    driver: local
  sentiment-models:
    driver: local
```

---

## Monitoring & Health Checks

### Health Endpoints

All services expose `/health` endpoints:

```bash
# Check individual service
curl http://localhost:8000/health

# Expected response:
{
  "status": "ok",
  "service": "openclaw-orchestrator",
  "version": "1.0.0",
  "dependencies": {
    "redis": "ok",
    "scenespeak-agent": "ok"
  }
}
```

### Health Check Script

Create `scripts/health-check-all.sh`:

```bash
#!/bin/bash
services=(8000 8001 8004 8005 8006 8007 8008)
all_healthy=true

for port in "${services[@]}"; do
  status=$(curl -s http://localhost:$port/health | jq -r '.status' 2>/dev/null)
  if [ "$status" == "ok" ]; then
    echo "✅ Port $port: Healthy"
  else
    echo "❌ Port $port: Unhealthy"
    all_healthy=false
  fi
done

if [ "$all_healthy" = true ]; then
  echo "All services healthy!"
  exit 0
else
  echo "Some services are unhealthy!"
  exit 1
fi
```

### Monitoring Setup

**Basic Monitoring:**

```bash
# Watch service logs
docker-compose -f docker-compose.mvp.yml logs -f

# Check resource usage
docker stats

# Check service status
docker-compose -f docker-compose.mvp.yml ps
```

**Advanced Monitoring (Optional):**

```bash
# Deploy monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3000

# Access Prometheus
open http://localhost:9090
```

---

## Troubleshooting

### Common Issues

#### Services Not Starting

**Problem:** Services fail to start

**Solution:**
```bash
# Check logs
docker-compose -f docker-compose.mvp.yml logs [service-name]

# Rebuild containers
docker-compose -f docker-compose.mvp.yml build --no-cache
docker-compose -f docker-compose.mvp.yml up -d

# Check for port conflicts
netstat -tulpn | grep LISTEN
```

#### Out of Memory

**Problem:** Services crash due to memory issues

**Solution:**
```bash
# Check Docker memory
docker system df

# Increase Docker memory limit (Docker Desktop settings)
# Recommended: 8GB minimum, 16GB for production

# Clean up unused resources
docker system prune -a
```

#### Connection Refused

**Problem:** Services can't connect to each other

**Solution:**
```bash
# Check network
docker network ls
docker network inspect chimera-backend

# Verify service names
docker-compose -f docker-compose.mvp.yml ps

# Test connectivity
docker-compose -f docker-compose.mvp.yml exec openclaw-orchestrator \
  curl http://scenespeak-agent:8001/health
```

#### LLM API Errors

**Problem:** SceneSpeak agent fails to generate dialogue

**Solution:**
```bash
# Verify API key
docker-compose -f docker-compose.mvp.yml exec scenespeak-agent env | grep GLM

# Test API key
curl https://open.bigmodel.cn/api/paas/v4/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Use mock mode for testing
# Set TRANSLATION_AGENT_USE_MOCK=true in .env
```

### Debug Commands

```bash
# View service logs
docker-compose -f docker-compose.mvp.yml logs -f [service-name]

# Exec into container
docker-compose -f docker-compose.mvp.yml exec [service-name] /bin/bash

# Check service status
docker-compose -f docker-compose.mvp.yml ps

# Restart specific service
docker-compose -f docker-compose.mvp.yml restart [service-name]

# Rebuild specific service
docker-compose -f docker-compose.mvp.yml build [service-name]
docker-compose -f docker-compose.mvp.yml up -d [service-name]
```

### Recovery Procedures

**Full Restart:**
```bash
# Stop all services
docker-compose -f docker-compose.mvp.yml down

# Remove volumes (WARNING: Deletes data)
docker-compose -f docker-compose.mvp.yml down -v

# Restart
docker-compose -f docker-compose.mvp.yml up -d
```

**Service Recovery:**
```bash
# Restart specific service
docker-compose -f docker-compose.mvp.yml restart [service-name]

# Rebuild and restart
docker-compose -f docker-compose.mvp.yml up -d --build [service-name]
```

---

## Scaling & Performance

### Horizontal Scaling

**Scale services:**
```bash
# Scale specific service
docker-compose -f docker-compose.mvp.yml up -d --scale scenespeak-agent=3

# Scale multiple services
docker-compose -f docker-compose.mvp.yml up -d \
  --scale scenespeak-agent=3 \
  --scale sentiment-agent=2
```

**Load Balancing:**

Add load balancer in `docker-compose.prod.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "8000:8000"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - openclaw-orchestrator
```

### Performance Tuning

**Resource Limits:**

```yaml
services:
  scenespeak-agent:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

**Performance Optimization:**

1. **Enable model caching** for sentiment agent
2. **Use local LLM fallback** for faster response
3. **Adjust timeouts** based on network latency
4. **Monitor resource usage** with `docker stats`

### Backup & Recovery

**Backup Data:**

```bash
# Backup Redis data
docker-compose -f docker-compose.mvp.yml exec redis \
  redis-cli SAVE

# Copy Redis backup
docker cp chimera-redis:/data/dump.rdb backup/redis-$(date +%Y%m%d).rdb
```

**Restore Data:**

```bash
# Copy backup to container
docker cp backup/redis-20260411.rdb chimera-redis:/data/dump.rdb

# Restart Redis
docker-compose -f docker-compose.mvp.yml restart redis
```

---

## Security Considerations

### Production Security

1. **Use strong passwords** for Redis
2. **Enable HTTPS/TLS** for external access
3. **Implement rate limiting** on API endpoints
4. **Secure API keys** with environment variables
5. **Network isolation** through Docker networks
6. **Regular security updates**

### Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
ufw enable
```

---

## Additional Resources

- [MVP Overview](MVP_OVERVIEW.md) - Architecture details
- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [Testing Guide](TESTING.md) - Testing procedures
- [API Documentation](docs/api/README.md) - Complete API reference

---

**Need help?**
- GitHub Issues: https://github.com/ranjrana2012-lab/project-chimera/issues
- Documentation: [docs/](docs/)
- Community: Discussion forums (coming soon)

---

**Deployment Guide v1.0.0** - MVP Release
**Last Updated:** April 11, 2026
