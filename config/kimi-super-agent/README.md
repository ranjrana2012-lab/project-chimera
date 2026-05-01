# Kimi Super-Agent Configuration

This directory contains configuration for the Kimi K2.6 super-agent service.

## Configuration Options

### kimi
- `model_name`: HuggingFace model identifier
- `vllm_endpoint`: vLLM service endpoint
- `max_tokens`: Maximum tokens per request
- `temperature`: Sampling temperature
- `top_p`: Nucleus sampling parameter

### grpc
- `host`: gRPC server host
- `port`: gRPC server port
- `max_workers`: Maximum gRPC worker threads
- `nemoclaw_endpoint`: Nemo Claw orchestrator endpoint

### memory
- `gpu_memory_fraction`: Fraction of GPU memory for vLLM
- `kv_cache_size_bytes`: KV cache size in bytes
- `max_concurrent_requests`: Maximum concurrent requests

### delegation
- `long_context_threshold_tokens`: Token threshold for long context delegation
- `enable_multimodal`: Enable multimodal processing
- `enable_agentic_coding`: Enable code generation

### chimera_agents
- Agent endpoints and timeouts for Chimera services
