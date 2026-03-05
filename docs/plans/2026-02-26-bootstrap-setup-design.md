# Project Chimera - Bootstrap Setup Design

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Approved
**Author:** Technical Architecture Team

---

## Overview

This design describes an automated single-command bootstrap process that installs and configures Project Chimera on a local Kubernetes (k3s) cluster. Students can run `make bootstrap` to go from zero to fully running system in one command.

**Target Audience:** 2nd-3rd year degree students
**Execution Time:** ~15-20 minutes (depending on hardware)

---

## Design Goals

1. **Single Command Execution** - `make bootstrap` handles everything
2. **Idempotent** - Scripts can be safely re-run
3. **Error Recovery** - Automatic cleanup on failure
4. **Local Development** - No external dependencies required
5. **Production-Like** - Uses k3s as specified in TRD

---

## Architecture

### Bootstrap Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    make bootstrap                           │
└────────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐        ┌─────────┐        ┌─────────┐
│  k3s    │        │Registry │        │ Images  │
│Install  │   →    │Setup    │   →    │Build    │
└─────────┘        └─────────┘        └─────────┘
                                                  │
    ┌─────────────────────────────────────────────┘
    │
    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Infra-       │     │Monitoring   │     │AI           │
│structure    │  →  │Stack        │  →  │Services     │
│(Redis/Kafka)│     │(Prom/Graph) │     │(8 services) │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                      ┌─────────────┐
                                      │Verification │
                                      │& Health     │
                                      └─────────────┘
```

### Script Structure

```
scripts/bootstrap/
├── 01-install-k3s.sh           # Install k3s, setup kubeconfig
├── 02-setup-registry.sh        # Local container registry
├── 03-build-images.sh          # Build all service images
├── 04-deploy-infrastructure.sh # Redis, Kafka, Vector DB
├── 05-deploy-monitoring.sh     # Prometheus, Grafana, Jaeger
├── 06-deploy-services.sh       # All AI services
├── 07-verify-deployment.sh     # Health checks
└── cleanup-on-error.sh         # Rollback on failure
```

---

## Components

### 1. k3s Installation

**Script:** `01-install-k3s.sh`

- Checks if k3s is already installed
- Installs via `curl -sfL https://get.k3s.io | sh -`
- Waits for node to be Ready
- Sets up kubeconfig for current user
- Creates namespaces: `live`, `preprod`, `shared`
- Installs Kustomize

### 2. Local Registry

**Script:** `02-setup-registry.sh`

- Deploys registry:2 to `registry` namespace
- Exposes on NodePort 30500
- Configures k3s with insecure registry
- Restarts k3s to apply configuration

### 3. Image Building

**Script:** `03-build-images.sh`

Builds and pushes 8 service images:

| Service | Purpose |
|---------|---------|
| openclaw-orchestrator | Central orchestration |
| SceneSpeak Agent | LLM dialogue generation |
| Captioning Agent | Speech-to-text |
| bsl-text2gloss-agent | BSL gloss translation |
| Sentiment Agent | Sentiment analysis |
| lighting-control | DMX/OSC stage control |
| safety-filter | Content moderation |
| operator-console | Human oversight |

All images tagged as `localhost:30500/project-chimera/<service>:latest`

### 4. Infrastructure Deployment

**Script:** `04-deploy-infrastructure.sh`

Deploys to `shared` namespace:

| Service | CPU | Memory | Purpose |
|---------|-----|--------|---------|
| Redis | 2 cores | 8 GB | Caching, pub/sub |
| Kafka | 2 cores | 4 GB | Event streaming |
| Milvus | 2 cores | 8 GB | Vector embeddings |

Each service is verified with connection tests before proceeding.

### 5. Monitoring Stack

**Script:** `05-deploy-monitoring.sh`

Deploys to `shared` namespace:

| Component | Port | Access |
|-----------|------|--------|
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 (admin/admin) |
| Jaeger | 16686 | http://localhost:16686 |

Automatic port-forwarding configured for local access.

### 6. AI Services

**Script:** `06-deploy-services.sh`

Deploys to `live` namespace:

| Service | CPU | Memory | GPU | Port |
|---------|-----|--------|-----|------|
| openclaw-orchestrator | 4 cores | 16 GB | 1 | 8000 |
| SceneSpeak Agent | 8 cores | 32 GB | 1 | 8001 |
| Captioning Agent | 4 cores | 8 GB | 0 | 8002 |
| bsl-text2gloss-agent | 2 cores | 8 GB | 0 | 8003 |
| Sentiment Agent | 4 cores | 8 GB | 0 | 8004 |
| lighting-control | 1 core | 2 GB | 0 | 8005 |
| safety-filter | 2 cores | 4 GB | 0 | 8006 |
| operator-console | 1 core | 2 GB | 0 | 8007 |

Each deployment waits for rollout completion before proceeding.

### 7. Verification

**Script:** `07-verify-deployment.sh`

- Checks all pods are Running (not Pending/Error)
- Tests health endpoints via temporary port-forward
- Reports status of all services
- Displays final access information

---

## Makefile Integration

### Primary Target

```makefile
bootstrap:
	@echo "🚀 Bootstrapping Project Chimera..."
	@trap './scripts/bootstrap/cleanup-on-error.sh' ERR; \
	./scripts/bootstrap/01-install-k3s.sh && \
	./scripts/bootstrap/02-setup-registry.sh && \
	./scripts/bootstrap/03-build-images.sh && \
	./scripts/bootstrap/04-deploy-infrastructure.sh && \
	./scripts/bootstrap/05-deploy-monitoring.sh && \
	./scripts/bootstrap/06-deploy-services.sh && \
	./scripts/bootstrap/07-verify-deployment.sh
	@echo "🎉 Bootstrap complete!"
```

### Utility Targets

```makefile
# Status commands
bootstrap-status       # Show all resources
bootstrap-destroy      # Remove k3s cluster

# Quick access
run-openclaw           # Port-forward OpenClaw to :8000
run-scenespeak         # Port-forward SceneSpeak to :8001
run-captioning         # Port-forward Captioning to :8002
run-sentiment          # Port-forward Sentiment to :8004
run-bsl                # Port-forward BSL to :8003

# Logs
logs                   # View SceneSpeak logs
logs-all               # View all service logs
```

---

## Error Handling

### Failure Strategy

1. **Error Trap** - `trap './scripts/bootstrap/cleanup-on-error.sh' ERR` catches any script failure
2. **Cleanup Script** - Stops port-forwards, optionally removes k3s
3. **Logging** - All output saved to `/tmp/project-chimera-bootstrap.log`
4. **User Choice** - Prompts before destructive actions

### Recovery Options

- **Re-run bootstrap** - Scripts are idempotent, safe to re-run
- **Manual debugging** - k3s left intact for troubleshooting
- **Clean slate** - `make bootstrap-destroy` to remove everything

---

## Success Criteria

After `make bootstrap` completes:

- [ ] k3s node is Ready
- [ ] All namespaces exist (live, preprod, shared)
- [ ] All 8 services deployed and Running
- [ ] Infrastructure services healthy (Redis, Kafka, Milvus)
- [ ] Monitoring stack accessible (Grafana, Prometheus, Jaeger)
- [ ] All service health endpoints responding
- [ ] No pods in Pending/Error state

---

## Post-Bootstrap Access

### Web UIs

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Jaeger:** http://localhost:16686

### Service APIs

```bash
make run-openclaw    # → http://localhost:8000
make run-scenespeak  # → http://localhost:8001
make run-captioning  # → http://localhost:8002
make run-sentiment   # → http://localhost:8004
make run-bsl         # → http://localhost:8003
```

### Logs

```bash
make logs           # SceneSpeak logs
make logs-all       # All service logs
```

---

## Resource Requirements

### Minimum

- CPU: 8 cores
- RAM: 32 GB
- Storage: 50 GB free
- OS: Linux (Ubuntu 22.04 recommended)

### Recommended

- CPU: 16+ cores
- RAM: 64 GB
- Storage: 100 GB free
- GPU: NVIDIA GPU with k3s device plugin support

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| k3s won't start | Check journalctl: `journalctl -u k3s` |
| Pod stuck in Pending | Check resources: `kubectl describe pod` |
| Image pull errors | Verify registry: `kubectl get svc -n registry` |
| Port conflicts | Kill existing: `pkill port-forward` |

### Debug Mode

Set `DEBUG=1` environment variable for verbose output:
```bash
DEBUG=1 make bootstrap
```

---

## Security Considerations

- Local registry uses HTTP (insecure) - suitable for development only
- k3s runs as root - use container-specific security contexts
- No network policies applied in bootstrap (use `k8s-apply` for full config)
- Default Grafana credentials (admin/admin) - change in production

---

## Future Enhancements

1. **GPU Detection** - Auto-detect NVIDIA GPUs and configure device plugin
2. **Progress Bar** - Show overall bootstrap progress
3. **Snapshot/Restore** - Save bootstrap state for quick restore
4. **Health Dashboard** - Web UI showing real-time bootstrap status
5. **Cloud Deployment** - Support for GKE/AKE deployment

---

## Related Documents

- [Implementation Documentation](./IMPLEMENTATION_DOCUMENTATION.md)
- [Scaffold Design](./2026-02-26-project-chimera-scaffold-design.md)
- [TRD - Project Chimera](../../TRD_Project_Chimera.md)

---

*This design was approved on 2026-02-26 for immediate implementation.*
