# Deployment Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 16
- Redis 7
- k3s cluster (optional, for containerized deployment)

## Deploy Platform Services

### Local Development

```bash
cd platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb chimera_quality
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/chimera_quality"

# Start services
uvicorn orchestrator.main:orchestrator_app --host 0.0.0.0 --port 8008 --reload
uvicorn dashboard.main:dashboard_app --host 0.0.0.0 --port 8009 --reload
uvicorn ci_gateway.main:ci_gateway_app --host 0.0.0.0 --port 8010 --reload
```

### k3s Deployment

```bash
# Apply platform manifests
kubectl apply -f platform/manifests/

# Wait for services to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment -n chimera-quality -l app=chimera-quality

# Port forward to access services
kubectl port-forward -n chimera-quality svc/orchestrator 8008:8008
kubectl port-forward -n chimera-quality svc/dashboard 8009:8009
kubectl port-forward -n chimera-quality svc/ci-gateway 8010:8010
```

## Configure Webhooks

### GitHub

1. Go to repository Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/github`
3. Secret: Generate a secure random string
4. Set environment variable: `GITHUB_WEBHOOK_SECRET`
5. Events: Push, Pull requests

### GitLab

1. Go to Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/gitlab`
3. Secret: Generate a secure random string
4. Set environment variable: `GITLAB_WEBHOOK_SECRET`
5. Events: Push events, Merge request events

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | - |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| GITHUB_WEBHOOK_SECRET | GitHub webhook secret | - |
| GITHUB_TOKEN | GitHub API token | - |
| DASHBOARD_URL | Dashboard URL | http://localhost:8000 |
| MAX_WORKERS | Max parallel workers | 16 |
| MIN_COVERAGE_THRESHOLD | Min coverage % | 95.0 |
