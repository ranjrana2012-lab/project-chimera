# Dual-Stack Architecture: NemoClaw + Chimera

**Date:** 2026-03-22 (Updated: 2026-03-23)
**Status:** Revised Understanding - Host k3s Compatible, Docker-in-Docker Not Compatible

## Overview

This system runs **two independent NemoClaw implementations** side-by-side, each serving different purposes:

| Implementation | Purpose | Technology |
|----------------|---------|------------|
| **Official NVIDIA NemoClaw** | Secure sandboxed AI agent execution with OpenShell policy enforcement | OpenShell runtime, k3s, container-based isolation |
| **Chimera nemoclaw-orchestrator** | Show automation and agent coordination with privacy-preserving LLM routing | Custom Node.js service, Docker Compose |

Both stacks share the same **Nemotron 3 Super 120B** model served via vLLM as a local inference backend.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DGX Spark (ARM64)                                 │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Official NVIDIA NemoClaw                         │  │
│  │  ┌────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │  │
│  │  │ OpenClaw       │───▶│ OpenShell       │───▶│ k3s Cluster     │   │  │
│  │  │ Gateway        │    │ Runtime         │    │ (Sandboxed      │   │  │
│  │  │ :18789         │    │                 │    │  Agents)        │   │  │
│  │  └────────────────┘    └─────────────────┘    └─────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Nemotron vLLM Server                              │  │
│  │  ┌──────────────────────────────────────────────────────────────┐    │  │
│  │  │  nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4            │    │  │
│  │  │  NVFP4 quantization (4-bit)                                  │    │  │
│  │  │  120B params (12B active via LatentMoE)                     │    │  │
│  │  │  Port: 8012                                                 │    │  │
│  │  └──────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    ▲                                        │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Chimera nemoclaw-orchestrator                    │  │
│  │  ┌────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │  │
│  │  │ Privacy Router │───▶│ Agent           │───▶│ Chimera Services│   │  │
│  │  │                │    │ Coordination    │    │ (Show Control)  │   │  │
│  │  │ Tier 1: Z.AI   │    │                 │    │                 │   │  │
│  │  │ Tier 2: Nemotron│   │                 │    │                 │   │  │
│  │  │ Tier 3: Ollama │    │                 │    │                 │   │  │
│  │  └────────────────┘    └─────────────────┘    └─────────────────┘   │  │
│  │                                                                   Port: 9000 │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REVISED UNDERSTANDING (2026-03-23)

### Critical Discovery: Host k3s Works Perfectly

After extensive testing, we discovered:

**✅ CONFIRMED WORKING:**
- **Host k3s v1.34.5+k3s1** - Runs perfectly on DGX Spark ARM64 with cgroup v2
- All system pods (CoreDNS, metrics-server, etc.) - **No CrashLoopBackOff**
- GPU device plugin - **Working correctly**

**❌ INCOMPATIBLE:**
- **OpenShell's Docker-in-Docker gateway** - Fails with cgroup v2 issues on ARM64
- The embedded k3s inside Docker container cannot manage cgroups properly

### Root Cause Revision

**Original hypothesis:** k3s + ARM64 + cgroup v2 = Incompatible

**Revised understanding:** k3s + ARM64 + cgroup v2 = ✅ **Fully Compatible**

The problem is specifically **k3s running inside a Docker container** (Docker-in-Docker), which is the architecture OpenShell/NemoClaw requires.

### Updated Architecture Options

**Option A: Host k3s (Recommended)**
```
DGX Spark (ARM64, Ubuntu 24.04, cgroup v2)
  └── k3s v1.34.5+k3s1 (running directly on host) ✅
      ├── OpenClaw pods (can work with proper config)
      ├── Chimera services
      └── Nemotron vLLM
```

**Option B: Docker-in-Docker (Broken)**
```
DGX Spark
  └── Docker
      └── OpenShell gateway container
          └── Embedded k3s ❌ (cgroup v2 issues)
```

### Current Implementation Status

| Component | Technology | Status | Notes |
|-----------|------------|--------|-------|
| **Host k3s** | k3s v1.34.5+k3s1 | ✅ Working | Direct host installation |
| **Nemotron vLLM** | Docker container | ✅ Working | Port 8012 |
| **Chimera orchestrator** | Node.js + Docker | ✅ Working | Port 9000 |
| **OpenShell gateway** | Docker-in-Docker | ❌ Incompatible | Requires Docker container |

---

## Port Allocation

### Official NemoClaw (OpenShell)

| Port | Service | Description |
|------|---------|-------------|
| **18789** | OpenClaw Gateway | Main gateway API (default) |
| **18791** | OpenClaw Gateway | Secondary gateway port |
| **18792** | OpenClaw Gateway | Tertiary gateway port |
| **6443** | k3s API | Kubernetes API (if used externally) |
| **Dynamic** | k3s services | Sandboxes get dynamic ports |

### Chimera Stack

| Port | Service | Description |
|------|---------|-------------|
| **8000** | chimera-orchestrator | Main Chimera orchestrator |
| **8001** | chimera-scenespeak | Scene description agent |
| **8002** | chimera-captioning | Video captioning agent |
| **8003** | chimera-bsl | BSL (sign language) agent |
| **8004** | chimera-sentiment | Sentiment analysis agent |
| **8005** | chimera-lighting-sound-music | Audio/visual control |
| **8006** | chimera-safety-filter | Content moderation |
| **8007** | chimera-operator-console | Human operator interface |
| **8011** | chimera-music-generation | Music generation service |
| **8012** | **nemotron-vllm** | **Nemotron inference (shared)** |
| **9000** | **nemoclaw-orchestrator** | **Chimera's NemoClaw (Privacy Router)** |
| **3000** | chimera-grafana | Metrics dashboard |
| **6379** | chimera-redis | State store |

### Infrastructure

| Port | Service |
|------|---------|
| 2181 | chimera-zookeeper |
| 2379-2380 | chimera-etcd |
| 4317-4318 | chimera-jaeger (OTLP) |
| 5778 | chimera-jaeger |
| 9091-9092 | chimera-milvus, chimera-kafka |
| 16686 | chimera-jaeger UI |

### Reserved / Do Not Use

| Port | Owner | Notes |
|------|-------|-------|
| **11434** | Ollama | Local fallback LLM |
| 2222 | SSH | System SSH |
| 53 | DNS | System DNS |

---

## Integration Points

### Shared Resources

1. **Nemotron vLLM (Port 8012)**
   - Serves inference requests from BOTH stacks
   - OpenAI-compatible API (`/v1/chat/completions`, `/v1/completions`)
   - Model: `nvidia/nemotron-3-super`

2. **Ollama (Port 11434)**
   - Fallback LLM for Chimera's Privacy Router
   - Used when Nemotron is unavailable

3. **GPU Resources**
   - Both stacks share the same GPU via CUDA
   - vLLM configured with `--gpu-memory-utilization 0.6` to leave room

### Communication Between Stacks

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│   Official NemoClaw          Chimera nemoclaw-orchestrator            │
│        (Agent)                    (API Service)                       │
│           │                            │                              │
│           │                            │                              │
│           └────────────┬───────────────┘                              │
│                        ▼                                              │
│                Nemotron vLLM :8012                                     │
│                (Shared Inference)                                     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Important:** The two stacks operate **independently**. There is no direct API communication between them. They simply share the same Nemotron inference endpoint.

---

## Installation & Configuration

### Official NemoClaw Setup

```bash
# Clone repository
cd /tmp/NemoClaw
git clone https://github.com/NVIDIA/NemoClaw.git

# Install globally (requires sudo)
sudo npm install -g .

# Run setup wizard
nemoclaw setup-spark

# Onboard and configure providers
nemoclaw onboard
```

**Key Configuration Files:**
- `~/.nemoclaw/config.json` - Main configuration
- `~/.openshell/` - OpenShell runtime state
- `/tmp/NemoClaw/` - Source code

**Default Gateway Port:** 18789 (configurable via OpenShell)

### Chimera nemoclaw-orchestrator Setup

```bash
# Navigate to service directory
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator

# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f nemoclaw-orchestrator
```

**Key Configuration Files:**
- `services/nemoclaw-orchestrator/docker-compose.yml`
- `services/nemoclaw-orchestrator/.env` (if present)

### Nemotron vLLM Setup (Shared)

```bash
# Deploy vLLM container
/home/ranj/Project_Chimera/scripts/deploy-nemotron-vllm.sh

# Check health
curl http://localhost:8012/health

# Test inference
curl http://localhost:8012/v1/models
```

**Key Configuration Files:**
- `scripts/deploy-nemotron-vllm.sh`
- `.env.nemotron` (local/private/ignored NGC credentials and port config; not committed)
- `models/nemotron/` - Hugging Face cache

---

## Privacy Router Configuration

The Chimera nemoclaw-orchestrator implements a **3-tier fallback**:

```yaml
# docker-compose.yml excerpt
LOCAL_RATIO: 0.95                    # 95% local, 5% cloud
CLOUD_FALLBACK_ENABLED: "true"

# Tier 1: Z.AI GLM-4.7 (Primary Cloud)
ZAI_API_KEY: ${ZAI_API_KEY}
ZAI_PRIMARY_MODEL: glm-4.7

# Tier 2: Nemotron (Local - Shared)
NEMOTRON_ENABLED: "true"
NEMOTRON_ENDPOINT: http://host.docker.internal:8012
NEMOTRON_MODEL: nemotron-3-super-120b-a12b-nvfp4

# Tier 3: Ollama (Fallback Local)
DGX_ENDPOINT: http://host.docker.internal:11434
NEMOTRON_MODEL: llama3:instruct
```

---

## Startup Order

To ensure proper initialization, start services in this order:

1. **Infrastructure First**
   ```bash
   # Docker network and shared resources
   docker network inspect chimera-network || docker network create chimera-network
   ```

2. **Nemotron vLLM** (Shared Inference)
   ```bash
   /home/ranj/Project_Chimera/scripts/deploy-nemotron-vllm.sh
   # Wait for: "Service running on port 8012"
   ```

3. **Official NemoClaw** (if not already running)
   ```bash
   # Gateway starts automatically after onboard
   nemoclaw onboard  # or openshell gateway start
   ```

4. **Chimera Stack**
   ```bash
   cd /home/ranj/Project_Chimera/docker
   docker-compose up -d
   ```

---

## Health Checks

### Official NemoClaw

```bash
# Check OpenShell gateway
curl http://localhost:18789/health

# List sandboxes
openshell sandbox list

# Check gateway logs
openshell gateway logs
```

### Chimera nemoclaw-orchestrator

```bash
# Health endpoint
curl http://localhost:9000/health/live

# Check container
docker ps | grep nemoclaw-orchestrator
docker logs nemoclaw-orchestrator --tail 50
```

### Nemotron vLLM (Shared)

```bash
# Health check
curl http://localhost:8012/health

# List models
curl http://localhost:8012/v1/models

# Check container
docker ps | grep nemotron-vllm
docker logs nemotron-vllm --tail 50
```

---

## Troubleshooting

### Port Conflicts

If you see "port already in use" errors:

```bash
# Find what's using a port
sudo ss -tlnp | grep :PORT_NUMBER

# Common solutions:
# - Change the port in docker-compose.yml
# - Stop conflicting service: docker stop CONTAINER_NAME
# - Use openshell gateway destroy to reset NemoClaw
```

### GPU Memory Issues

If you see OOM errors:

```bash
# Check GPU usage
nvidia-smi

# Reduce vLLM GPU utilization (edit deploy-nemotron-vllm.sh)
--gpu-memory-utilization 0.5  # Reduce from 0.6

# Or reduce Nemotron container count
openshell sandbox stop SANDBOX_NAME
```

### OpenShell Gateway Won't Start

```bash
# Check for stale port forwards
openshell gateway destroy
openshell gateway start

# Or use the cgroup v2 fix (see /tmp/NemoClaw/spark-install.md)
```

---

## Key Differences Between Implementations

| Aspect | Official NemoClaw | Chimera nemoclaw-orchestrator |
|--------|-------------------|-------------------------------|
| **Primary Purpose** | Secure agent execution sandbox | Show automation coordination |
| **Runtime** | OpenShell (Docker-in-Docker) ❌ | Docker Compose ✅ |
| **Policy Enforcement** | OpenShell network policies | Privacy Router |
| **LLM Routing** | Direct to inference provider | 3-tier fallback system |
| **Architecture** | k3s + gateway + sandbox | Monolithic service |
| **Compatibility** | **INCOMPATIBLE with DGX Spark** | **COMPATIBLE with DGX Spark** |
| **Configuration** | `~/.nemoclaw/` + OpenShell state | `docker-compose.yml` |
| **Port** | 18789 (gateway) | 9000 (orchestrator) |
| **Source** | github.com/NVIDIA/NVIDIA/NemoClaw | Custom Chimera project |

### Compatibility Summary

**DGX Spark GB10 (ARM64, Ubuntu 24.04, cgroup v2):**

| Runtime | Status | Reason |
|---------|--------|-------|
| Host k3s (direct) | ✅ Working | Native cgroup v2 support |
| k3s in Docker (OpenShell) | ❌ Failing | Docker-in-Docker cgroup issues |
| Docker Compose | ✅ Working | No nested k3s required |

---

## References

- **Official NemoClaw:** https://github.com/NVIDIA/NemoClaw
- **Spark Install Guide:** `/tmp/NemoClaw/spark-install.md`
- **Nemotron vLLM Script:** `/home/ranj/Project_Chimera/scripts/deploy-nemotron-vllm.sh`
- **Chimera nemoclaw-orchestrator:** `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/`

---

## Summary

- **Two independent stacks** running side-by-side
- **No port conflicts** (NemoClaw: 18789, Chimera: 9000)
- **Shared Nemotron inference** on port 8012
- **Official NemoClaw** for sandboxed agent execution
- **Chimera nemoclaw-orchestrator** for show automation with privacy routing
