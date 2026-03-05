# Deployment Guide

**Version:** 0.4.0
**Last Updated:** March 2026

---

## Overview

This guide covers deploying Project Chimera to various environments, from local development with k3s to production Kubernetes clusters.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Local Deployment (k3s)](#local-deployment-k3s)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Linux (Ubuntu 22.04) | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 50 GB | 100+ GB SSD |
| GPU | - | NVIDIA GPU (for AI features) |

### Software Requirements

- **Kubernetes:** 1.25+ (k3s for local, standard k8s for production)
- **kubectl:** Matching cluster version
- **Helm:** 3.0+ (for production deployments)
- **Python:** 3.10+
- **Docker:** 20.10+

### External Dependencies

- **PostgreSQL:** 16+ (can be deployed via Helm)
- **Redis:** 7+ (can be deployed via Helm)
- **Milvus:** 2.3+ (vector database)

---

## Deployment Options

### 1. Local Development (k3s)

**Best for:** Development, testing, demos

**Pros:**
- Lightweight, single-node Kubernetes
- Quick setup (< 15 minutes)
- Minimal resource requirements

**Cons:**
- Not production-ready
- Single point of failure

### 2. Production Kubernetes

**Best for:** Production staging, production

**Pros:**
- High availability
- Scalability
- Production-ready

**Cons:**
- More complex setup
- Requires infrastructure

---

## Local Deployment (k3s)

### Automated Bootstrap

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera

# Run the bootstrap script
make bootstrap
```

**This automatically:**
1. Installs k3s
2. Sets up local container registry
3. Builds all service Docker images
4. Deploys infrastructure (Redis, Kafka, Milvus)
5. Deploys monitoring (Prometheus, Grafana, Jaeger, AlertManager)
6. Deploys all AI agents

### Manual Bootstrap Steps

If you prefer manual setup:

#### 1. Install k3s

```bash
curl -sfL https://get.k3s.io | sh -
```

#### 2. Verify k3s Installation

```bash
kubectl get nodes
# Expected: Single node named "chimera-control-plane" Ready
```

#### 3. Deploy Infrastructure

```bash
kubectl apply -f platform/deployment/redis/
kubectl apply -f platform/deployment/kafka/
kubectl apply -f platform/deployment/milvus/
```

#### 4. Deploy Monitoring Stack

```bash
kubectl apply -f platform/monitoring/config/prometheus/
kubectl apply -f platform/monitoring/config/grafana/
kubectl apply -f platform/monitoring/config/alertmanager/
```

#### 5. Build and Deploy Services

```bash
# Build all service images
make build

# Deploy all services
kubectl apply -f platform/deployment/services/
```

#### 6. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n live

# Expected output: All pods in Running state
```

---

## Production Deployment

### Using Helm Charts

Project Chimera includes Helm charts for production deployment:

#### 1. Add Chart Dependencies

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

#### 2. Create Namespace

```bash
kubectl create namespace chimera-prod
```

#### 3. Install Infrastructure

```bash
# PostgreSQL
helm install chimera-postgres bitnami/postgresql \
  --namespace chimera-prod \
  --set auth.password=your-password \
  --set primary.persistence.size=50Gi

# Redis
helm install chimera-redis bitnami/redis \
  --namespace chimera-prod \
  --set auth.enabled=true \
  --set master.persistence.size=20Gi

# Kafka
helm install chimera-kafka bitnami/kafka \
  --namespace chimera-prod \
  --set replicas=3 \
  --set persistence.size=100Gi
```

#### 4. Deploy Monitoring Stack

```bash
# Prometheus
helm install chimera-prometheus prometheus-community/kube-prometheus-stack \
  --namespace chimera-prod \
  --values platform/deployment/helm/prometheus-values.yaml

# Grafana dashboards
kubectl apply -f platform/monitoring/config/grafana-dashboards/
```

#### 5. Deploy Project Chimera Services

```bash
helm install chimera platform/deployment/helm/project-chimera \
  --namespace chimera-prod \
  --values platform/deployment/helm/production-values.yaml
```

### Production Values Example

```yaml
# platform/deployment/helm/production-values.yaml

replicaCount:
  openclaw: 3
  scenespeak: 3
  captioning: 2
  bsl: 2
  sentiment: 2
  lighting: 1
  safety: 3
  console: 2

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# SLO-based quality gate
qualityGate:
  enabled: true
  sloThreshold: 0.95
  errorBudgetThreshold: 0.10

# Observability
telemetry:
  enabled: true
  sampling: 0.10
  exporter: otlp
  endpoint: http://jaeger-collector:4317
```

---

## Configuration

### Environment Variables

Key environment variables for production:

```yaml
# Database
DATABASE_URL: postgresql://user:pass@postgres-service:5432/chimera
REDIS_URL: redis://redis-service:6379

# Monitoring
PROMETHEUS_URL: http://prometheus:9090
JAEGER_ENDPOINT: http://jaeger-collector:4317

# SLO Configuration
SLO_WINDOW_DAYS: 30
ERROR_BUDGET_THRESHOLD: 0.10

# Feature Flags
ENABLE_TELEMETRY: "true"
ENABLE_TRACING: "true"
SAMPLING_RATE: "0.10"
```

### Secrets Management

Use Kubernetes secrets for sensitive data:

```bash
# Create secret for database credentials
kubectl create secret generic chimera-db-secret \
  --from-literal=username=chimera \
  --from-literal=password=secure-password \
  --namespace chimera-prod

# Create secret for API keys
kubectl create secret generic chimera-api-keys \
  --from-literal=openai-api-key=sk-... \
  --namespace chimera-prod
```

---

## Monitoring & Observability

### Access Monitoring Tools

| Tool | URL | Credentials |
|------|-----|-------------|
| Grafana | `http://<ingress>/grafana` | admin/admin (change on first login) |
| Prometheus | `http://<ingress>/prometheus` | Basic auth |
| AlertManager | `http://<ingress>/alertmanager` | Basic auth |
| Jaeger | `http://<ingress>/jaeger` | - |

### Key Metrics to Monitor

**Service Health:**
- `up{job="chimera-services"}` - Service availability
- `rate(http_requests_total{status=~"5.."}[5m])` - Error rate

**Business Metrics:**
- `scenespeak_lines_generated_total` - Dialogue lines
- `sentiment_audience_avg` - Audience sentiment
- `captioning_latency_seconds` - Caption timing
- `bsl_active_sessions` - BSL avatar sessions

**SLO Metrics:**
- `slo:*_success_rate:30d` - SLO compliance
- `slo:error_budget_remaining:30d` - Error budget
- `slo:error_burn_rate` - Burn rate

### Alerting

Alerts are configured in `platform/monitoring/config/alert-rules-critical.yaml`:

- **Critical alerts** fire immediately and route to on-call
- **Warning alerts** aggregate and send daily digests
- **SLO alerts** trigger on burn rate thresholds

See [Alerting Runbook](docs/runbooks/alerts.md) for alert response procedures.

---

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n live

# Describe pod for events
kubectl describe pod <pod-name> -n live

# Check logs
kubectl logs <pod-name> -n live --follow
```

#### Service Not Reachable

```bash
# Check service endpoints
kubectl get endpoints -n live

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://service-name:port/health
```

#### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n live

# Check node resources
kubectl top nodes
```

### Debug Commands

```bash
# Port forward to local service
kubectl port-forward svc/scenespeak-agent 8001:8001 -n live

# Exec into container
kubectl exec -it <pod-name> -n live -- /bin/bash

# Check events
kubectl get events -n live --sort-by='.lastTimestamp'
```

### Health Check All Services

```bash
# Core services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done

# Platform services
for port in 8010 8011 8012 8013; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done
```

---

## Rollback Procedures

### Rollback Helm Release

```bash
# List releases
helm list -n chimera-prod

# Check revision history
helm history chimera -n chimera-prod

# Rollback to previous revision
helm rollback chimera -n chimera-prod

# Rollback to specific revision
helm rollback chimera <revision> -n chimera-prod
```

### Rollback Kubernetes Deployment

```bash
# Check rollout history
kubectl rollout history deployment/scenespeak-agent -n live

# Rollback to previous revision
kubectl rollout undo deployment/scenespeak-agent -n live

# Rollback to specific revision
kubectl rollout undo deployment/scenespeak-agent -n live --to-revision=2
```

### Emergency Rollback

If a deployment causes critical issues:

1. **Immediately scale to zero:**
   ```bash
   kubectl scale deployment/<deployment> --replicas=0 -n live
   ```

2. **Restore from backup:**
   ```bash
   kubectl apply -f backup/<previous-version>/deployment.yaml
   ```

3. **Verify health:**
   ```bash
   kubectl get pods -n live
   ./scripts/health-check-all.sh
   ```

---

## Additional Resources

- [Quick Start Guide](docs/getting-started/quick-start.md) - Development environment setup
- [Monitoring Runbook](docs/runbooks/monitoring.md) - Monitoring procedures
- [Incident Response](docs/runbooks/incident-response.md) - Handling incidents
- [Architecture Documentation](docs/architecture/) - System design
- [Observability Guide](docs/observability.md) - Production observability

---

**Need help?** Check out our [FAQ](docs/getting-started/faq.md) or [Office Hours](docs/getting-started/office-hours.md).
