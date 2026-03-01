# Bootstrap Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automated single-command bootstrap that installs k3s, builds all images, and deploys Project Chimera locally

**Architecture:** Sequential shell scripts orchestrated by Makefile, each script is idempotent with error trapping and cleanup

**Tech Stack:** k3s, Docker, Kubernetes, Kustomize, bash shell scripting

---

## Task 1: Create Bootstrap Directory Structure

**Files:**
- Create: `scripts/bootstrap/01-install-k3s.sh`
- Create: `scripts/bootstrap/02-setup-registry.sh`
- Create: `scripts/bootstrap/03-build-images.sh`
- Create: `scripts/bootstrap/04-deploy-infrastructure.sh`
- Create: `scripts/bootstrap/05-deploy-monitoring.sh`
- Create: `scripts/bootstrap/06-deploy-services.sh`
- Create: `scripts/bootstrap/07-verify-deployment.sh`
- Create: `scripts/bootstrap/cleanup-on-error.sh`

**Step 1: Create bootstrap directory**

```bash
mkdir -p scripts/bootstrap
```

**Step 2: Create placeholder files with execute permissions**

```bash
for i in {01..07}; do
    touch scripts/bootstrap/${i}-*.sh
    chmod +x scripts/bootstrap/${i}-*.sh 2>/dev/null || true
done
touch scripts/bootstrap/cleanup-on-error.sh
chmod +x scripts/bootstrap/cleanup-on-error.sh
```

**Step 3: Verify structure**

Run: `ls -la scripts/bootstrap/`
Expected: List of 8 .sh files with -rwxr-xr-x permissions

**Step 4: Commit**

```bash
git add scripts/bootstrap/
git commit -m "chore: create bootstrap directory structure"
```

---

## Task 2: Implement k3s Installation Script

**Files:**
- Create: `scripts/bootstrap/01-install-k3s.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/01-install-k3s.sh << 'EOF'
#!/bin/bash
set -e

echo "⏳ [1/7] Installing k3s..."

# Check if k3s is already installed
if command -v k3s &> /dev/null; then
    echo "✅ k3s already installed"
    k3s --version
else
    echo "⏳ Installing k3s..."
    curl -sfL https://get.k3s.io | sh -
    echo "✅ k3s installed"
fi

# Wait for k3s to be ready
echo "⏳ Waiting for k3s to be ready..."
until kubectl get nodes &> /dev/null; do
    sleep 2
done

# Verify node is Ready
NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
if [ "$NODE_STATUS" != "True" ]; then
    echo "❌ k3s node not ready"
    exit 1
fi

echo "✅ k3s node ready"

# Export kubeconfig for current user
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config

# Create namespaces
echo "⏳ Creating namespaces..."
kubectl create namespace live --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace preprod --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace shared --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace registry --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces created: live, preprod, shared, registry"

# Install Kustomize if not present
if ! command -v kustomize &> /dev/null; then
    echo "⏳ Installing Kustomize..."
    curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
    sudo mv kustomize /usr/local/bin/
fi

echo "✅ Kustomize installed"
echo "✅ [1/7] k3s installation complete"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/01-install-k3s.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/01-install-k3s.sh`
Expected: No output (syntax OK)

**Step 4: Commit**

```bash
git add scripts/bootstrap/01-install-k3s.sh
git commit -m "feat: add k3s installation script"
```

---

## Task 3: Implement Local Registry Script

**Files:**
- Create: `scripts/bootstrap/02-setup-registry.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/02-setup-registry.sh << 'EOF'
#!/bin/bash
set -e

echo "⏳ [2/7] Setting up local container registry..."

# Deploy local registry
kubectl apply -f - <<EOF_MANIFEST
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry
  namespace: registry
spec:
  replicas: 1
  selector:
    matchLabels:
      app: registry
  template:
    metadata:
      labels:
        app: registry
    spec:
      containers:
      - name: registry
        image: registry:2
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: data
          mountPath: /var/lib/registry
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: registry
  namespace: registry
spec:
  type: NodePort
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
  selector:
    app: registry
EOF_MANIFEST

# Wait for registry to be ready
kubectl wait --for=condition=available -n registry deployment/registry --timeout=60s

echo "✅ Local registry ready at localhost:30500"

# Configure insecure registry for containerd
sudo mkdir -p /etc/rancher/k3s
cat <<EOF | sudo tee /etc/rancher/k3s/registries.yaml
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF

# Restart k3s to apply registry config
echo "⏳ Restarting k3s to apply registry configuration..."
sudo systemctl restart k3s

# Wait for k3s to come back
until kubectl get nodes &> /dev/null; do
    sleep 2
done

echo "✅ Local registry configured"
echo "✅ [2/7] Registry setup complete"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/02-setup-registry.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/02-setup-registry.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/02-setup-registry.sh
git commit -m "feat: add local registry setup script"
```

---

## Task 4: Implement Image Build Script

**Files:**
- Create: `scripts/bootstrap/03-build-images.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/03-build-images.sh << 'EOF'
#!/bin/bash
set -e

REGISTRY="localhost:30500"
VERSION="latest"

SERVICES=(
    "openclaw-orchestrator"
    "scenespeak-agent"
    "captioning-agent"
    "bsl-text2gloss-agent"
    "sentiment-agent"
    "lighting-control"
    "safety-filter"
    "operator-console"
)

echo "⏳ [3/7] Building all service images..."

for service in "${SERVICES[@]}"; do
    echo "⏳ Building $service..."

    if [ ! -d "services/$service" ]; then
        echo "⚠️  Service directory not found: services/$service"
        continue
    fi

    docker build -t $REGISTRY/project-chimera/$service:$VERSION services/$service/

    echo "⏳ Pushing $service to local registry..."
    docker push $REGISTRY/project-chimera/$service:$VERSION

    echo "✅ $service built and pushed"
done

echo "✅ [3/7] All images built and pushed to local registry"
echo ""
echo "Available images:"
docker images | grep project-chimera
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/03-build-images.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/03-build-images.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/03-build-images.sh
git commit -m "feat: add image build script"
```

---

## Task 5: Implement Infrastructure Deployment Script

**Files:**
- Create: `scripts/bootstrap/04-deploy-infrastructure.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/04-deploy-infrastructure.sh << 'EOF'
#!/bin/bash
set -e

NAMESPACE="shared"

echo "⏳ [4/7] Deploying shared infrastructure..."

# Deploy Redis
echo "⏳ Deploying Redis..."
kubectl apply -k infrastructure/kubernetes/base/redis/ -n $NAMESPACE

# Deploy Kafka
echo "⏳ Deploying Kafka..."
kubectl apply -k infrastructure/kubernetes/base/kafka/ -n $NAMESPACE

# Deploy Vector DB
echo "⏳ Deploying Vector DB..."
kubectl apply -k infrastructure/kubernetes/base/vector-db/ -n $NAMESPACE

echo "⏳ Waiting for infrastructure to be ready..."

# Wait for Redis
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=redis --timeout=180s || echo "⚠️  Redis pods not ready"

# Wait for Kafka
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=kafka --timeout=180s || echo "⚠️  Kafka pods not ready"

# Wait for Vector DB
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=milvus --timeout=180s || echo "⚠️  Milvus pods not ready"

echo "✅ Shared infrastructure deployed"

# Display service endpoints
echo ""
echo "📡 Infrastructure endpoints:"
kubectl get svc -n $NAMESPACE

echo "✅ [4/7] Infrastructure deployment complete"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/04-deploy-infrastructure.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/04-deploy-infrastructure.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/04-deploy-infrastructure.sh
git commit -m "feat: add infrastructure deployment script"
```

---

## Task 6: Implement Monitoring Deployment Script

**Files:**
- Create: `scripts/bootstrap/05-deploy-monitoring.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/05-deploy-monitoring.sh << 'EOF'
#!/bin/bash
set -e

NAMESPACE="shared"

echo "⏳ [5/7] Deploying monitoring stack..."

# Deploy Prometheus
echo "⏳ Deploying Prometheus..."
kubectl apply -k infrastructure/kubernetes/base/monitoring/prometheus/ -n $NAMESPACE

# Deploy Grafana
echo "⏳ Deploying Grafana..."
kubectl apply -k infrastructure/kubernetes/base/monitoring/grafana/ -n $NAMESPACE

# Deploy Jaeger
echo "⏳ Deploying Jaeger..."
kubectl apply -k infrastructure/kubernetes/base/monitoring/jaeger/ -n $NAMESPACE

echo "⏳ Waiting for monitoring stack to be ready..."

kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=prometheus --timeout=180s || echo "⚠️  Prometheus not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=grafana --timeout=180s || echo "⚠️  Grafana not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=jaeger --timeout=180s || echo "⚠️  Jaeger not ready"

echo "✅ Monitoring stack deployed"

# Kill existing port forwards if any
pkill -f "port-forward.*prometheus" || true
pkill -f "port-forward.*grafana" || true
pkill -f "port-forward.*jaeger" || true

# Start port forwards in background
kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090 > /dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000 > /dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE svc/jaeger 16686:16686 > /dev/null 2>&1 &

sleep 3

echo "✅ Port forwards active"
echo ""
echo "📊 Monitoring endpoints:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  Jaeger:      http://localhost:16686"

echo "✅ [5/7] Monitoring deployment complete"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/05-deploy-monitoring.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/05-deploy-monitoring.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/05-deploy-monitoring.sh
git commit -m "feat: add monitoring deployment script"
```

---

## Task 7: Implement Services Deployment Script

**Files:**
- Create: `scripts/bootstrap/06-deploy-services.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/06-deploy-services.sh << 'EOF'
#!/bin/bash
set -e

REGISTRY="localhost:30500"
VERSION="latest"
NAMESPACE="live"

echo "⏳ [6/7] Deploying AI services to live namespace..."

# Update image tags in deployments to use local registry
for service in openclaw-orchestrator scenespeak-agent captioning-agent bsl-text2gloss-agent sentiment-agent lighting-control safety-filter operator-console; do
    if [ -f "infrastructure/kubernetes/base/$service/deployment.yaml" ]; then
        echo "⏳ Deploying $service..."

        # Patch image to use local registry
        kubectl set image deployment/$service $service=$REGISTRY/project-chimera/$service:$VERSION -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -n $NAMESPACE -f -

        # Apply the deployment
        kubectl apply -f infrastructure/kubernetes/base/$service/deployment.yaml -n $NAMESPACE
        kubectl apply -f infrastructure/kubernetes/base/$service/service.yaml -n $NAMESPACE

        # Wait for rollout
        kubectl rollout status deployment/$service -n $NAMESPACE --timeout=300s || echo "⚠️  $service rollout timeout"

        echo "✅ $service deployed"
    else
        echo "⚠️  Manifests not found for $service"
    fi
done

echo "✅ All AI services deployed"

# Display deployments
echo ""
echo "📦 Deployed services:"
kubectl get deployments -n $NAMESPACE

echo ""
echo "🌐 Service endpoints:"
kubectl get svc -n $NAMESPACE

echo "✅ [6/7] Services deployment complete"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/06-deploy-services.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/06-deploy-services.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/06-deploy-services.sh
git commit -m "feat: add services deployment script"
```

---

## Task 8: Implement Verification Script

**Files:**
- Create: `scripts/bootstrap/07-verify-deployment.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/07-verify-deployment.sh << 'EOF'
#!/bin/bash

NAMESPACE="live"

echo "⏳ [7/7] Running deployment verification..."

# Check all pods are running
echo "⏳ Checking pod status..."

PODS_NOT_READY=$(kubectl get pods -n $NAMESPACE --no-headers | grep -v "Running\|Completed" | wc -l)

if [ "$PODS_NOT_READY" -gt 0 ]; then
    echo "⚠️  Some pods are not ready yet:"
    kubectl get pods -n $NAMESPACE
    echo "⏳ Waiting additional 30 seconds for pods to stabilize..."
    sleep 30
fi

echo "✅ Pod status check complete"

# Check shared namespace pods
echo ""
echo "🌊 Shared namespace pods:"
kubectl get pods -n shared

echo ""
echo "🌊 Live namespace pods:"
kubectl get pods -n $NAMESPACE

echo ""
echo "🌊 All services:"
kubectl get svc -A

echo ""
echo "✅ [7/7] Deployment verification complete!"
echo ""
echo "🎉 Project Chimera bootstrap complete!"
echo ""
echo "📊 Access points:"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  Prometheus:  http://localhost:9090"
echo "  Jaeger:      http://localhost:16686"
echo ""
echo "🔌 To access services:"
echo "  make run-openclaw   # Port-forward OpenClaw to localhost:8000"
echo "  make run-scenespeak # Port-forward SceneSpeak to localhost:8001"
echo "  make logs           # View SceneSpeak logs"
echo "  make logs-all       # View all service logs"
echo ""
echo "📖 Documentation:"
echo "  docs/plans/IMPLEMENTATION_DOCUMENTATION.md"
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/07-verify-deployment.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/07-verify-deployment.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/07-verify-deployment.sh
git commit -m "feat: add verification script"
```

---

## Task 9: Implement Cleanup Script

**Files:**
- Create: `scripts/bootstrap/cleanup-on-error.sh`

**Step 1: Write script content**

```bash
cat > scripts/bootstrap/cleanup-on-error.sh << 'EOF'
#!/bin/bash

echo ""
echo "❌ Bootstrap failed. Cleaning up..."
echo ""

# Stop port forwards
echo "🧹 Stopping port forwards..."
pkill -f "port-forward" || true

# Ask before destructive actions
echo ""
read -p "Remove k3s and all resources? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏳ Removing k3s..."
    /usr/local/bin/k3s-uninstall.sh 2>/dev/null || true
    echo "🧹 k3s removed"

    # Clean kubeconfig
    rm -f ~/.kube/config
    echo "🧹 Kubeconfig removed"
else
    echo "⚠️  k3s left intact for debugging"
    echo ""
    echo "💡 Debug commands:"
    echo "   kubectl get pods -A"
    echo "   kubectl get svc -A"
    echo "   journalctl -u k3s -n 50"
fi

echo ""
echo "📋 Bootstrap log location: /tmp/project-chimera-bootstrap.log"
exit 1
EOF
```

**Step 2: Set execute permissions**

```bash
chmod +x scripts/bootstrap/cleanup-on-error.sh
```

**Step 3: Verify script syntax**

Run: `bash -n scripts/bootstrap/cleanup-on-error.sh`
Expected: No output

**Step 4: Commit**

```bash
git add scripts/bootstrap/cleanup-on-error.sh
git commit -m "feat: add cleanup script"
```

---

## Task 10: Update Makefile with Bootstrap Target

**Files:**
- Modify: `Makefile`

**Step 1: Add bootstrap target to Makefile**

Add these targets after the existing `help` section:

```makefile
# Bootstrap
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
	@echo ""
	@echo "🎉 Bootstrap complete!"
	@echo ""
	@echo "📊 Access points:"
	@echo "  Grafana:     http://localhost:3000 (admin/admin)"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Jaeger:      http://localhost:16686"
	@echo ""
	@echo "🔌 To access services:"
	@echo "  make run-openclaw   # Port-forward OpenClaw to localhost:8000"
	@echo "  make run-scenespeak # Port-forward SceneSpeak to localhost:8001"
	@echo "  make logs           # View SceneSpeak logs"
	@echo "  make logs-all       # View all service logs"

bootstrap-status:
	@echo "📊 Bootstrap Status:"
	@echo ""
	@kubectl get nodes 2>/dev/null || echo "k3s not installed"
	@echo ""
	@echo "📦 Namespaces:"
	@kubectl get namespaces 2>/dev/null || echo "No namespaces"
	@echo ""
	@echo "🌊 Pods (live):"
	@kubectl get pods -n live 2>/dev/null || echo "No pods in live"
	@echo ""
	@echo "🌊 Pods (shared):"
	@kubectl get pods -n shared 2>/dev/null || echo "No pods in shared"

bootstrap-destroy:
	@echo "⚠️  Destroying k3s cluster..."
	@read -p "Are you sure? This will remove k3s and all resources. (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		pkill -f "port-forward" || true; \
		/usr/local/bin/k3s-uninstall.sh || true; \
		rm -f ~/.kube/config; \
		echo "🧹 k3s removed"; \
	else \
		echo "Aborted"; \
	fi
```

**Step 2: Update .PHONY declaration**

Update the first line to include new targets:

```makefile
.PHONY: help dev test lint format build-all deploy \
        install-deps verify check-env clean \
        run-dev backup restore \
        bootstrap bootstrap-status bootstrap-destroy
```

**Step 3: Verify Makefile syntax**

Run: `make -n bootstrap`
Expected: Dry-run of all bootstrap commands

**Step 4: Commit**

```bash
git add Makefile
git commit -m "feat: add bootstrap targets to Makefile"
```

---

## Task 11: Create Bootstrap Documentation

**Files:**
- Create: `reference/runbooks/bootstrap-setup.md`

**Step 1: Write documentation**

```bash
cat > reference/runbooks/bootstrap-setup.md << 'EOF'
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

Use `make run-*` targets to port-forward services:

```bash
make run-openclaw    # localhost:8000
make run-scenespeak  # localhost:8001
make run-captioning  # localhost:8002
make run-sentiment   # localhost:8004
make run-bsl         # localhost:8003
```

## Troubleshooting

### Bootstrap fails

Check the error message and logs:
```bash
kubectl get pods -A
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

### k3s won't start

```bash
sudo systemctl status k3s
journalctl -u k3s -n 50
```

### Port conflicts

Kill existing port forwards:
```bash
pkill port-forward
```

## Clean Restart

To completely remove and restart:

```bash
make bootstrap-destroy
make bootstrap
```

## Manual Steps

If you need to run bootstrap scripts individually:

```bash
./scripts/bootstrap/01-install-k3s.sh
./scripts/bootstrap/02-setup-registry.sh
./scripts/bootstrap/03-build-images.sh
./scripts/bootstrap/04-deploy-infrastructure.sh
./scripts/bootstrap/05-deploy-monitoring.sh
./scripts/bootstrap/06-deploy-services.sh
./scripts/bootstrap/07-verify-deployment.sh
```

## Next Steps

After bootstrap completes:

1. Verify all pods are running: `make bootstrap-status`
2. Access Grafana: http://localhost:3000
3. Test OpenClaw: `make run-openclaw` then curl http://localhost:8000/health/live
4. View logs: `make logs` or `make logs-all`

## Related Documentation

- [Implementation Documentation](../plans/IMPLEMENTATION_DOCUMENTATION.md)
- [Bootstrap Design](../plans/2026-02-26-bootstrap-setup-design.md)
EOF
```

**Step 2: Verify documentation**

Run: `cat reference/runbooks/bootstrap-setup.md | head -20`
Expected: Documentation header content

**Step 3: Commit**

```bash
git add reference/runbooks/bootstrap-setup.md
git commit -m "docs: add bootstrap setup guide"
```

---

## Task 12: Final Verification and Testing

**Files:**
- Test: All bootstrap scripts

**Step 1: Verify all scripts have execute permissions**

Run: `ls -la scripts/bootstrap/`
Expected: All .sh files have -rwxr-xr-x permissions

**Step 2: Verify script syntax**

Run: `for script in scripts/bootstrap/*.sh; do bash -n "$script" && echo "✅ $script" || echo "❌ $script"; done`
Expected: All scripts pass syntax check

**Step 3: Verify Makefile targets**

Run: `make -n bootstrap | head -20`
Expected: Dry-run output showing bootstrap commands

**Step 4: Create summary of all changes**

Run: `git diff HEAD~12 --stat`
Expected: Summary of all bootstrap files

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete bootstrap setup implementation

- Added 7 bootstrap scripts for automated setup
- Added cleanup script for error handling
- Updated Makefile with bootstrap targets
- Added bootstrap documentation

Features:
- Automated k3s installation
- Local container registry
- Infrastructure deployment
- Monitoring stack deployment
- AI services deployment
- Health verification

Usage: make bootstrap"
```

---

## Execution Notes

### Dependencies
- Docker must be installed before running bootstrap
- Scripts are sequential - each must complete before next runs
- Error trap triggers cleanup on any failure

### Testing Strategy
1. Scripts are idempotent - safe to re-run
2. Syntax checked with `bash -n`
3. Dry-run with `make -n bootstrap`
4. Full integration test on first run

### Success Criteria
- All 8 scripts created and executable
- Makefile has bootstrap target
- Documentation complete
- All syntax checks pass

---

**Plan complete and saved to `docs/plans/2026-02-26-bootstrap-setup.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
