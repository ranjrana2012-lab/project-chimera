# Kimi K2.6 Super-Agent Integration Design

**Date:** 2026-05-01
**Author:** Project Chimera Technical Lead
**Status:** Design Pending Approval

## Overview

This design specifies the integration of **Kimi K2.6** (Moonshot AI's 1T parameter Mixture-of-Experts model) as a super-orchestrator for Project Chimera's existing agent ecosystem on the NVIDIA DGX Spark GB10 ARM64 platform with 128GB GPU VRAM.

### Problem Statement

Project Chimera currently uses a flat agent architecture where Nemo Claw orchestrates agents directly. Complex workflows requiring long context reasoning, multimodal processing, or agentic coding capabilities cannot be handled efficiently by the existing agent pool.

### Solution

Add **Kimi K2.6** as a hierarchical super-agent that Nemo Claw delegates to for capability-based workflows. Kimi K2.6 processes complex requests and coordinates Chimera agents (sentiment, translation, scenespeak, safety) as needed.

### Constraints

- Must fit within 128GB GPU VRAM with headroom for existing agents
- Must integrate with existing Nemo Claw orchestrator via gRPC
- Must support native INT4 quantization via vLLM
- Must be ARM64-compatible for DGX Spark GB10

---

## Architecture

### High-Level Flow

```
User Request
    │
    ▼
Nemo Claw Orchestrator (Top-level routing)
    │
    ├── Simple Workflows ──► Chimera Agents (direct)
    │
    └── Capability Match ──► Kimi K2.6 Super-Agent
                                │
                                ├── Chimera Agents (coordinated)
                                └── Direct Response
```

### Delegation Triggers

Nemo Claw delegates to Kimi K2.6 when the request requires:

| Capability | Trigger | Example |
|------------|---------|---------|
| **Long Context** | >8K tokens, multi-scene reasoning | "Analyze 3 hours of performance data" |
| **Multimodal Input** | Video, image, audio processing | "Process this audience video feedback" |
| **Agentic Coding** | Dynamic code/behavior generation | "Create a new agent that combines X + Y" |

---

## Components

### New Services

#### `services/kimi-super-agent/`

**Purpose:** Kimi K2.6 super-agent gRPC server

| File | Purpose |
|------|---------|
| `kimi_orchestrator.py` | Main gRPC server, handles delegation requests |
| `kimi_client.py` | vLLM client for Kimi K2.6 inference |
| `agent_coordinator.py` | Manages Chimera agent delegation |
| `capability_detector.py` | Determines if request requires Kimi's capabilities |
| `code_generator.py` | Handles agentic code generation |
| `multimodal_processor.py` | Processes video/image/audio inputs |
| `proto/kimi.proto` | gRPC service definitions |
| `Dockerfile` | ARM64 container definition |

#### `services/nemoclaw-orchestrator/delegation/`

**Purpose:** Nemo Claw integration for Kimi delegation

| File | Purpose |
|------|---------|
| `kimi_delegate.py` | Delegation logic to Kimi K2.6 |
| `capability_checker.py` | Evaluates if request needs Kimi |
| `grpc_kimi_client.py` | gRPC client for Kimi communication |

### Configuration

#### `config/kimi-super-agent/config.yaml`

```yaml
kimi:
  model_name: "moonshotai/Kimi-K2.6"
  vllm_endpoint: "http://kimi-vllm:8012"
  max_tokens: 32768
  temperature: 0.7
  top_p: 0.9

grpc:
  port: 50052
  nemoclaw_endpoint: "nemoclaw-orchestrator:50051"

memory:
  gpu_memory_fraction: 0.55
  kv_cache_size_bytes: 10737418240  # 10GB

delegation:
  long_context_threshold_tokens: 8192
  enable_multimodal: true
  enable_agentic_coding: true
```

---

## Data Flow & Protocol

### Request Flow

1. **User Request** → Nemo Claw
2. Nemo Claw evaluates capability match
3. If matched → gRPC call to Kimi Super-Agent
4. Kimi K2.6 processes via vLLM
5. Kimi coordinates Chimera agents as needed
6. Response via gRPC → Nemo Claw → User

### gRPC Protocol

**File:** `services/kimi-super-agent/proto/kimi.proto`

```protobuf
syntax = "proto3";

package kimi;

service KimiSuperAgent {
  rpc Delegate(DelegationRequest) returns (DelegationResponse);
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message DelegationRequest {
  string request_id = 1;
  string user_input = 2;
  repeated MultimodalContent multimodal_content = 3;
  ContextMetadata context = 4;
  CapabilityHint capability_hint = 5;
}

message MultimodalContent {
  ContentType type = 1;
  bytes data = 2;
  string mime_type = 3;
  map<string, string> metadata = 4;
}

message DelegationResponse {
  string request_id = 1;
  string response = 2;
  repeated AgentInvocation agents_used = 3;
  GeneratedCode generated_code = 4;
  ResponseMetadata metadata = 5;
}

enum ContentType {
  TEXT = 0;
  IMAGE = 1;
  VIDEO = 2;
  AUDIO = 3;
}

enum CapabilityHint {
  NONE = 0;
  LONG_CONTEXT = 1;
  MULTIMODAL = 2;
  AGENTIC_CODING = 3;
}
```

---

## Memory Allocation

| Component | VRAM Usage |
|-----------|------------|
| Kimi K2.6 (Native INT4) | ~70 GB |
| KV Cache | ~10 GB |
| Multimodal Processors | ~5 GB |
| Chimera Agents (shared) | ~10-20 GB |
| **Headroom** | ~23 GB |
| **Total** | 128 GB |

---

## Deployment

### Model Download

**Script:** `scripts/download-kimi-k26.sh`

```bash
#!/bin/bash
set -e
MODEL_NAME="moonshotai/Kimi-K2.6"
CACHE_DIR="./models/kimi"
VENV=".venv_kimi"

python3 -m venv $VENV
source $VENV/bin/activate
pip install --upgrade huggingface_hub

python3 << EOF
from huggingface_hub import snapshot_download
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
snapshot_download(
    repo_id="${MODEL_NAME}",
    local_dir="${CACHE_DIR}",
    local_dir_use_symlinks=False,
    resume_download=True
)
EOF
```

### Docker Services

**File:** `docker-compose.dgx-spark.yml` (add)

```yaml
kimi-vllm:
  platform: linux/arm64
  image: vllm/vllm-openai:latest
  command: >
    --model /model
    --gpu-memory-utilization 0.55
    --max-model-len 32768
    --dtype bfloat16
    --quantization int4
    --port 8012
    --host 0.0.0.0
  gpus: all
  volumes:
    - ./models/kimi:/model
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8012/health"]
    interval: 30s
    timeout: 10s
    retries: 3

kimi-super-agent:
  platform: linux/arm64
  build: services/kimi-super-agent
  gpus: all
  environment:
    KIMI_VLLM_ENDPOINT: http://kimi-vllm:8012
    CHIMERA_RUNTIME_PROFILE: dgx-spark
  depends_on:
    - kimi-vllm
    - nemoclaw-orchestrator
```

### Startup Sequence

```bash
# 1. Download model
./scripts/download-kimi-k26.sh

# 2. Start vLLM
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm

# 3. Start super-agent
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-super-agent

# 4. Verify
curl http://localhost:8012/health
docker compose logs kimi-super-agent
```

---

## Testing

### Test Layers

| Layer | Purpose | Tool |
|-------|---------|------|
| Unit | Component logic | pytest |
| Integration | Nemo → Kimi → Chimera flow | docker-compose test |
| E2E | Full request/response | pytest + fixtures |
| Load | VRAM, concurrency, latency | locust |

### Key Test Scenarios

1. **Long Context Delegation:** 10K+ token requests
2. **Multimodal Processing:** Video/image/audio inputs
3. **Agentic Code Generation:** Dynamic agent creation
4. **Chimera Coordination:** Multi-agent orchestration
5. **VRAM Validation:** Ensure <85GB usage

### Validation Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Model present | `ls ./models/kimi/` | Files exist |
| vLLM healthy | `curl localhost:8012/health` | 200 OK |
| gRPC listening | `grpcurl -plaintext localhost:50052 list` | Services |
| Delegation works | Integration test | Correct routing |
| VRAM in bounds | `nvidia-smi` | <85GB |

---

## Success Criteria

- [ ] Kimi K2.6 model downloaded and verified
- [ ] vLLM serving with <85GB VRAM usage
- [ ] Nemo Claw successfully delegates capability-based requests
- [ ] gRPC communication between Nemo and Kimi
- [ ] Kimi coordinates Chimera agents correctly
- [ ] Multimodal processing functional
- [ ] Agentic code generation produces valid Python
- [ ] All integration tests passing
- [ ] VRAM stays within budget under load

---

## Open Questions

None at this time.

---

## References

- [Moonshot AI Kimi-K2.6](https://huggingface.co/moonshotai/Kimi-K2.6)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Project Chimera DGX Setup Guide](../guides/DGX_SPARK_SETUP.md)
