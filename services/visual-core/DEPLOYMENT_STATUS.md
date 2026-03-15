# Visual Core Service - Kubernetes Deployment Status

**Date:** 2026-03-15
**Task:** Task 5 - Deploy Visual Core Service
**Namespace:** project-chimera

## Deployment Summary

### ✅ Completed Steps

1. **Namespace Creation**
   - Created `project-chimera` namespace successfully

2. **Kubernetes Resources Applied**
   - ConfigMap `visual-core-config` created (8 configuration items)
   - Secret `visual-core-secrets` created with placeholder LTX_API_KEY
   - Service `visual-core` created (ClusterIP: 10.43.169.16, Port: 8014)
   - PersistentVolumeClaim `visual-core-storage` created and bound (100Gi, local-path)
   - Deployment `visual-core` created (2 replicas configured)
   - HorizontalPodAutoscaler `visual-core-hpa` created (2-8 replicas)

3. **Resource Configuration**
   - **Deployment:** 2 replicas requested
   - **HPA:** Configured for 70% CPU / 80% memory targets
   - **Storage:** 100Gi PVC bound successfully
   - **Security:** Pod security context configured (non-root, dropped capabilities)
   - **Probes:** Liveness and readiness probes configured

### ⚠️ Issues Encountered

#### 1. Docker Build Permission Issue
**Status:** BLOCKED
**Issue:** Cannot build Docker image due to permission denied on Docker socket
```
ERROR: permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**Root Cause:** User lacks permissions to access Docker daemon

**Current Pod Status:**
```
NAME                           READY   STATUS             RESTARTS   AGE
visual-core-667bc889b4-b54ch   0/1     ImagePullBackOff   0          138m
visual-core-667bc889b4-kz7x6   0/1     ImagePullBackOff   0          138m
```

#### 2. Alternative Build Tools
Checked for alternative container build tools:
- `nerdctl`: Not available
- `podman`: Not available
- `buildah`: Not available
- `ctr`: Available (v2.2.1) but doesn't support building images directly
- `crictl`: Available but requires sudo access (password not available)

## Resolution Options

### Option 1: Grant Docker Permissions (Recommended for Development)
```bash
# Add user to docker group (requires sudo)
sudo usermod -aG docker $USER
newgrp docker

# Then build the image
docker build -t visual-core:latest .
```

### Option 2: Use sudo for Docker Build
```bash
# Build with sudo
sudo docker build -t visual-core:latest .

# Import to k3s containerd
sudo docker save visual-core:latest | sudo ctr -n k8s.io image import -
```

### Option 3: Build on Remote Registry
```bash
# Build and push to registry
docker build -t <registry>/visual-core:latest .
docker push <registry>/visual-core:latest

# Update deployment image reference
kubectl set image deployment/visual-core visual-core=<registry>/visual-core:latest -n project-chimera
```

### Option 4: Use CI/CD Pipeline
Configure GitHub Actions or similar CI/CD to:
1. Build image in privileged environment
2. Push to container registry
3. Update deployment manifests

## Current Kubernetes State

### Resources Created:
- ✅ Namespace: `project-chimera`
- ✅ ConfigMap: `visual-core-config` (8 keys)
- ✅ Secret: `visual-core-secrets` (1 key)
- ✅ Service: `visual-core` (ClusterIP 10.43.169.16:8014)
- ✅ PVC: `visual-core-storage` (100Gi, Bound)
- ✅ Deployment: `visual-core` (2 replicas)
- ✅ HPA: `visual-core-hpa` (2-8 replicas)

### Configuration Details:
**Environment Variables (from ConfigMap):**
- LOG_LEVEL: "INFO"
- PORT: "8014"
- LTX_API_BASE: "https://api.ltx.video/v1"
- LTX_MODEL_DEFAULT: "ltx-2-3-pro"
- MAX_CONCURRENT_REQUESTS: "5"
- CACHE_PATH: "/app/cache/videos"
- LORA_STORAGE_PATH: "/app/models/lora"
- OTLP_ENDPOINT: "http://jaeger:4317"

**Secrets:**
- LTX_API_KEY: "your-api-key-here" (placeholder)

**Resource Limits:**
- CPU Request: 500m
- CPU Limit: 2000m
- Memory Request: 1Gi
- Memory Limit: 4Gi

**Health Probes:**
- Liveness: `/health/live` (30s initial, 10s interval)
- Readiness: `/health/ready` (10s initial, 5s interval)

## Next Steps

1. **Resolve Image Build Issue**
   - Choose one of the resolution options above
   - Build and make the `visual-core:latest` image available to the cluster

2. **Update LTX API Key**
   - Replace placeholder API key with actual key from https://console.ltx.video
   ```bash
   kubectl create secret generic visual-core-secrets \
     --from-literal=LTX_API_KEY='actual-api-key' \
     --dry-run=client -o yaml | kubectl apply -n project-chimera -f -
   ```

3. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n project-chimera -l app=visual-core

   # Test health endpoints
   kubectl exec -n project-chimera deployment/visual-core -- curl -s http://localhost:8014/health/live
   kubectl exec -n project-chimera deployment/visual-core -- curl -s http://localhost:8014/health/ready
   ```

4. **Monitor HPA**
   ```bash
   kubectl get hpa -n project-chimera -w
   ```

## Deployment Files

- **Manifest:** `/home/ranj/Project_Chimera/services/visual-core/k8s-deployment.yaml`
- **Dockerfile:** `/home/ranj/Project_Chimera/services/visual-core/Dockerfile`
- **Source Code:** `/home/ranj/Project_Chimera/services/visual-core/main.py`

## Verification Commands

Once image is available and pods are running:

```bash
# Verify all resources
kubectl get all -n project-chimera -l app=visual-core

# Check pod logs
kubectl logs -n project-chimera -l app=visual-core --tail=50

# Port forward for local testing
kubectl port-forward -n project-chimera svc/visual-core 8014:8014

# Test service endpoint
curl http://localhost:8014/health/live
curl http://localhost:8014/health/ready
```

## Notes

- All Kubernetes manifests are properly configured and applied
- PVC is bound and ready for use
- HPA is configured but shows "unknown" metrics until pods are running
- Service is accessible but no ready endpoints due to image pull failure
- Security best practices implemented (non-root, dropped capabilities, read-only root filesystem could be added)

## Conclusion

The Kubernetes infrastructure is fully deployed and ready. The only remaining blocker is building and making the Docker image available to the cluster. Once the image is built and available (either locally or via registry), the pods should start successfully and the service will be operational.
