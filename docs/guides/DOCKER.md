# Docker Compose - Project Chimera

This document explains how to use Docker Compose to orchestrate all Project Chimera services for local development and demo.

## Overview

The Docker Compose setup includes:

- **8 Core Services**: Orchestrator and AI agents (ports 8000-8007)
- **5 Infrastructure Services**: Redis, Kafka, Prometheus, Jaeger, Grafana
- **Networking**: All services on `chimera-network` for internal communication
- **Volumes**: Persistent storage for infrastructure services

## Quick Start

### Start All Services (Development Mode)

```bash
./scripts/docker-start.sh dev
```

This will:
1. Build all Docker images
2. Start infrastructure services (Redis, Kafka, Prometheus, Jaeger, Grafana)
3. Start all core services with hot-reload enabled
4. Display service URLs and recent logs

### Start All Services (Production Mode)

```bash
./scripts/docker-start.sh prod
```

This will:
1. Build production-optimized Docker images
2. Start all services with resource limits
3. Disable debug logging and hot-reload

### Check Service Status

```bash
./scripts/docker-status.sh
```

This will show:
- Health status of all core services
- Status of infrastructure services
- Recent logs
- Resource usage (CPU, memory)

### Stop All Services

```bash
./scripts/docker-stop.sh
```

To also remove volumes (clean slate):

```bash
./scripts/docker-stop.sh --clean
```

To prune Docker resources:

```bash
./scripts/docker-stop.sh --prune
```

## Services

### Core Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| OpenClaw Orchestrator | 8000 | Central orchestration service | `/health/live` |
| SceneSpeak Agent | 8001 | Script generation agent | `/health/live` |
| Captioning Agent | 8002 | Live captioning service | `/health/live` |
| BSL Agent | 8003 | Sign language translation | `/health/live` |
| Sentiment Agent | 8004 | Audience sentiment analysis | `/health/live` |
| Lighting-Sound-Music | 8005 | Stage control service | `/health/live` |
| Safety Filter | 8006 | Content moderation | `/health` |
| Operator Console | 8007 | Monitoring dashboard | `/health/live` |

### Infrastructure Services

| Service | Port | Description | Access |
|---------|------|-------------|--------|
| Redis | 6379 | Caching layer | `redis://localhost:6379` |
| Kafka | 9092 | Event streaming | `localhost:9092` |
| Prometheus | 9090 | Metrics collection | http://localhost:9090 |
| Jaeger | 16686 | Distributed tracing | http://localhost:16686 |
| Grafana | 3000 | Dashboards | http://localhost:3000 (admin/chimera) |

## Configuration

### Environment Variables

The `.env.docker` file contains all environment variables for Docker Compose. Key variables:

```bash
# Service URLs (internal networking)
OPENCLAW_ORCHESTRATOR_URL=http://openclaw-orchestrator:8000
SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
# ... etc

# Infrastructure
REDIS_URL=redis://redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
OTLP_ENDPOINT=http://jaeger:4317
```

### Docker Compose Files

- `docker-compose.yml` - Base configuration with all services
- `docker-compose.dev.yml` - Development overrides (hot-reload, debug logging, volume mounts)
- `docker-compose.prod.yml` - Production overrides (resource limits, restart policies)

### Prometheus Configuration

Located at `config/prometheus.yml`:

- Scrape interval: 15 seconds
- All services expose `/metrics` endpoint
- Auto-discovery of all core services

### Grafana Configuration

Located at `config/grafana/`:

- Datasource: Prometheus auto-configured
- Dashboards: Provisioned from `config/grafana/dashboards/`
- Default credentials: admin/chimera

## Development Workflow

### Start Development Environment

```bash
# Start all services with hot-reload
./scripts/docker-start.sh dev

# View logs for a specific service
docker-compose logs -f openclaw-orchestrator

# View logs for all services
docker-compose logs -f
```

### Make Changes to Code

With hot-reload enabled (dev mode), changes to Python files will automatically reload:

```bash
# Edit a service file
vim services/openclaw-orchestrator/main.py

# Changes are reflected automatically
# Check logs to see reload happening
docker-compose logs -f openclaw-orchestrator
```

### Rebuild After Dependency Changes

If you modify `requirements.txt` or `Dockerfile`:

```bash
# Rebuild specific service
docker-compose build openclaw-orchestrator

# Rebuild all services
docker-compose build

# Restart with new build
docker-compose up -d
```

## Troubleshooting

### Service Won't Start

1. Check service logs:
   ```bash
   docker-compose logs openclaw-orchestrator
   ```

2. Check if port is already in use:
   ```bash
   lsof -i :8000
   ```

3. Check service health:
   ```bash
   curl http://localhost:8000/health/live
   ```

### Out of Memory

If services are running out of memory:

1. Check resource usage:
   ```bash
   docker stats
   ```

2. Adjust memory limits in `docker-compose.prod.yml`

3. Restart with new limits:
   ```bash
   docker-compose down
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Network Issues

If services can't communicate:

1. Check network:
   ```bash
   docker network ls | grep chimera
   docker network inspect chimera-network
   ```

2. Verify service URLs (use service names, not localhost):
   ```bash
   # Correct
   OPENCLAW_ORCHESTRATOR_URL=http://openclaw-orchestrator:8000

   # Wrong
   OPENCLAW_ORCHESTRATOR_URL=http://localhost:8000
   ```

### Kafka Connection Issues

Kafka takes time to start. If services fail to connect:

1. Wait for Kafka to be healthy:
   ```bash
   docker-compose ps kafka
   ```

2. Check Kafka logs:
   ```bash
   docker-compose logs kafka
   ```

3. Test connection:
   ```bash
   docker-compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
   ```

## Production Deployment

For production deployment:

1. Update environment variables in `.env.docker`:
   ```bash
   ENVIRONMENT=production
   GRAFANA_ADMIN_PASSWORD=<secure-password>
   ```

2. Use production compose file:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. Configure external access (reverse proxy, load balancer)

4. Set up log aggregation and monitoring

5. Configure backup for persistent volumes

## Monitoring and Observability

### Metrics

All services expose Prometheus-compatible metrics at `/metrics`:

- Request counts and latencies
- Error rates
- Custom business metrics

View in Grafana: http://localhost:3000

### Tracing

All services send traces to Jaeger:

- Distributed request tracing
- Service dependency map
- Performance analysis

View in Jaeger UI: http://localhost:16686

### Logs

View logs for all services:

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs -f openclaw-orchestrator

# Last 100 lines
docker-compose logs --tail=100
```

## Best Practices

1. **Always use the scripts** - Use `docker-start.sh`, `docker-stop.sh`, `docker-status.sh` instead of direct `docker-compose` commands
2. **Check service health** - Use `docker-status.sh` before starting work
3. **Monitor resources** - Keep an eye on memory usage with `docker stats`
4. **Clean up regularly** - Use `--clean` flag when stopping to free up disk space
5. **Use dev mode for development** - Hot-reload saves time
6. **Use prod mode for demos** - More stable and production-like

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Service Documentation](../services/README.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Development Guide](../docs/DEVELOPMENT.md)
