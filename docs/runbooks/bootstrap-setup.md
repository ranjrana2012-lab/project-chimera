# Bootstrap Setup Guide

## Overview

The `make bootstrap` command automates the complete setup of Project Chimera on a local k3s cluster.

## Prerequisites

- **OS:** Linux (Ubuntu 22.04 recommended)
- **CPU:** 8+ cores recommended
- **RAM:** 32+ GB recommended
- **Storage:** 50+ GB free
- **Sudo:** Root access for k3s installation
- **Docker:** Installed and running

## Quick Start

```bash
git clone <repository>
cd Project_Chimera
make bootstrap
```

Expected runtime: 15-20 minutes

## What Bootstrap Does

1. **Installs k3s** - Lightweight Kubernetes distribution
2. **Sets up local registry** - Container registry at localhost:30500
3. **Builds all images** - Docker images for 8 services
4. **Deploys infrastructure** - Redis, Kafka, Milvus
5. **Deploys monitoring** - Prometheus, Grafana, Jaeger
6. **Deploys services** - All AI agents
7. **Verifies deployment** - Health checks on all services

## Access Points

After bootstrap completes:

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |

### Service APIs

```bash
make run-openclaw    # localhost:8000
make run-scenespeak  # localhost:8001
make run-captioning  # localhost:8002
make run-sentiment   # localhost:8004
make run-bsl         # localhost:8003
```

## Troubleshooting

### Bootstrap fails
```bash
kubectl get pods -A
kubectl describe pod <pod-name> -n <namespace>
```

### k3s won't start
```bash
sudo systemctl status k3s
journalctl -u k3s -n 50
```

### Port conflicts
```bash
pkill port-forward
```

## Clean Restart

```bash
make bootstrap-destroy
make bootstrap
```

## Next Steps

1. Verify pods: `make bootstrap-status`
2. Access Grafana: http://localhost:3000
3. Test services: `make run-openclaw`

## Related Documentation

- [Implementation Documentation](../plans/IMPLEMENTATION_DOCUMENTATION.md)
- [Bootstrap Design](../plans/2026-02-26-bootstrap-setup-design.md)
