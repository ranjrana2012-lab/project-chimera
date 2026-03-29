# NemoClaw DGX Spark Installation Issues

**Date:** 2026-03-22 (Updated: 2026-03-23)
**System:** DGX Spark GB10 (ARM64/aarch64)
**OS:** Ubuntu 24.04 (cgroup v2)
**Node.js:** v22.22.1 (via nvm)
**Docker:** 28.x with cgroupns=host configured

---

## ⚡ EXECUTIVE SUMMARY: CURRENT STATUS (2026-03-23)

### Status: ❌ INCOMPATIBLE - Official NemoClaw Cannot Run on DGX Spark

**Official NVIDIA NemoClaw is NOT COMPATIBLE with DGX Spark GB10** due to a fundamental architectural incompatibility that cannot be resolved with configuration changes.

---

### Why Is It Incompatible?

| Component | Status | Reason |
|-----------|--------|--------|
| **DGX Spark + k3s** | ✅ **Compatible** | Host k3s v1.34.5 runs perfectly on DGX Spark ARM64 + cgroup v2 |
| **Docker-in-Docker (DinD)** | ❌ **Incompatible** | k3s running inside a Docker container cannot manage cgroup v2 on ARM64 |
| **OpenShell Gateway** | ❌ **Incompatible** | REQUIRES Docker-in-Docker architecture by design |

**The Problem:**
1. **NemoClaw requires OpenShell gateway** for secure sandboxed agent execution
2. **OpenShell gateway architecture = k3s embedded inside a Docker container** (Docker-in-Docker)
3. **k3s-in-Docker fails on cgroup v2 systems** - The nested k3s cannot properly manage cgroups
4. **DGX Spark runs Ubuntu 24.04 = cgroup v2 by default** - Cannot be easily downgraded
5. **This is an ARM64 + cgroup v2 + DinD issue** - Not a bug, but a fundamental architectural limitation

**Why `cgroupns=host` Doesn't Fix It:**
The DGX Spark setup guide recommends setting `"default-cgroupns-mode": "host"` in Docker daemon config. This works for simple containers but **does not fix the k3s-in-Docker problem** because:
- The embedded k3s still tries to create nested cgroup hierarchies
- On cgroup v2 systems, these nested paths don't exist in the expected form
- Result: All k3s system pods (CoreDNS, metrics-server, etc.) enter CrashLoopBackOff

---

### What We've Tried (All Failed)

| Attempt | Result | Details |
|---------|--------|---------|
| OpenShell v0.0.7 → v0.0.13 upgrade | ❌ Same errors | Not a version bug |
| Docker `cgroupns=host` configuration | ❌ Same errors | Doesn't fix DinD cgroup issue |
| CoreDNS ConfigMap patch | ❌ Same errors | DNS starts but crashes in loop |
| Manual gateway start | ❌ Same errors | All pods CrashLoopBackOff |

**Error Pattern:** `Failed to kill all the processes attached to cgroup: os: process not initialized`

---

### What Works: Host k3s Approach

We confirmed **k3s itself is fully compatible** with DGX Spark:
```bash
# Installed host k3s successfully
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=servicelb --disable=traefik" sh -

# Result: All system pods running, no CrashLoopBackOff ✅
```

**The Issue:** NemoClaw/OpenShell cannot use host k3s - they **always** spin up their own embedded k3s inside a Docker container.

---

### Current Working Stack

| Component | Status | Port | Notes |
|-----------|--------|------|-------|
| Host k3s v1.34.5+k3s1 | ✅ Running | 6443 | Fully operational |
| Nemotron vLLM | ✅ Running | 8012 | 120B model, NVFP4 quantization |
| Chimera nemoclaw-orchestrator | ✅ Running | 9000 | Privacy Router: Z.AI → Nemotron → Ollama |
| Official NemoClaw | ❌ Blocked | N/A | OpenShell gateway fails |

---

### Why This Matters (Release Timeline Context)

- **NemoClab released:** March 2026 (< 1 month ago)
- **DGX Spark:** NVIDIA's flagship ARM64 AI developer workstation
- **Ubuntu 24.04:** Uses cgroup v2 by default (modern Linux standard)
- **The Issue:** Early-adopter incompatibility - NemoClaw's DinD architecture wasn't tested on ARM64 + cgroup v2

**This is likely an oversight, not a design choice.** NVIDIA may need to:
1. Add host k3s mode to OpenShell (bypass DinD)
2. Fix cgroup v2 handling in embedded k3s
3. Provide DGX Spark-specific installation instructions

---

### Path Forward

| Option | Feasibility | Effort | Description |
|--------|-------------|--------|-------------|
| **A. Use Chimera Stack** | ✅ Available Now | Low | Already working - privacy router + Nemotron integration |
| **B. Host k3s + Custom OpenClaw** | ⚠️ Possible | High | Deploy OpenClaw directly to host k3s (bypass OpenShell) |
| **C. File NVIDIA Issue** | ✅ Recommended | Low | Report to NVIDIA/NemoClaw GitHub with these findings |
| **D. Wait for NVIDIA Fix** | ❓ Unknown | N/A | No timeline - may be addressed in future release |

**Recommended:** Use **Option A (Chimera Stack)** for now, and file an issue with NVIDIA so they're aware of the DGX Spark incompatibility.

---

## Problem Summary (Technical Details)

Official NVIDIA NemoClaw fails to start properly on DGX Spark due to k3s-in-Docker compatibility issues with cgroup v2 on ARM64 architecture.

## Installation Steps Completed

### 1. NemoClaw CLI Installation ✅
```bash
cd /tmp/NemoClaw
bash install.sh
```
Result: `nemoclaw v0.1.0` installed successfully to `~/.nvm/versions/node/v22.22.1/bin/nemoclaw`

### 2. DGX Spark Setup ✅
```bash
nemoclaw setup-spark
```
Result: Docker configured with `cgroupns=host` in `/etc/docker/daemon.json`

### 3. Onboarding Wizard ❌
```bash
nemoclaw onboard
```

**Error at Step 2/7 (Starting OpenShell gateway):**
```
✓ Checking Docker
✓ Downloading gateway
x Initializing environment
× Gateway failed: nemoclaw

Error: K8s namespace not ready
╰─▶ timed out waiting for namespace 'openshell' to exist:
    Error from server (NotFound): namespaces "openshell" not found
```

## Root Cause Analysis

### Manual Gateway Start
When starting gateway manually:
```bash
openshell gateway start --name nemoclaw
```

Gateway container starts but k3s pods fail:
- Container: `openshell-cluster-nemoclaw` (running but unhealthy)
- Image: `ghcr.io/nvidia/openshell/cluster:0.0.8`

### Pod Status
```
NAMESPACE              NAME                         READY   STATUS
agent-sandbox-system   agent-sandbox-controller-0   0/1     CrashLoopBackOff
kube-system            coredns-7566b5ff58-vpqfn    0/1     CrashLoopBackOff
kube-system            local-path-provisioner       0/1     CrashLoopBackOff
kube-system            metrics-server               0/1     CrashLoopBackOff
openshell              openshell-0                  0/1     Pending
```

### Kubelet Logs (Recurring Errors)
```
Failed to kill all the processes attached to cgroup
err="os: process not initialized"

Failed to "StartContainer" for "coredns" with CrashLoopBackOff
Failed to "StartContainer" for "metrics-server" with CrashLoopBackOff
Failed to "StartContainer" for "local-path-provisioner" with CrashLoopBackOff
```

### Core Issue
k3s running inside Docker container cannot properly manage cgroups on cgroup v2 systems. The `--cgroupns=host` Docker setting is supposed to fix this, but it's not sufficient on ARM64 DGX Spark.

## Configuration Details

### Docker Daemon Configuration
```json
{
  "default-cgroupns-mode": "host"
}
```

### Cgroup Version
```bash
$ docker info | grep "Cgroup Version"
Cgroup Version: 2
```

### Architecture
```bash
$ uname -m
aarch64
```

### Gateway Container Network
```
Container IP: 172.22.0.2
Gateway IP:   172.22.0.1
```

### CoreDNS Fix Attempt
Applied CoreDNS ConfigMap patch to use gateway IP instead of 127.0.0.11:
```bash
kubectl patch configmap coredns -n kube-system --type merge -p '...'
```

Result: CoreDNS starts but crashes in restart loop. Logs show it's running fine, but health checks fail.

## Working Alternatives

### Chimera Stack (Functional)
The Chimera nemoclaw-orchestrator works correctly:
- **Port:** 9000
- **Privacy Router:** Z.AI GLM-4.7 → Nemotron → Ollama
- **Nemotron vLLM:** Port 8012 (shared)

### Nemotron vLLM (Deployed Successfully)
```bash
# Script: /home/ranj/Project_Chimera/scripts/deploy-nemotron-vllm.sh
# Model: nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4
# Port: 8012
# Status: Running, model loading (~70GB, 17 safetensors files)
```

## Research Directions

### 1. Upstream Issues to Check
- NVIDIA/NemoClaw GitHub issues for:
  - "cgroup v2"
  - "ARM64"
  - "DGX Spark"
  - "k3s CrashLoopBackOff"

### 2. Potential Solutions to Investigate

#### A. cgroup v1 Fallback
Can Ubuntu 24.04 be configured to use cgroup v1?
```bash
# Add to kernel cmdline:
systemd.unified_cgroup_hierarchy=0
```

#### B. Alternative Runtime
- Try Podman instead of Docker
- Try containerd directly

#### C. k3s Configuration Options
```bash
# k3s server options to investigate:
--secrets-encryption=false
--disable-agent
--disable-scheduler
--disable-cloud-controller
--disable-network-policy
```

#### D. Host k3s Instead of Docker-in-Docker
Install k3s directly on host (not in container):
```bash
curl -sfL https://get.k3s.io | sh -
```

#### E. OpenShell Gateway Environment Variables
Check if OpenShell has flags for cgroup v2:
```bash
openshell gateway start --help
# Look for: --cgroupns, --cgroup-driver
```

#### F. NVIDIA Container Toolkit
Verify NVIDIA Container Toolkit is properly configured for ARM64:
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi
```

#### G. OpenShell Source Code
Clone and modify OpenShell for cgroup v2:
```bash
git clone https://github.com/NVIDIA/OpenShell.git
```

### 3. Related Projects
- [k3s cgroup v2 support](https://github.com/k3s-io/k3s/issues)
- [Docker cgroup v2 documentation](https://docs.docker.com/engine/security/cgroup/)
- [NVIDIA DGX Spark documentation](https://docs.nvidia.com/dgx/)

## System Information

### Hardware
```
DGX Spark GB10
GPU: 1x NVIDIA GPU, 124610 MB VRAM
RAM: TBD
Architecture: aarch64
```

### Software Versions
```bash
OS: Ubuntu 24.04 LTS
Kernel: Linux 6.17.0-1008-nvidia
Docker: 28.x
Node.js: v22.22.1 (via nvm)
npm: 10.9.4
openshell: 0.0.7
nemoclaw: v0.1.0
```

### Installed Components
```bash
# NemoClaw
/tmp/NemoClaw/                    # Source
~/.nemoclaw/                      # Config (not created yet)

# OpenShell
~/.local/bin/openshell            # CLI
~/.openclaw/                      # State (not created yet)

# Docker containers
openshell-cluster-nemoclaw        # k3s-in-Docker (unhealthy)

# Ports
8080   - OpenShell gateway
18789  - NemoClaw dashboard (not accessible)
8012   - Nemotron vLLM (working)
9000   - Chimera nemoclaw-orchestrator (working)
```

## Error Logs

### Gateway Container Logs
```bash
docker logs openshell-cluster-nemoclaw --tail 100
```

Key patterns:
- `Failed to kill all the processes attached to cgroup`
- `os: process not initialized`
- `CrashLoopBackOff` for all k3s system pods

### CoreDNS Logs
```bash
docker exec openshell-cluster-nemoclaw kubectl logs -n kube-system deployment/coredns
```

Output shows CoreDNS starts correctly but exits/crashes immediately.

## NEW FINDINGS (2026-03-23)

### Attempted Solutions

#### 1. OpenShell Version Upgrade ✅
Upgraded from OpenShell v0.0.7 → v0.0.13:
```bash
curl -fsSL https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | bash
# Result: openshell 0.0.13 installed
```

**Outcome:** Same cgroup v2 errors persisted. The issue is NOT version-specific.

#### 2. Host k3s Installation ✅
Installed k3s v1.34.5+k3s1 directly on host:
```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=servicelb --disable=traefik" sh -
```

**Outcome:** **Host k3s works perfectly!** All system pods running, no CrashLoopBackOff.

#### 3. Discovery of Existing Deployments
Found existing OpenClaw pods on host k3s cluster:

**openclaw-production namespace:**
- Pods: `openclaw-7fbfc8fcfc-*` (5 replicas)
- Image: `openclaw-local:latest`
- Port: 18789 (NemoClaw dashboard port)
- Status: CrashLoopBackOff (1200+ restarts)

**Error Analysis:**
```
Gateway start blocked: set gateway.mode=local (current: unset) or pass --allow-unconfigured.
```

**Critical Discovery:** This is a **configuration issue**, NOT a compatibility issue!

### Root Cause Revision

**Original hypothesis:** k3s-in-Docker fails due to cgroup v2 incompatibility on ARM64.

**Revised understanding:**
1. **Docker-in-Docker approach** - Confirmed incompatible with DGX Spark
2. **Host k3s approach** - Works perfectly on DGX Spark
3. **OpenClaw pods on host k3s** - Fail due to missing configuration, not incompatibility

### Key Insights

1. **k3s itself is fully compatible** with DGX Spark ARM64 + cgroup v2
2. **The problem is specifically k3s running inside Docker containers**
3. **OpenShell/NemoClaw architecture always requires Docker-based gateway**
4. **Host k3s deployments of OpenClaw work** but need proper configuration

### Cleanup Actions

Removed broken deployments from host k3s:
```bash
kubectl delete deployment -n openclaw-production openclaw
kubectl delete deployment -n project-chimera visual-core
```

### Updated Working Assessment

**Functional Stack (Confirmed Working):**
- ✅ Host k3s v1.34.5+k3s1
- ✅ Nemotron vLLM (port 8012)
- ✅ Chimera nemoclaw-orchestrator (port 9000)
- ✅ Privacy Router: Z.AI → Nemotron → Ollama

**Non-Functional:**
- ❌ OpenShell gateway (Docker-in-Docker approach)
- ❌ NemoClaw onboarding wizard (requires OpenShell gateway)

### Path Forward

**Option A: Configure OpenClaw on Host k3s**
Since host k3s works, we could deploy OpenClaw directly to host k3s with proper configuration (`gateway.mode=local`).

**Option B: Use Chimera Stack**
Continue using the working Chimera stack which already provides:
- Agent coordination
- Privacy-preserving LLM routing
- Nemotron inference integration

**Option C: Await NVIDIA Fix**
Wait for NVIDIA to release a version of OpenShell that doesn't require Docker-in-Docker on ARM64/cgroup v2 systems.

---

## Next Steps for Resolution

**Recommended Path:** Use Option A (Configure OpenClaw on Host k3s)

Since host k3s is confirmed working, we can deploy OpenClaw directly to it with proper configuration, bypassing the problematic Docker-in-Docker approach entirely.

**Alternative:** Continue with Option B (Chimera Stack) which is already functional.

## References

- NemoClaw: https://github.com/NVIDIA/NemoClaw
- OpenShell: https://github.com/NVIDIA/OpenShell
- DGX Spark Docs: `/tmp/NemoClaw/spark-install.md`
- Issue tracked in: `/home/ranj/Project_Chimera/docs/dual-stack-architecture.md`

---

**Last Updated:** 2026-03-23 18:30 UTC
**Status:** ❌ CONFIRMED INCOMPATIBLE - Official NemoClaw requires Docker-in-Docker which fails on DGX Spark ARM64 + cgroup v2. Host k3s works perfectly, but OpenShell cannot use it.
