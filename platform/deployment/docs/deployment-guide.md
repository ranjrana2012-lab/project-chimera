# Deployment Guide

## Prerequisites

- k3s cluster running
- kubectl configured
- Helm 3.x installed
- Access to GitHub Container Registry

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera
```

### 2. Create Namespaces

```bash
kubectl create namespace chimera-live
kubectl create namespace chimera-preprod
kubectl create namespace chimera-shared
```

### 3. Deploy with Helm

```bash
helm upgrade --install chimera platform/deployment/helm/project-chimera \
  --namespace chimera-live \
  --values platform/deployment/helm/project-chimera/values.yaml \
  --wait
```

### 4. Verify Deployment

```bash
kubectl get pods -n chimera-live
kubectl get svc -n chimera-live
```

## Upgrading

```bash
helm upgrade chimera platform/deployment/helm/project-chimera \
  --namespace chimera-live \
  --values platform/deployment/helm/project-chimera/values.yaml \
  --set images.tag=<new-version>
```

## Troubleshooting

See [runbooks.md](runbooks.md) for common issues.
