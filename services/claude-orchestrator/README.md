# Claude Orchestrator

The supervisory control plane for Project Chimera - a comprehensive platform for AI-driven live theatre experiences.

## Overview

Claude Orchestrator serves as the primary control layer for Project Chimera, coordinating multiple AI services including dialogue generation, captioning, BSL translation, sentiment analysis, and show control. It implements a sophisticated state machine for operational modes and provides both REST API and CLI interfaces for operator control.

## Features

### Core Capabilities
- **State Machine Control**: STANDBY, CHECKING, CONTROL, ESCALATED, PAUSED modes
- **Health Monitoring**: Continuous health checks with configurable service monitoring
- **Policy Engine**: YAML-based governance with escalation rules and approval gates
- **Error Handling**: Automatic error detection, escalation, and resolution tracking
- **Ralph Loop**: Continuous autonomous execution with task queue and learnings
- **Multi-Channel Notifications**: Webhook, email, and log channels for alerts

### Integration
- **Nemo Claw Client**: HTTP/WebSocket communication with show orchestrator
- **Show State Tracking**: Real-time lifecycle monitoring (INACTIVE → STARTING → ACTIVE → ENDING)
- **LLM Integration**: AI-powered decision support using Anthropic Claude API

### Operator Interfaces
- **Web Dashboard**: Real-time responsive dashboard with WebSocket updates
- **CLI Tool**: Interactive command-line interface for system control
- **REST API**: Full API coverage for automation and integration

## Quick Start

### Local Development

```bash
# Start services with Docker Compose
docker-compose up -d

# Access the dashboard
open http://localhost:8010

# Use the CLI tool
./bin/cli
```

### Manual Build

```bash
# Build binaries
go build -o bin/orchestrator ./cmd/orchestrator
go build -o bin/cli ./cmd/cli

# Run with configuration
./bin/orchestrator --config config/config.yaml
```

### Docker Build

```bash
# Build image
docker build -f deploy/Dockerfile -t claude-orchestrator:latest .

# Run container
docker run -p 8010:8010 \
  -e CLAUDE_REDIS_URL=redis://localhost:6379 \
  -e CLAUDE_NEMOCLAW_BASE_URL=http://nemoclaw:8000 \
  claude-orchestrator:latest
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLAUDE_SERVICE_NAME` | No | `claude-orchestrator` | Service identifier |
| `CLAUDE_PORT` | No | `8010` | HTTP server port |
| `CLAUDE_HOST` | No | `0.0.0.0` | Server bind address |
| `CLAUDE_REDIS_URL` | Yes* | - | Redis connection URL |
| `CLAUDE_NEMOCLAW_BASE_URL` | Yes* | - | Nemo Claw service URL |
| `CLAUDE_STATE_DIR` | No | `/state/claude-orchestrator` | State persistence directory |
| `CLAUDE_POLICY_CONFIG_PATH` | No | `/config/policies.yaml` | Policy configuration file |
| `CLAUDE_LOG_LEVEL` | No | `info` | Logging level (debug/info/warn/error) |
| `CLAUDE_RALPH_LOOP_ENABLED` | No | `false` | Enable Ralph Loop continuous execution |
| `CLAUDE_API_KEY` | Yes* | - | Anthropic API key for LLM features |

*Required for full functionality

### Configuration Files

**`config/config.yaml`** - Main configuration:
```yaml
server:
  port: 8010
  host: "0.0.0.0"

services:
  - name: scenespeak-agent
    host: localhost
    port: 8001
    protocol: http
    critical: true

health_check:
  interval: 30s
  timeout: 10s

ralph_loop:
  enabled: true
  max_iterations: 0
```

**`config/policies.yaml`** - Policy governance:
```yaml
policies:
  - id: error-escalation
    name: Auto-Escalate Critical Errors
    trigger:
      type: severity_threshold
      severity: CRITICAL
    actions:
      - escalate
    auto_escalate: true
```

## Operational Modes

| Mode | Purpose | Auto-Transition |
|------|---------|-----------------|
| **STANDBY** | Idle mode, minimal activity | When show ends |
| **CHECKING** | Running health checks on all services | Before show starts |
| **CONTROL** | Active show control mode | When show is ACTIVE |
| **ESCALATED** | Error handling mode | Critical errors detected |
| **PAUSED** | Awaiting operator intervention | Manual operator action |

## API Endpoints

### Health Endpoints
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /api/status` - Full system status

### Mode Control
- `GET /mode/current` - Get current operational mode
- `POST /mode/transition` - Request mode transition
- `GET /mode/history` - Get mode transition history

### Health Monitoring
- `POST /health/check` - Trigger health check
- `GET /health/report` - Get latest health report

### Task Management
- `GET /tasks` - List all tasks
- `POST /tasks` - Create new task
- `PUT /tasks/:id/approve` - Approve task
- `PUT /tasks/:id/deny` - Deny task

### Error Management
- `GET /errors` - List active errors
- `POST /errors/:id/resolve` - Resolve error

## Testing

```bash
# Run all tests
go test -v -race ./...

# Run with coverage
go test -cover ./...

# Run specific package tests
go test -v ./internal/health/...

# Run integration tests
go test -v ./tests/integration/...
```

### Test Coverage

Current coverage (2026-04-01):
- config: 90.9%
- health: 76.0%
- policy: 57.6%
- nemoclaw: 51.4%
- error: 50.5%
- ralph: 31.7%
- mode: 27.1%
- state: 4.2%

## Deployment

### Kubernetes

```bash
# Apply manifests
kubectl apply -f deploy/k8s.yaml

# Check status
kubectl get pods -n chimera -l app=claude-orchestrator

# View logs
kubectl logs -f deployment/claude-orchestrator -n chimera
```

### Production Considerations

1. **TLS/SSL**: Enable HTTPS for production deployments
2. **RBAC**: Configure role-based access control
3. **Secrets**: Use Kubernetes Secrets for sensitive data
4. **HPA**: Horizontal Pod Autoscaler configured (2-5 pods)
5. **Monitoring**: Integrate with Prometheus and Grafana

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Human Operator                     │
│  - Web Dashboard (https://orchestrator.chimera)     │
│  - CLI Tool (orchestrator> status)                  │
│  - API Endpoints (/api/status, /api/mode, etc.)     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Claude Orchestrator                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         Supervisory Control Plane            │  │
│  │  - Mode Control (STANDBY/CHECKING/CONTROL)   │  │
│  │  - Policy Engine (escalation, approval)      │  │
│  │  - Error Handler (auto-escalate, resolution) │  │
│  │  - Ralph Loop (continuous execution)         │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │            Deterministic Adapters           │  │
│  │  - Nemo Claw Client (HTTP/WebSocket)        │  │
│  │  - Health Monitor (service checks)          │  │
│  │  - Show State Tracker (lifecycle events)    │  │
│  │  - LLM Client (AI-powered decisions)        │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Project Chimera Services                │
│  - Nemo Claw, SceneSpeak, Captioning, BSL           │
│  - Sentiment, Lighting/Sound/Music, Safety          │
└─────────────────────────────────────────────────────┘
```

## Documentation

- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Full implementation details
- **[TEST_REPORT.md](TEST_REPORT.md)** - Test results and coverage
- **[SESSION_SUMMARY_2026-04-01.md](SESSION_SUMMARY_2026-04-01.md)** - Latest session summary

## License

This implementation is part of Project Chimera and follows the project's licensing terms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass (`go test -race ./...`)
5. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.
