# Kimi Super-Agent gRPC Protocol

This directory contains the gRPC protocol definitions for the Kimi K2.6 super-agent service.

## Generating Python Code

```bash
cd services/kimi-super-agent
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/kimi.proto
```

## Services

- **KimiSuperAgent**: Main service for delegation requests
  - `Delegate()`: Handle delegation requests from Nemo Claw
  - `HealthCheck()`: Health check endpoint
