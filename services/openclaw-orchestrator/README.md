# OpenClaw Orchestrator

Central control plane for Project Chimera.

## Overview

The OpenClaw Orchestrator is the central coordination service that manages all skills and pipelines for Project Chimera.

## Features

- Skill Registry - Manages and loads all OpenClaw skills
- Pipeline Executor - Executes complex multi-skill pipelines
- Health Monitoring - Comprehensive health checking for all dependencies
- Metrics - Prometheus metrics for observability
- Tracing - OpenTelemetry integration for distributed tracing

## API Endpoints

### Health
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /health/startup` - Startup probe

### Orchestration
- `POST /api/v1/orchestration/invoke` - Invoke a single skill

### Skills
- `GET /api/v1/skills` - List available skills
- `GET /api/v1/skills/{name}` - Get skill metadata
- `POST /api/v1/skills/{name}/enable` - Enable a skill
- `POST /api/v1/skills/{name}/disable` - Disable a skill
- `POST /api/v1/skills/reload` - Reload all skills

### Pipelines
- `POST /api/v1/pipelines/execute` - Execute a pipeline
- `GET /api/v1/pipelines/status/{id}` - Get pipeline status
- `POST /api/v1/pipelines/define` - Define a new pipeline
- `DELETE /api/v1/pipelines/{id}` - Delete a pipeline

## Development

### Running locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m src.main
```

### Running tests
```bash
pytest tests/
```

## Configuration

See `.env.example` for configuration options.

Key configuration:
- `REDIS_HOST` - Redis server host
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka bootstrap servers
- `GPU_ENABLED` - Enable GPU support
- `SKILLS_PATH` - Path to skills directory
