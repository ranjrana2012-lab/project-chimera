# Project Chimera Deployment Guide

This guide covers deploying Project Chimera in various environments, from local development to production clusters.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Scenarios](#deployment-scenarios)
- [Local Deployment](#local-deployment)
- [k3s Deployment](#k3s-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration Management](#configuration-management)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB
- GPU: Optional (for AI features)

**Recommended (Production):**
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 100GB+ SSD
- GPU: NVIDIA GPU with 8GB+ VRAM (for SceneSpeak)

### Software Requirements

- **OS:** Ubuntu 22.04 LTS or macOS 12+
- **Container Runtime:** Docker 24.0+
- **Orchestration:** k3s 1.25+ (lightweight Kubernetes)
- **CLI Tools:**
  - kubectl
  - helm (optional, for charts)
  - make

### Network Requirements

- Ports 8000-8007 available for services
- Port 6443 for k3s API
- Port 3000 for Grafana (optional)
- Port 9090 for Prometheus (optional)

## Deployment Scenarios

### Scenario Matrix

| Scenario | Description | Use Case |
|----------|-------------|----------|
| Local Development | k3s on localhost | Development, testing |
| Single-Node Production | k3s on dedicated server | Small venue deployment |
| Multi-Node Production | k3s cluster | Large venue, high availability |
| Cloud Deployment | Managed k3s | University cloud deployment |

## Local Deployment

### Automated Bootstrap (Recommended)

The bootstrap process automates local k3s setup:

```bash
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera
make bootstrap
```

**This process:**
1. Installs k3s
2. Sets up local container registry
3. Builds all service images
4. Deploys infrastructure (Redis, Kafka, Milvus)
5. Deploys monitoring stack
6. Deploys all AI services

**Runtime:** 15-20 minutes

### Manual Setup

If you prefer manual setup or encounter issues:

#### 1. Install k3s

```bash
curl -sfL https://get.k3s.io | sh -
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

#### 2. Verify Installation

```bash
kubectl get nodes
kubectl get pods -A
```

#### 3. Create Namespaces

```bash
kubectl create namespace live
kubectl create namespace shared
kubectl create namespace monitoring
```

#### 4. Deploy Infrastructure

```bash
kubectl apply -k infrastructure/kubernetes/overlays/dev
```

#### 5. Build and Deploy Services

```bash
make build-all
kubectl apply -f infrastructure/kubernetes/services/
```

#### 6. Verify Deployment

```bash
kubectl get pods -n live
kubectl get pods -n shared
kubectl get pods -n monitoring
```

## k3s Deployment

### Cluster Setup

#### Single-Node (k3s)

For small deployments or edge computing:

```bash
# Install k3s with custom configuration
curl -sfL https://get.k3s.io | sh - \
  --write-kubeconfig-mode 644 \
  --disable traefik \
  --disable servicelb
```

#### Multi-Node (k3s)

For larger deployments, use a multi-node k3s cluster:

```bash
# On control plane
kubeadm init --pod-network-cidr=10.244.0.0/16

# On worker nodes
kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

### Namespace Configuration

Create namespaces with resource quotas:

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: live
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: live
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
EOF
```

### Service Deployment

#### Deploy Infrastructure

```bash
kubectl apply -k infrastructure/kubernetes/overlays/production
```

#### Deploy Services

```bash
# Deploy all services
kubectl apply -f infrastructure/kubernetes/services/

# Or deploy individually
kubectl apply -f infrastructure/kubernetes/services/openclaw-orchestrator/
kubectl apply -f infrastructure/kubernetes/services/scenespeak-agent/
```

### GPU Configuration

For GPU-enabled services (SceneSpeak, OpenClaw):

```bash
# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify GPU availability
kubectl get nodes -o json | jq '.items[0].status.capacity'
```

Service configuration:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    nvidia.com/gpu: 1
```

## Cloud Deployment

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster \
  --name chimera-prod \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.xlarge \
  --nodes-max 6 \
  --nodes-min 2

# Deploy
kubectl apply -k infrastructure/kubernetes/overlays/production
```

### Google GKE

```bash
# Create GKE cluster
gcloud container clusters create chimera-prod \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --accelerator type=nvidia-tesla-t4,count=1

# Deploy
kubectl apply -k infrastructure/kubernetes/overlays/production
```

### Azure AKS

```bash
# Create AKS cluster
az aks create \
  --resource-group chimera-rg \
  --name chimera-prod \
  --node-count 3 \
  --node-vm-size Standard_NC4as_T4_v3 \
  --enable-cluster-autoscaler

# Deploy
kubectl apply -k infrastructure/kubernetes/overlays/production
```

## Configuration Management

### Environment Variables

Configuration is managed via environment variables. See `.env.example` for all options.

### Kubernetes Secrets

```bash
# Create secret from file
kubectl create secret generic chimera-secrets \
  --from-env-file=.env \
  -n live

# Create sealed secret (for production)
kubeseal -f chimera-secret.yaml -w sealed-secret.yaml
kubectl apply -f sealed-secret.yaml
```

### ConfigMaps

```bash
# Create configmap from file
kubectl create configmap chimera-config \
  --from-file=configs/ \
  -n live
```

### Configuration by Environment

| Environment | Config Location |
|-------------|-----------------|
| Development | `.env` file |
| Staging | k3s ConfigMaps |
| Production | Sealed Secrets |

## Monitoring Setup

### Deploy Monitoring Stack

```bash
# Deploy Prometheus
kubectl apply -f infrastructure/monitoring/prometheus/

# Deploy Grafana
kubectl apply -f infrastructure/monitoring/grafana/

# Deploy Jaeger
kubectl apply -f infrastructure/monitoring/jaeger/
```

### Access Dashboards

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Port-forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Port-forward Jaeger
kubectl port-forward -n monitoring svc/jaeger 16686:16686
```

**Default Credentials:**
- Grafana: `admin` / `admin` (change on first login)

### Configure Alerts

Alert rules are in `configs/alerts/`:

```bash
kubectl apply -f configs/alerts/prometheus-alerts.yaml
```

## Troubleshooting

### Common Issues

#### Service Not Starting

```bash
# Check pod status
kubectl get pods -n live

# Check logs
kubectl logs -n live deployment/scenespeak-agent

# Describe pod for events
kubectl describe pod -n live <pod-name>
```

#### GPU Not Available

```bash
# Check GPU nodes
kubectl get nodes -o json | jq '.items[].status.allocatable'

# Check NVIDIA plugin
kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds
```

#### Image Pull Errors

```bash
# Verify images exist
docker images | grep chimera

# Check registry connectivity
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

#### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n live

# Adjust resource limits
kubectl edit deployment scenespeak-agent -n live
```

### Debug Mode

Enable debug logging:

```yaml
env:
  - name: LOG_LEVEL
    value: DEBUG
```

## Maintenance

### Updates

#### Update Services

```bash
# Build new images
make build-all

# Deploy new version
kubectl set image deployment/scenespeak-agent \
  scenespeak-agent=ghcr.io/project-chimera/scenespeak-agent:v1.0.1 \
  -n live

# Or apply updated manifests
kubectl apply -k infrastructure/kubernetes/overlays/production
```

#### Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/scenespeak-agent -n live

# Check rollout status
kubectl rollout status deployment/scenespeak-agent -n live
```

### Backup

```bash
# Backup etcd (k3s)
sudo cp /var/lib/rancher/k3s/server/db/snapshots/* /backup/

# Backup k3s resources
kubectl get all -n live -o yaml > backup-live.yaml
```

### Scaling

```bash
# Scale a service
kubectl scale deployment/scenespeak-agent --replicas=3 -n live

# Enable autoscaling
kubectl autoscale deployment/scenespeak-agent \
  --min=1 --max=5 --cpu-percent=70 -n live
```

### Health Checks

```bash
# Check all services
make k8s-status

# Run health checks
kubectl get pods -n live -o jsonpath='{.items[*].status.phase}'
```

## Production Considerations

### High Availability

- Run multiple replicas of critical services
- Use anti-affinity rules for pod placement
- Configure readiness/liveness probes properly

### Security

- Use network policies to restrict traffic
- Enable RBAC for k3s
- Use Sealed Secrets for sensitive data
- Regular security updates

### Performance

- Enable Horizontal Pod Autoscaler
- Use SSD storage for databases
- Configure resource limits appropriately
- Monitor and optimize GPU utilization

### Disaster Recovery

- Regular backups of etcd/database
- Documented restore procedures
- Multi-region deployment for critical deployments

---

For more information:
- [Architecture Documentation](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
- [Monitoring Runbook](runbooks/monitoring.md)
- [Incident Response](runbooks/incident-response.md)
