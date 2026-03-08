# TRD #006: K3s Production Deployment

**Date:** 2026-03-07
**Status:** Draft
**Priority:** HIGH (Production Readiness)

## Overview

Define the Kubernetes (K3s) deployment strategy for Project Chimera on ARM64 GB10 GPU hardware.

## Current State Analysis

### Existing Infrastructure

**✅ Has Complete Manifest:**
- `services/music-generation/manifests/k8s.yaml` (238 lines)
  - ConfigMap, Service, PersistentVolumeClaim, Deployment
  - HorizontalPodAutoscaler, PodDisruptionBudget
  - GPU scheduling for `NVIDIA_GB10`
  - Namespace: `project-chimera`

**✅ Has Monitoring Config:**
- `infrastructure/kubernetes/prometheus/configmap.yaml`
  - Service discovery for all 8 agents
  - Exporters: kafka, postgres, redis, node
  - Namespace: `shared` ⚠️ **INCONSISTENT**

**❌ Missing:**
- Cluster-level resources (namespace, storage-class, ingress)
- K8s manifests for 8 other services
- Infrastructure deployments (Redis, Kafka, Milvus)
- Monitoring stack deployments (Prometheus, Grafana, AlertManager)

## Issues Identified

1. **Namespace Inconsistency:** music-generation uses `project-chimera` but prometheus uses `shared`
2. **Incomplete Service Coverage:** Only 1/9 services has K8s manifests
3. **Missing Infrastructure:** No manifests for Redis, Kafka, Milvus
4. **Missing Monitoring Stack:** Prometheus/Grafana/AlertManager configured but not deployed

## Proposed Architecture

### Namespace Strategy

**Unified Namespace Approach:**
- Single namespace: `project-chimera`
- All services, infrastructure, monitoring in one namespace
- Simplifies service discovery and networking
- Aligns with existing music-generation manifest

### Cluster-Level Resources

**Create `infrastructure/kubernetes/cluster/` with:**
1. `namespace.yaml` - project-chimera namespace
2. `storage-class.yaml` - NFS storage class for model caches
3. `network-policy.yaml` - Network isolation rules
4. `resource-quota.yaml` - Resource limits per namespace

### Service Manifests Pattern

**Follow existing music-generation pattern:**
```
services/<service>/manifests/k8s.yaml
├── ConfigMap (environment config)
├── Service (ClusterIP)
├── PersistentVolumeClaim (if needed)
├── Deployment (with probes, resources, affinity)
├── HorizontalPodAutoscaler (optional)
└── PodDisruptionBudget
```

## Component Specifications

### 1. Cluster-Level Resources

#### namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: project-chimera
  labels:
    name: project-chimera
    environment: production
```

#### storage-class.yaml
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-sc
provisioner: nfs.csi.k8s.io
parameters:
  server: 10.0.0.10  # NFS server IP
  share: /export/k3s-storage
reclaimPolicy: Retain
volumeBindingMode: Immediate
```

#### network-policy.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: project-chimera-netpol
  namespace: project-chimera
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8000  # Orchestrator
    - protocol: TCP
      port: 8001  # SceneSpeak
    # ... all service ports
  egress:
  - to:
    - namespaceSelector: {}
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53  # DNS
```

#### resource-quota.yaml
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: project-chimera-quota
  namespace: project-chimera
spec:
  hard:
    requests.cpu: "16"
    requests.memory: "32Gi"
    requests.nvidia.com/gpu: "4"
    limits.cpu: "64"
    limits.memory: "128Gi"
    limits.nvidia.com/gpu: "4"
    persistentvolumeclaims: "10"
```

### 2. Service Manifests (8 Remaining)

#### GPU Services (need GPU scheduling)
1. **SceneSpeak Agent** (8001) - ARM64 GB10 GPU
2. **Captioning Agent** (8002) - ARM64 GB10 GPU
3. **BSL Agent** (8003) - ARM64 GB10 GPU

#### CPU Services (no GPU required)
4. **OpenClaw Orchestrator** (8000) - CPU only
5. **Sentiment Agent** (8004) - CPU only (DistilBERT small)
6. **Lighting Control** (8005) - CPU only
7. **Safety Filter** (8006) - CPU only
8. **Operator Console** (8007) - CPU only

### 3. Infrastructure Deployments

#### Redis
```yaml
# StatefulSet with 1 replica
# Port: 6379
# Storage: 5Gi PVC
# Resources: 500m CPU, 1Gi memory
```

#### Kafka
```yaml
# StatefulSet with 1 replica (production: 3)
# Port: 9092
# Storage: 20Gi PVC
# Resources: 1000m CPU, 2Gi memory
```

#### Milvus
```yaml
# Deployment with etcd, MinIO, coord services
# Port: 19530
# Storage: 50Gi PVC
# Resources: 2000m CPU, 4Gi memory
```

### 4. Monitoring Stack

#### Prometheus
```yaml
# Deployment with PVC for TSDB
# Port: 9090
# Storage: 50Gi PVC
# Resources: 2000m CPU, 4Gi memory
# Uses existing configmap.yaml
```

#### Grafana
```yaml
# Deployment with PVC for dashboards
# Port: 3000
# Storage: 10Gi PVC
# Resources: 500m CPU, 1Gi memory
# ConfigMap for datasource provisioning
```

#### AlertManager
```yaml
# Deployment with PVC
# Port: 9093
# Storage: 5Gi PVC
# Resources: 500m CPU, 1Gi memory
# Uses existing configmap.yaml
```

## Deployment Order

1. **Cluster Setup**
   - namespace.yaml
   - storage-class.yaml
   - network-policy.yaml
   - resource-quota.yaml

2. **Infrastructure**
   - Redis
   - Kafka
   - Milvus

3. **Monitoring**
   - Prometheus
   - Grafana
   - AlertManager

4. **Services** (dependency order)
   - Orchestrator (8000)
   - SceneSpeak (8001) - GPU
   - Captioning (8002) - GPU
   - BSL (8003) - GPU
   - Sentiment (8004)
   - Lighting (8005)
   - Safety (8006)
   - Console (8007)
   - Music Generation (8011) - GPU (already exists)

## GPU Scheduling Strategy

### ARM64 GB10 GPU Node Affinity
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: nvidia.com/gpu.product
          operator: In
          values:
          - NVIDIA_GB10
        - key: nvidia.com/gpu.count
          operator: Gt
          values:
          - "0"
```

### Resource Limits for GPU Services
```yaml
resources:
  requests:
    nvidia.com/gpu: "1"
    cpu: "2000m"
    memory: "4Gi"
  limits:
    nvidia.com/gpu: "1"
    cpu: "8000m"
    memory: "16Gi"
```

## Health Check Strategy

### Liveness Probes
- Path: `/health/live`
- Initial delay: 30s
- Period: 30s
- Timeout: 5s
- Failure threshold: 3

### Readiness Probes
- Path: `/health/ready`
- Initial delay: 60s (models take time to load)
- Period: 10s
- Timeout: 5s
- Failure threshold: 3

### Startup Probes
- Path: `/health/live`
- Initial delay: 10s
- Period: 10s
- Timeout: 5s
- Failure threshold: 30 (5 min grace period)

## Migration Strategy

### Phase 1: Namespace Unification
1. Update prometheus configmap from `shared` to `project-chimera`
2. Test in staging environment

### Phase 2: Service Rollout
1. Create cluster-level resources
2. Deploy infrastructure (Redis, Kafka, Milvus)
3. Deploy monitoring stack
4. Roll out service manifests (1-2 per day)

### Phase 3: Validation
1. Health check all deployments
2. Verify service-to-service communication
3. Test GPU scheduling
4. Load testing with Locust

## Success Criteria

- [ ] All 9 services have complete k8s manifests
- [ ] Infrastructure deployed and functional
- [ ] Monitoring stack operational
- [ ] GPU services scheduled on GB10 nodes
- [ ] Health checks passing for all services
- [ ] Network policies enforce isolation
- [ ] Resource quotas prevent overcommit
- [ ] Storage provisioned via NFS
- [ ] End-to-end show workflow tested

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GPU node shortage | High | Implement node affinities and limits |
| Storage bottlenecks | Medium | Use ReadWriteMany PVCs, monitor capacity |
| Network isolation blocking traffic | High | Thorough netpol testing in staging |
| Namespace migration breakage | High | Deploy fresh namespace, cutover via DNS |
| K3s version incompatibility | Medium | Pin to specific K3s version in docs |

## Open Questions

1. **NFS Server:** Is there an existing NFS server or should we deploy one?
2. **Ingress:** Do we need an Ingress controller for external access?
3. **TLS:** Should we enable TLS for inter-service communication?
4. **Backup Strategy:** How do we backup PVCs (models, configs)?

## Next Steps

1. Answer open questions
2. Create cluster-level resource files
3. Generate service manifests for 8 remaining services
4. Create deployment script (`scripts/deploy-k3s.sh`)
5. Write deployment runbook in `docs/runbooks/k3s-deployment.md`

---

**TRD Owner:** Infrastructure Team
**Review Date:** 2026-03-07
**Target Completion:** 2026-03-14
