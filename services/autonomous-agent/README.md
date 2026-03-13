# Autonomous Agent Service

Autonomous agent orchestration service with Ralph Mode, GSD (Goal-Setting and Delegation), and Flow-Next architecture for persistent task execution with graceful degradation.

## Overview

The Autonomous Agent Service implements a sophisticated execution model for autonomous task completion through three core paradigms:

### Ralph Mode
Persistent execution loop that continues until task completion (promise) or maximum retry limit (backstop). Features:
- Non-blocking async execution with exponential backoff
- Fresh context loading for each retry attempt
- Graceful degradation with `BackstopExceededError`
- Configurable retry limits and backoff strategies

### GSD (Goal-Setting and Delegation)
Three-phase orchestration pipeline:
1. **Discuss Phase**: Extract structured requirements from natural language
2. **Plan Phase**: Create implementation plans with task dependencies
3. **Execute Phase**: Execute tasks with Ralph Mode persistence

### Flow-Next Architecture
State management paradigm preventing context rot:
- Fresh context per iteration (no memory carryover)
- External state persistence (STATE.md, PLAN.md, REQUIREMENTS.md)
- Session-based isolation with automatic cleanup

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional, for containerized deployment)
- Access to OpenTelemetry collector (optional)

### Local Development

```bash
# Navigate to service directory
cd services/autonomous-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration (optional for defaults)

# Run service
uvicorn main:app --reload --port 8008
```

### Docker Deployment

```bash
# Build image
docker build -t autonomous-agent:latest .

# Run container
docker run -d \
  --name autonomous-agent \
  -p 8008:8008 \
  -v $(pwd)/state:/app/state \
  -e OTLP_ENDPOINT=http://otel-collector:4317 \
  -e MAX_RETRIES=5 \
  autonomous-agent:latest
```

### Kubernetes Deployment

```bash
# Apply deployment manifests
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml

# Verify deployment
kubectl get pods -l app=autonomous-agent
kubectl get svc autonomous-agent
```

## API Endpoints

### Health Checks

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "autonomous-agent",
  "version": "1.0.0",
  "timestamp": "2026-03-13T12:00:00.000000"
}
```

#### `GET /metrics`
Prometheus metrics endpoint.
- Returns Prometheus text format metrics
- Includes task execution, phase duration, and active task metrics

### Task Execution

#### `POST /execute`
Execute a task using GSD Discuss→Plan→Execute pipeline with Ralph Mode.

**Request Body:**
```json
{
  "user_request": "Implement a REST API for user management",
  "requirements": ["Python", "FastAPI", "PostgreSQL"]
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-03-13T12:00:00.000000"
}
```

**Behavior:**
- Creates unique task ID
- Starts background execution pipeline
- Returns immediately for async polling
- Executes through three phases:
  1. **Discuss**: Extracts requirements (writes REQUIREMENTS.md)
  2. **Plan**: Creates implementation plan (writes PLAN.md)
  3. **Execute**: Executes with Ralph Mode (updates STATE.md)

#### `GET /execute/{task_id}`
Get status of an executing task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "phases_completed": ["discuss", "plan", "execute"],
  "requirements": {
    "goal": "Implement a REST API for user management",
    "constraints": ["Python", "FastAPI", "PostgreSQL"],
    "acceptance_criteria": []
  },
  "plan_tasks": ["Implement: REST API for user management"],
  "result": "Task completed successfully",
  "error": null,
  "retry_count": 2,
  "status": "complete"
}
```

**Status Values:**
- `pending`: Task queued, not started
- `in_progress`: Task executing
- `complete`: Task completed successfully
- `failed`: Task failed after exceeding backstop

### Service Status

#### `GET /status`
Get current autonomous agent status.

**Response:**
```json
{
  "current_task": "550e8400-e29b-41d4-a716-446655440000",
  "completed_tasks": [],
  "pending_tasks": [],
  "retry_count": 2,
  "last_updated": "2026-03-13T12:00:00.000000"
}
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                    (main.py)                                │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   GSD       │  │   Ralph     │  │  Flow-Next  │
│ Orchestrator│  │   Engine    │  │   Manager   │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  State Files    │
                │  - STATE.md     │
                │  - PLAN.md      │
                │  - REQUIREMENTS │
                └─────────────────┘
```

### GSD Orchestrator
Implements the Discuss→Plan→Execute→Verify lifecycle:
- **Discuss Phase**: Extracts structured requirements from user input
- **Plan Phase**: Creates implementation plans with task dependencies
- **Execute Phase**: Executes tasks with verification
- **Verification**: Spec compliance and code quality checks

### Ralph Engine
Persistent execution loop with backstop:
- Executes task until success or max retries
- Loads fresh context per retry (Flow-Next)
- Updates external state after each attempt
- Raises `BackstopExceededError` on backstop hit

### Flow-Next Manager
State management preventing context rot:
- Creates fresh sessions per iteration
- Manages external state files
- Implements session amnesia (automatic cleanup)

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `autonomous-agent` | Service identifier |
| `SERVICE_VERSION` | `1.0.0` | Service version |
| `PORT` | `8008` | HTTP server port |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry traces endpoint |
| `GIT_REPO_PATH` | `/app` | Git repository path |
| `GIT_BRANCH` | `main` | Git branch |
| `MAX_RETRIES` | `5` | Ralph Mode maximum retry backstop |
| `RETRY_DELAY_SECONDS` | `10` | Initial retry delay in seconds |
| `STATE_DIR` | `state` | State files directory |
| `REQUIREMENTS_FILE` | `state/REQUIREMENTS.md` | Requirements file path |
| `PLAN_FILE` | `state/PLAN.md` | Plan file path |
| `STATE_FILE` | `state/STATE.md` | State file path |

### State Files

The service maintains three state files in the `state/` directory:

- **REQUIREMENTS.md**: Structured requirements from Discuss phase
- **PLAN.md**: Implementation plan from Plan phase
- **STATE.md**: Current execution state and results

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test module
pytest tests/test_ralph_engine.py -v

# Run specific test
pytest tests/test_ralph_engine.py::test_ralph_engine_init -v
```

### Integration Tests

```bash
# Run integration tests (requires running service)
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=. --cov-report=html
```

### Test Coverage

Current coverage (as of Phase 4 completion):
- Unit tests: 95%+ coverage
- Integration tests: 85%+ coverage
- Critical paths: 100% coverage

## Monitoring Metrics

The service exposes Prometheus metrics on `/metrics`:

### Task Execution Metrics
- `autonomous_agent_task_executions_total`: Total task executions (label: status)
- `autonomous_agent_task_duration_seconds`: Task execution duration
- `autonomous_agent_active_tasks`: Current active tasks

### GSD Phase Metrics
- `autonomous_agent_gsd_phase_duration_seconds`: Duration per phase (label: phase)
- `autonomous_agent_gsd_phase_completed_total`: Phases completed (label: phase)

### Service Info
- `autonomous_agent_service_info`: Service metadata (labels: version)

### Ralph Engine Metrics
- Retry counts per task
- Backstop exceeded events
- Context load durations

### Alerting Rules

Key alerts configured (see `monitoring/prometheus-alerts.yaml`):
- **HighTaskFailureRate**: > 25% failure rate over 5m
- **HighTaskLatency**: > 30s average duration over 5m
- **BackstopExceeded**: Ralph Mode backstop exceeded
- **ServiceDown**: Health check failures

## Troubleshooting

### Task Not Completing

**Symptom:** Task stuck in `in_progress` status

**Diagnosis:**
```bash
# Check task status
curl http://localhost:8008/execute/{task_id}

# Check logs for retry count
docker logs autonomous-agent | grep "retry_count"
```

**Solutions:**
1. **Increase MAX_RETRIES**: Task may need more retries
   ```bash
   export MAX_RETRIES=10
   ```
2. **Check external state**: Verify state files are writable
   ```bash
   ls -la state/
   ```
3. **Review requirements**: Ensure task is well-defined

### Ralph Mode Backstop Exceeded

**Symptom:** Task status `failed` with `BackstopExceededError`

**Diagnosis:**
```bash
# Check retry count in response
curl http://localhost:8008/execute/{task_id} | jq '.retry_count'

# Check logs for error details
docker logs autonomous-agent | grep "BackstopExceededError"
```

**Solutions:**
1. **Increase backstop**: Raise `MAX_RETRIES` in configuration
2. **Fix underlying issue**: Address the root cause preventing success
3. **Break down task**: Split complex task into smaller subtasks

### State File Corruption

**Symptom:** Service fails to read/write state files

**Diagnosis:**
```bash
# Check state files
ls -la state/
cat state/STATE.md
```

**Solutions:**
1. **Reset state files**: Remove corrupted files and restart
   ```bash
   rm state/*.md
   systemctl restart autonomous-agent
   ```
2. **Check permissions**: Ensure service has write access
   ```bash
   chmod 755 state/
   ```
3. **Verify disk space**: Check available disk space
   ```bash
   df -h
   ```

### High Memory Usage

**Symptom:** Service consuming increasing memory over time

**Diagnosis:**
```bash
# Check memory usage
docker stats autonomous-agent

# Check for memory leaks in logs
docker logs autonomous-agent | grep "memory"
```

**Solutions:**
1. **Restart service**: Clear accumulated state
2. **Reduce MAX_RETRIES**: Limit retry attempts
3. **Clean state directory**: Remove old state files
4. **Monitor metrics**: Set up memory alerts

### Phase Duration Issues

**Symptom:** GSD phases taking too long

**Diagnosis:**
```bash
# Check phase duration metrics
curl http://localhost:8008/metrics | grep gsd_phase_duration
```

**Solutions:**
1. **Optimize requirements**: Simplify user requests
2. **Plan complexity**: Reduce task dependencies
3. **External services**: Check dependent service latency

## Development

### Code Structure

```
autonomous-agent/
├── main.py              # FastAPI application
├── config.py            # Configuration (Pydantic Settings)
├── models.py            # Pydantic request/response models
├── ralph_engine.py      # Ralph Engine (persistent execution)
├── gsd_orchestrator.py  # GSD Orchestrator (3-phase pipeline)
├── flow_next.py         # Flow-Next Manager (state management)
├── metrics.py           # Prometheus metrics
├── tracing.py           # OpenTelemetry setup
├── conftest.py          # Pytest configuration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image
├── k8s-deployment.yaml  # Kubernetes Deployment
├── k8s-service.yaml     # Kubernetes Service
├── .env.example         # Environment variables template
├── state/               # State files directory
│   ├── STATE.md         # Current execution state
│   ├── PLAN.md          # Implementation plan
│   └── REQUIREMENTS.md  # Structured requirements
└── tests/               # Test suite
    ├── test_ralph_engine.py
    ├── test_gsd_orchestrator.py
    ├── test_flow_next.py
    ├── test_main.py
    └── integration/
        └── test_e2e_task_execution.py
```

### Adding Features

1. **New GSD Phase**: Add method to `gsd_orchestrator.py`
2. **New API Endpoint**: Add route to `main.py`
3. **New Metrics**: Add metric to `metrics.py`
4. **New Models**: Add Pydantic model to `models.py`
5. **Tests**: Add tests to `tests/`

### Extending Ralph Engine

To add custom execution logic:

```python
from ralph_engine import RalphEngine, Task, Context, Result

class CustomRalphEngine(RalphEngine):
    async def execute_task(self, task: Task, context: Context) -> Result:
        # Custom execution logic
        try:
            # Execute task
            output = await self.custom_execution(task, context)
            return Result(success=True, data={"output": output})
        except Exception as e:
            return Result(success=False, error=str(e))
```

### Extending GSD Orchestrator

To add custom plan generation:

```python
from gsd_orchestrator import GSDOrchestrator, Requirements, Plan

class CustomGSDOrchestrator(GSDOrchestrator):
    def plan_phase(self, requirements: Requirements) -> Plan:
        # Custom planning logic
        tasks = self.create_custom_tasks(requirements)
        return Plan(tasks=tasks, estimated_hours=self.estimate(tasks))
```

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  autonomous-agent:
    build: .
    ports:
      - "8008:8008"
    volumes:
      - ./state:/app/state
    environment:
      - OTLP_ENDPOINT=http://otel-collector:4317
      - MAX_RETRIES=5
    restart: unless-stopped
```

### Kubernetes

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: autonomous-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: autonomous-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
