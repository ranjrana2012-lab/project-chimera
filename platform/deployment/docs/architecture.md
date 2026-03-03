# Deployment Architecture

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

This document defines the deployment architecture for Project Chimera on k3s Kubernetes cluster running on NVIDIA DGX Spark hardware.

---

## Cluster Configuration

### k3s Single-Node Setup

**Hardware:**
- **Node:** NVIDIA DGX Spark (GB10-Arm64)
- **RAM:** 128 GB
- **GPU:** 8x NVIDIA A100 40GB (pass-through configured)
- **Storage:** Local NVMe for container images and PVs

**k3s Configuration:**
```yaml
# /etc/rancher/k3s/config.yaml
write-kubeconfig-mode: "0644"
tls-san:
  - dgx-spark.local
  - k3s.local
disable:
  - traefik  # We use ingress-nginx
  - servicelb
node-name: dgx-spark
```

### Namespaces

| Namespace | Purpose | Resource Quota |
|-----------|---------|----------------|
| `live` | Production workloads | 80 CPU, 96GB RAM, 7 GPU |
| `preprod` | Pre-production testing | 40 CPU, 48GB RAM, 1 GPU |
| `shared` | Shared services (Redis, Kafka, monitoring) | 20 CPU, 24GB RAM, 0 GPU |
| `platform` | Quality platform services | 10 CPU, 12GB RAM, 0 GPU |

---

## Service Placement Strategy

### GPU-Required Services

| Service | Namespace | GPU Request | GPU Limit | Priority |
|---------|-----------|-------------|-----------|----------|
| scenespeak-agent | live | 1 | 2 | P1 |
| bsl-agent | live | 1 | 1 | P1 |
| captioning-agent | live | 0.5 | 1 | P1 |
| sentiment-agent | live | 0.5 | 1 | P2 |
| openclaw-orchestrator | live | 2 | 4 | P1 |

### CPU-Only Services

| Service | Namespace | CPU Request | Memory Request | Replicas |
|---------|-----------|-------------|----------------|----------|
| lighting-service | live | 500m | 512Mi | 1 |
| safety-filter | live | 1000m | 1Gi | 2 |
| operator-console | live | 500m | 512Mi | 1 |
| redis | shared | 500m | 1Gi | 1 |
| kafka | shared | 1000m | 2Gi | 1 |
| prometheus | shared | 500m | 1Gi | 1 |
| grafana | shared | 200m | 256Mi | 1 |

### Platform Services

| Service | Namespace | CPU Request | Memory Request | Replicas |
|---------|-----------|-------------|----------------|----------|
| test-orchestrator | platform | 1000m | 1Gi | 1 |
| dashboard-service | platform | 500m | 512Mi | 1 |
| cicd-gateway | platform | 500m | 512Mi | 1 |
| quality-gate | platform | 500m | 512Mi | 1 |

---

## Networking Architecture

### Ingress Configuration

**Ingress Controller:** ingress-nginx

**Ingress Class:** nginx

```yaml
# Ingress architecture
Internet/Network
    |
    v
[ingress-nginx] :80, :443 (shared namespace)
    |
    +---> /api/scenespeak -> scenespeak-agent:8001 (live)
    +---> /api/captioning -> captioning-agent:8002 (live)
    +---> /api/bsl -> bsl-agent:8003 (live)
    +---> /api/sentiment -> sentiment-agent:8004 (live)
    +----- /api/lighting -> lighting-service:8005 (live)
    +----- /api/safety -> safety-filter:8006 (live)
    +----- /console -> operator-console:8007 (live)
    +----- /openclaw -> openclaw-orchestrator:8000 (live)
    +----- /dashboard -> dashboard-service:8010 (platform)
    +----- /orchestrator -> test-orchestrator:8011 (platform)
    +----- /cicd -> cicd-gateway:8012 (platform)
```

### Service Discovery

**DNS Pattern:** `<service-name>.<namespace>.svc.cluster.local`

**Internal Services:**
- All services communicate via Kubernetes DNS
- Cross-namespace communication allowed via network policies
- External access only via ingress

### Network Policies

**Default:** Deny all ingress/egress

**Allowed Flows:**
1. Ingress → all services (namespace-specific)
2. Services → Redis, Kafka (shared)
3. Services → Prometheus (metrics scraping)
4. All → OpenClaw (orchestration)

---

## Storage Architecture

### Persistent Volume Claims

| PVC | Storage Class | Size | Access Mode | Used By |
|-----|---------------|------|-------------|---------|
| `redis-data` | local-path | 10Gi | RWO | redis |
| `kafka-data` | local-path | 50Gi | RWO | kafka |
| `openclaw-workspace` | local-path | 100Gi | RWO | openclaw-orchestrator |
| `model-cache` | local-path | 200Gi | RWX | All agents |
| `test-history` | local-path | 20Gi | RWO | test-orchestrator |
| `coverage-reports` | local-path | 10Gi | RWO | test-orchestrator |

### Storage Class Configuration

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
provisioner: rancher.io/local-path
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain
```

---

## Resource Limits

### Cluster-Wide Limits

| Resource | Total | Allocated | Headroom |
|----------|-------|-----------|----------|
| CPU | 80 cores | 49.5 cores (62%) | 30.5 cores |
| Memory | 128 GiB | 105.5 GiB (82%) | 22.5 GiB |
| GPU | 8 | 7 (87.5%) | 1 |

### Namespace Resource Quotas

**live namespace:**
```yaml
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 96Gi
    requests.nvidia.com/gpu: "7"
    limits.cpu: "80"
    limits.memory: 128Gi
    limits.nvidia.com/gpu: "8"
    persistentvolumeclaims: "10"
```

**shared namespace:**
```yaml
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 24Gi
    limits.cpu: "20"
    limits.memory: 32Gi
    persistentvolumeclaims: "5"
```

**platform namespace:**
```yaml
spec:
  hard:
    requests.cpu: "5"
    requests.memory: 12Gi
    limits.cpu: "10"
    limits.memory: 16Gi
    persistentvolumeclaims: "5"
```

---

## Deployment Strategy

### Rolling Updates

**Max Unavailable:** 25%

**Max Surge:** 50%

**Deployment Order:**
1. Platform services (test-orchestrator, dashboard, cicd-gateway, quality-gate)
2. Shared services (redis, kafka, monitoring)
3. CPU-only agents (lighting-service, safety-filter, operator-console)
4. GPU agents (captioning, sentiment, bsl, scenespeak)
5. Orchestrator (openclaw-orchestrator)

### Health Checks

**Liveness Probe:** `/health` - 30s interval, 5s timeout

**Readiness Probe:** `/ready` - 10s interval, 3s timeout

**Startup Probe:** `/health` - 10s interval, 30s timeout, 30 attempts

---

## Security Configuration

### Pod Security Standards

**Baseline:** Restricted

**Requirements:**
- Run as non-root user
- Read-only root filesystem
- Drop all capabilities
- Seccomp profile: runtime/default

### Secrets Management

**Tool:** Sealed Secrets

**Secrets:**
- GitHub webhook secret
- API keys for external services
- Database credentials (if any)

### Network Security

**Ingress:** TLS termination at ingress-nginx

**Internal:** mTLS between services (future enhancement)

---

## Monitoring and Observability

### Metrics Collection

**Prometheus:** Scrapes all services every 15s

**Metrics Exposed:**
- `/metrics` endpoint on all services
- Pod resource usage
- Service performance metrics
- Custom business metrics

### Logging

**Aggregator:** (To be determined - ELK/Loki)

**Log Levels:**
- DEBUG: Development only
- INFO: Production default
- WARNING: Alerts triggered
- ERROR: Immediate notification

### Tracing

**Tool:** (To be determined - Jaeger/Tempo)

**Traced:**
- OpenClaw skill invocations
- Cross-service requests
- Pipeline executions

---

## Disaster Recovery

### Backup Strategy

**What to Backup:**
- Persistent volumes (daily snapshots)
- Kubernetes resources (weekly)
- Configuration (Git)

**Recovery:**
- PV restoration from snapshots
- Resource restoration from Git
- RTO: 4 hours
- RPO: 24 hours

### High Availability

**Single-Node Limitations:**
- No node redundancy (single DGX Spark)
- Pod anti-affinity for critical services
- Replica sets for CPU-only services
- StatefulSets for shared services

---

## Future Enhancements

### Multi-Node Cluster

**Planned Expansion:**
- Second DGX Spark node (200GbE link)
- GPU sharing across nodes
- True high availability

### Cloud Migration Path

**Target Platforms:**
- GKE (Google Kubernetes Engine)
- EKS (Amazon EKS)
- AKS (Azure Kubernetes Service)

**Migration Considerations:**
- Ingress controller compatibility
- Storage class changes
- GPU node pools
- Cost optimization

---

**Status:** ✅ Architecture Defined
**Next Step:** Create Helm charts (Task 4.1.2)
