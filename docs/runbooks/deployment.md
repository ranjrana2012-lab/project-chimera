# Deployment Runbook

This runbook covers deployment procedures for Project Chimera.

## Prerequisites

- k3s cluster (local) or cloud provider (production)
- kubectl configured
- Docker registry access
- NVIDIA GPU drivers (for GPU nodes)

## Initial Deployment

### 1. Build Images

```bash
make build-all
```

### 2. Deploy Infrastructure

```bash
./scripts/setup/setup_kubernetes.sh dev live
```

### 3. Verify Deployment

```bash
kubectl get pods -n live
kubectl get services -n live
```

## Rolling Updates

### Update a Single Service

```bash
kubectl set image deployment/scenespeak-agent \
  scenespeak-agent=ghcr.io/project-chimera/scenespeak-agent:v1.0.1 \
  -n live
```

### Update All Services

```bash
./scripts/operations/deploy.sh prod live
```

## Rollback Procedures

### Single Service Rollback

```bash
kubectl rollout undo deployment/scenespeak-agent -n live
```

### Full Rollback

```bash
./scripts/operations/rollback.sh live all
```

## Troubleshooting

### Pod Not Starting

1. Check pod status: `kubectl describe pod <pod-name> -n live`
2. Check logs: `kubectl logs <pod-name> -n live`
3. Check events: `kubectl get events -n live --sort-by='.lastTimestamp'`

### Service Not Responding

1. Check endpoint: `kubectl get endpoints <service-name> -n live`
2. Check pod labels: `kubectl get pods -n live --show-labels`
3. Test service: `kubectl port-forward svc/<service-name> 8000:8000 -n live`

### GPU Issues

1. Check GPU availability: `kubectl describe node | grep nvidia.com/gpu`
2. Check GPU usage: `kubectl exec -n live <pod> -- nvidia-smi`
3. Verify GPU request: `kubectl describe pod <pod> -n live | grep nvidia.com/gpu`
