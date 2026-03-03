# Quality Platform - Deployment Guide

## Prerequisites

- PostgreSQL 16
- Redis 7
- Python 3.11+
- k3s cluster (optional)

## Local Deployment

### Environment Setup

```bash
cd platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Setup

```bash
# Create database
createdb chimera_quality

# Run migrations
python -c "
from platform.shared.database import engine, Base
import asyncio
asyncio.run(engine.connect())
asyncio.run(engine.dispose())
"
```

### Environment Variables

Create `.env` file in platform directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/chimera_quality

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub (optional)
GITHUB_WEBHOOK_SECRET=your-secret-here
GITHUB_TOKEN=your-token-here

# Dashboard
DASHBOARD_URL=http://localhost:8009

# Test Execution
MAX_WORKERS=16
TEST_TIMEOUT_SECONDS=300

# Quality Gates
MIN_COVERAGE_THRESHOLD=95.0
MAX_MUTATION_SURVIVAL=2.0
```

### Start Services

```bash
# Terminal 1: Orchestrator
uvicorn orchestrator.main:orchestrator_app --host 0.0.0.0 --port 8008

# Terminal 2: Dashboard
uvicorn dashboard.main:dashboard_app --host 0.0.0.0 --port 8009

# Terminal 3: CI/CD Gateway
uvicorn ci_gateway.main:ci_gateway_app --host 0.0.0.0 --port 8010
```

### Verify Deployment

```bash
# Check health endpoints
curl http://localhost:8008/health
curl http://localhost:8009/health
curl http://localhost:8010/health

# Should all return: {"status": "healthy", "service": "..."}
```

## Production Deployment

### k3s Deployment

```bash
# Create namespace
kubectl create namespace quality

# Apply manifests
kubectl apply -f platform/manifests/ -n quality

# Verify deployment
kubectl get pods -n quality
kubectl get svc -n quality
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: quality-platform-ingress
  namespace: quality
spec:
  rules:
  - host: quality.chimera.example.com
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: orchestrator
            port:
              number: 8008
```

## Monitoring

### Prometheus Metrics

All services expose `/metrics` endpoint for Prometheus scraping.

### Grafana Dashboards

Import dashboards from `platform/grafana/` directory.

### Health Checks

Services are configured with liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8008
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8008
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Webhook Configuration

### GitHub

1. Go to repository Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/github`
3. Content type: application/json
4. Secret: Use generated webhook secret
5. Events: Push, Pull requests

### GitLab

1. Go to Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/gitlab`
3. Secret: Use generated webhook secret
4. Events: Push events, Merge request events

## Troubleshooting

### Database Issues

**Problem:** Connection refused

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -l | grep chimera_quality
```

**Problem:** Migration errors

```bash
# Drop and recreate database
dropdb chimera_quality
createdb chimera_quality

# Re-run migrations
python -c "from platform.shared.database import Base, engine; import asyncio; asyncio.run(engine.connect());"
```

### Service Issues

**Problem:** Service won't start

```bash
# Check logs
kubectl logs -n quality deployment/<service>

# Check events
kubectl describe pod -n quality <pod-name>
```

**Problem:** Services can't communicate

```bash
# Check services
kubectl get svc -n quality

# Check network policies
kubectl get networkpolicies -n quality
```
