# Music Platform Deployment Guide

## Prerequisites
- k3s cluster
- PostgreSQL database
- Redis
- MinIO
- NVIDIA GPU (for generation service)

## Local Deployment

```bash
# Create database
createdb chimera_music

# Run migrations
psql chimera_music < services/music-orchestration/migrations/001_create_music_tables.sql

# Start services
cd services/music-generation
uvicorn music_generation.main:app --host 0.0.0.0 --port 8011

cd services/music-orchestration
uvicorn music_orchestration.main:app --host 0.0.0.0 --port 8012
```

## Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace chimera

# Create secrets
kubectl create secret generic chimera-secrets \
  --from-literal=database-url='postgresql+asyncpg://user:pass@postgres/chimera_music' \
  --from-literal=redis-url='redis://redis:6379/0' \
  --from-literal=jwt-secret='your-secret' \
  -n chimera

# Apply manifests
kubectl apply -f services/music-generation/manifests/ -n chimera
kubectl apply -f services/music-orchestration/manifests/ -n chimera

# Verify
kubectl get pods -n chimera
```
