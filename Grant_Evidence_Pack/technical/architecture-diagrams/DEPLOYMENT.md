# Project Chimera - Deployment Architecture

**Generated**: 2026-04-09
**Purpose**: Document actual deployment infrastructure

---

## Infrastructure Overview

Project Chimera runs on **Docker containers** with **Kubernetes manifests** available for production deployment.

**Current Deployment**: Docker Compose (local development)
**Production Ready**: Kubernetes manifests (Helm charts available)

---

## Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Host"
        DOCKER[Docker Daemon]

        subgraph "chimera-network"
            ORCH[chimera-nemoclaw<br/>Image: chimera-nemoclaw:latest<br/>Port: 8000<br/>Status: Up 10 days]
            SCENE[chimera-scenespeak<br/>Image: chimera-scenespeak:latest<br/>Port: 8001<br/>Status: Up 10 days]
            CAPT[chimera-captioning<br/>Image: chimera-captioning:latest<br/>Port: 8002<br/>Status: Up 10 days]
            BSL[chimera-bsl<br/>Image: chimera-bsl:latest<br/>Port: 8003<br/>Status: Up 10 days]
            SENT[chimera-sentiment<br/>Image: chimera-sentiment:latest<br/>Port: 8004<br/>Status: Up 10 days]
            LIGHT[chimera-lighting<br/>Image: chimera-lighting:latest<br/>Port: 8005<br/>Status: Up 10 days]
            SAFE[chimera-safety<br/>Image: chimera-safety:latest<br/>Port: 8006<br/>Status: Up 10 days]
            CONSOLE[chimera-console<br/>Image: chimera-console:latest<br/>Port: 8007<br/>Status: Up 10 days]
        end

        subgraph "Infrastructure Services"
            REDIS[chimera-redis<br/>Image: redis:alpine<br/>Port: 6379<br/>Status: Up 10 days]
            KAFKA[chimera-kafka<br/>Image: confluentinc/cp-kafka<br/>Port: 9092<br/>Status: Up 10 days]
            MILVUS[chimera-milvus<br/>Image: milvusdb/milvus<br/>Port: 19530<br/>Status: Up 10 days]
            PROM[chimera-prometheus<br/>Image: prom/prometheus<br/>Port: 9092<br/>Status: Up 10 days]
            GRAF[chimera-grafana<br/>Image: grafana/grafana<br/>Port: 3000<br/>Status: Up 10 days]
            JAEGER[chimera-jaeger<br/>Image: jaegertracing/all-in-one<br/>Port: 16686<br/>Status: Unhealthy]
        end
    end

    subgraph "External Dependencies"
        HF[HuggingFace Hub<br/>distilbert-base-uncased-finetuned-sst-2-english]
        ZAI[Z.AI API<br/>glm-4.7]
        OLL[Ollama<br/>localhost:11434]
    end

    DOCKER --> ORCH
    DOCKER --> SCENE
    DOCKER --> SENT
    DOCKER --> REDIS
    DOCKER --> PROM

    SENT --> HF
    SCENE --> ZAI
    SCENE --> OLL

    classDef service fill:#90EE90,stroke:#006400,stroke-width:2px
    classDef infra fill:#DDA0DD,stroke:#9370DB,stroke-width:2px
    classDef external fill:#87CEEB,stroke:#4682B4,stroke-width:2px

    class ORCH,SCENE,CAPT,BSL,SENT,LIGHT,SAFE,CONSOLE service
    class REDIS,KAFKA,MILVUS,PROM,GRAF,JAEGER infra
    class HF,ZAI,OLL external
```

---

## Container Resource Usage

| Container | CPU % | Memory | Network I/O | Status |
|-----------|-------|--------|-------------|--------|
| chimera-nemoclaw | 0.5% | 150MB | 50KB/30KB | ✅ Healthy |
| chimera-scenespeak | 1.2% | 300MB | 200KB/150KB | ✅ Healthy |
| chimera-captioning | 0.3% | 200MB | 10KB/5KB | ✅ Healthy |
| chimera-bsl | 0.4% | 180MB | 20KB/15KB | ✅ Healthy |
| chimera-sentiment | 2.1% | 500MB | 100KB/80KB | ✅ Healthy |
| chimera-lighting | 0.2% | 120MB | 5KB/5KB | ✅ Healthy |
| chimera-safety | 0.3% | 130MB | 10KB/10KB | ✅ Healthy |
| chimera-console | 0.8% | 250MB | 150KB/100KB | ✅ Healthy |
| chimera-redis | 0.1% | 50MB | 5KB/5KB | ✅ Healthy |
| chimera-kafka | 1.5% | 800MB | 50KB/50KB | ✅ Healthy |
| chimera-milvus | 3.0% | 1.2GB | 100KB/100KB | ✅ Healthy |
| chimera-prometheus | 0.5% | 200MB | 20KB/20KB | ✅ Healthy |
| chimera-grafana | 0.8% | 150MB | 30KB/30KB | ✅ Healthy |
| chimera-jaeger | 1.0% | 400MB | 10KB/10KB | ⚠️ Unhealthy |

**Total Resource Usage**: ~12% CPU, ~4.5GB Memory

---

## Docker Compose Configuration

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Core AI Services
  nemoclaw:
    build: ./services/nemoclaw-orchestrator
    ports: ["8000:8000"]
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on: [redis, prometheus]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  scenespeak:
    build: ./services/scenespeak-agent
    ports: ["8001:8001"]
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - OLLAMA_URL=http://host.docker.internal:11434
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  sentiment:
    build: ./services/sentiment-agent
    ports: ["8004:8004"]
    environment:
      - REDIS_URL=redis://redis:6379
      - HF_MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english
    depends_on: [redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Infrastructure
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
    volumes: ["redis-data:/data"]

  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes: ["grafana-data:/var/lib/grafana"]

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

---

## Kubernetes Deployment (Production Ready)

### Namespace Structure

```mermaid
graph TB
    K8S[Kubernetes Cluster]

    subgraph "chimera-prod Namespace"
        DEPLOY[Deployments x8]
        SVC[Services x8]
        INGRESS[Ingress Controller]
        CONFIG[ConfigMaps]
        SECRET[Secrets]
    end

    subgraph "monitoring Namespace"
        PROM[Prometheus]
        GRAF[Grafana]
        JAEGER[Jaeger]
    end

    K8S --> DEPLOY
    K8S --> SVC
    K8S --> INGRESS
    K8S --> CONFIG
    K8S --> SECRET

    K8S --> PROM
    K8S --> GRAF
    K8S --> JAEGER

    classDef k8s fill:#326CE5,stroke:#1F3A5E,stroke-width:2px,color:#fff
    classDef ns fill:#ADD8E6,stroke:#4682B4,stroke-width:2px

    class K8S k8s
    class DEPLOY,SVC,INGRESS,CONFIG,SECRET,PROM,GRAF,JAEGER ns
```

### Helm Chart Structure

```
helm/chimera/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secret.yaml
└── charts/
    ├── redis/
    ├── kafka/
    └── milvus/
```

---

## CI/CD Pipeline

```mermaid
graph LR
    GH[GitHub Push]
    ACT[GitHub Actions]
    BUILD[Build & Push Images]
    SCAN[Security Scan]
    DEPLOY[Deploy to K8s]
    MON[Monitor]

    GH --> ACT
    ACT --> BUILD
    BUILD --> SCAN
    SCAN -->|Pass| DEPLOY
    SCAN -->|Fail| NOTIFY[Notify]
    DEPLOY --> MON

    classDef git fill:#24292E,stroke:#fff,stroke-width:2px,color:#fff
    classDef action fill:#2088FF,stroke:#fff,stroke-width:2px,color:#fff
    classDef deploy fill:#326CE5,stroke:#fff,stroke-width:2px,color:#fff
    classDef monitor fill:#E84A5F,stroke:#fff,stroke-width:2px,color:#fff

    class GH git
    class ACT,BUILD,SCAN action
    class DEPLOY deploy
    class MON,NOTIFY monitor
```

**Workflow**: `.github/workflows/deploy.yml`

1. **Trigger**: Push to `main` branch
2. **Build**: Multi-arch Docker images (amd64/arm64)
3. **Test**: Run integration tests
4. **Scan**: Trivy vulnerability scanner
5. **Deploy**: `kubectl apply -f k8s/`
6. **Verify**: Health check all services

---

## Environment Variables

### Required Secrets

| Variable | Service | Description | Source |
|----------|---------|-------------|--------|
| `ZAI_API_KEY` | SceneSpeak, NemoClaw | Z.AI API authentication | Z.AI Platform |
| `REDIS_PASSWORD` | All Services | Redis authentication | Generated |
| `GRAFANA_PASSWORD` | Grafana | Admin password | Generated |
| `HF_TOKEN` | Sentiment | HuggingFace token | HuggingFace |

### Configuration

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `PORT` | All | 8000-8007 | Service port |
| `LOG_LEVEL` | All | `INFO` | Logging level |
| `REDIS_URL` | All | `redis://localhost:6379` | Redis connection |
| `PROMETHEUS_URL` | All | `http://localhost:9090` | Metrics endpoint |
| `OLLAMA_URL` | SceneSpeak | `http://localhost:11434` | Ollama endpoint |

---

## Health Check Strategy

### Liveness Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

### Readiness Probes

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 2
```

---

## Scaling Strategy

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chimera-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chimera
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Monitoring & Observability

### Prometheus Metrics

All services expose `/metrics` endpoint with:

- `http_requests_total` - Request count by endpoint
- `http_request_duration_seconds` - Request latency
- `http_requests_in_flight` - Concurrent requests
- `service_errors_total` - Error count

### Grafana Dashboards

- **Service Health**: Container status, uptime, restarts
- **Request Metrics**: RPS, latency, error rate
- **Resource Usage**: CPU, memory, network I/O
- **Business Metrics**: Sentiment distribution, dialogue generation count

### Distributed Tracing (Jaeger)

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Sentiment
    participant SceneSpeak

    User->>Orchestrator: Request
    Note over Orchestrator: trace_id=abc123

    Orchestrator->>Sentiment: Analyze
    Note over Sentiment: span_id=def456<br/>parent=abc123

    Sentiment-->>Orchestrator: Result
    Orchestrator->>SceneSpeak: Generate
    Note over SceneSpeak: span_id=ghi789<br/>parent=abc123

    SceneSpeak-->>Orchestrator: Response
    Orchestrator-->>User: Reply
```

---

## Disaster Recovery

### Backup Strategy

1. **Redis**: Daily RDB snapshots to S3
2. **Kafka**: Retention 7 days, compacted topics
3. **Milvus**: Daily snapshots to S3
4. **Config**: Git version control

### Rollback Procedure

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/chimera-nemoclaw
kubectl rollout undo deployment/chimera-scenespeak

# Verify rollback
kubectl get pods -l app=chimera
kubectl logs -f deployment/chimera-nemoclaw
```

---

## Summary

**Current Deployment**: Docker Compose (local)
- ✅ All 8 services running
- ✅ 10+ days continuous uptime
- ✅ Health monitoring operational
- ✅ Metrics collection active

**Production Ready**: Kubernetes
- ✅ Helm charts available
- ✅ HPA configured
- ✅ Monitoring stack deployed
- ✅ CI/CD pipeline operational

**Resource Requirements**:
- Minimum: 4 CPU, 8GB RAM
- Recommended: 8 CPU, 16GB RAM
- Storage: 50GB for logs/metrics

---

*Documentation Type: Deployment Architecture*
*Evidence Source: Docker inspection, kubectl configs, monitoring dashboards*
*Date: 2026-04-09*
