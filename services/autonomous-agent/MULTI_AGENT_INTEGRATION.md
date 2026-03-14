# Multi-Agent Integration for Autonomous Agent

This directory contains the integration between the autonomous-agent service and OpenClaw Orchestrator, enabling VMAO-style multi-agent task execution.

## Quick Start

### 1. Configuration

**OpenClaw Orchestrator (services/openclaw-orchestrator/.env):**
```bash
autonomous_agent_url=http://localhost:8008
```

**Autonomous Agent (services/autonomous-agent/.env):**
```bash
enable_multi_agent=true
openclaw_url=http://localhost:8000
```

### 2. Start Services

```bash
# Terminal 1: OpenClaw Orchestrator
cd services/openclaw-orchestrator
python main.py

# Terminal 2: Autonomous Agent
cd services/autonomous-agent
python main.py
```

### 3. Run Demo

```bash
cd services/autonomous-agent
python demo_multi_agent.py
```

## New Components

### OpenClaw Client (`openclaw_client.py`)

Enables autonomous agent to call other specialized agents through OpenClaw.

**Key Features:**
- Skill discovery from OpenClaw
- Single and parallel agent invocation
- Health checking
- Show status queries

**Usage:**
```python
from openclaw_client import get_openclaw_client

client = get_openclaw_client()

# Discover available skills
skills = await client.get_available_skills()

# Call single agent
result = await client.call_agent(
    skill="generate_dialogue",
    input_data={"scene": "scene1"}
)

# Parallel calls (VMAO dependency-aware execution)
results = await client.call_agent_parallel([
    ("generate_dialogue", {"scene": "scene1"}),
    ("captioning", {"audio": "audio.wav"})
])
```

### VMAO Verifier (`vmao_verifier.py`)

Implements verification phase from VMAO (Verified Multi-Agent Orchestration) framework.

**Key Features:**
- Plan verification (goal alignment, constraints, dependencies)
- Execution result quality assessment
- Replanning triggers
- Quality metrics (completeness, accuracy, relevance, efficiency)

**Usage:**
```python
from vmao_verifier import get_verifier

verifier = get_verifier()

# Verify plan
plan_result = await verifier.verify_plan(plan, requirements)

# Verify execution result
result = await verifier.verify_execution_result(
    result=execution_result,
    requirements=requirements,
    plan=plan
)

# Check if replanning needed
if await verifier.should_replan(result):
    suggestions = await verifier.generate_replan_suggestions(result)
```

## New API Endpoints

### Autonomous Agent (Port 8008)

**List Available Agents:**
```bash
GET /api/agents

Response:
{
  "enabled": true,
  "openclaw_url": "http://localhost:8000",
  "agents": [
    {"name": "generate_dialogue", "description": "...", "enabled": true},
    {"name": "captioning", "description": "...", "enabled": true}
  ],
  "total": 2
}
```

**Check Dependencies Health:**
```bash
GET /api/health/dependencies

Response:
{
  "multi_agent_enabled": true,
  "dependencies": {
    "openclaw_orchestrator": {"healthy": true, "url": "..."}
  },
  "overall_healthy": true
}
```

**Multi-Agent Demo:**
```bash
POST /api/demo/multi-agent

Response:
{
  "demo": "multi-agent_workflow",
  "total_calls": 2,
  "successful": 2,
  "total_execution_time": 2.5,
  "results": [...],
  "vmao_framework": "Plan-Execute-Verify-Replan"
}
```

### OpenClaw Orchestrator (Port 8000)

**New Skill:**
- `autonomous_execution`: Routes autonomous task execution to autonomous-agent service

**Updated Endpoints:**
- `GET /skills`: Now includes `autonomous_execution`
- `GET /api/skills`: Lists `autonomous_execution` with metadata
- `POST /v1/orchestrate`: Routes `autonomous_execution` skill to autonomous-agent

## VMAO Framework

The integration implements the VMAO (Verified Multi-Agent Orchestration) framework:

### 1. Plan Phase
- Decompose complex tasks into subtasks
- Identify dependencies between subtasks
- Create DAG-based execution plan

### 2. Execute Phase
- Execute subtasks using specialized agents
- Support parallel execution of independent tasks
- Dependency-aware task scheduling

### 3. Verify Phase
- LLM-based quality verification
- Check results against requirements
- Assess completeness, accuracy, relevance

### 4. Replan Phase
- Trigger replanning if quality thresholds not met
- Generate improvement suggestions
- Iterate until quality satisfied

## Testing

### Integration Tests

```bash
cd services/autonomous-agent
pytest tests/integration/test_multi_agent_integration.py -v
```

**Test Coverage:**
- OpenClaw client functionality
- VMAO verifier functionality
- GSD orchestrator with verification
- End-to-end multi-agent workflows
- VMAO Plan-Execute-Verify-Replan cycle

### Manual Testing

**1. Test OpenClaw routing to autonomous-agent:**
```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "autonomous_execution",
    "input": {"user_request": "Test task"}
  }'
```

**2. List available agents:**
```bash
curl http://localhost:8008/api/agents
```

**3. Check multi-agent health:**
```bash
curl http://localhost:8008/api/health/dependencies
```

**4. Run multi-agent demo:**
```bash
curl -X POST http://localhost:8008/api/demo/multi-agent
```

## Architecture

```
User Request
    ↓
OpenClaw Orchestrator (Skill Routing)
    ↓
Autonomous Agent (GSD Framework)
    ↓
┌─────────────────────────────────────┐
│  Plan Phase                          │
│  - Task decomposition                │
│  - DAG construction                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Execute Phase                       │
│  - Call specialized agents           │
│  - Parallel execution                │
│  (via OpenClaw)                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Verify Phase (VMAO)                 │
│  - Quality assessment                │
│  - Requirement checking              │
│  - Replanning trigger                │
└─────────────────────────────────────┘
    ↓
Aggregated Result
```

## Benefits

1. **Enhanced Capabilities**: Autonomous agent can delegate to specialized agents
2. **Improved Reliability**: Ralph Engine + VMAO verification ensures quality
3. **Better Performance**: Parallel execution of independent tasks
4. **Framework Alignment**: VMAO Plan-Execute-Verify-Replan

## Documentation

- Full integration documentation: `/docs/plans/2026-03-14-autonomous-agent-integration.md`
- VMAO Paper: arXiv:2603.11445 (Verified Multi-Agent Orchestration)
- OpenClaw README: `/services/openclaw-orchestrator/README.md`
- Autonomous Agent README: `/services/autonomous-agent/README.md`

## Troubleshooting

**Issue: Multi-agent mode not enabled**
- Solution: Set `enable_multi_agent=true` in autonomous-agent `.env`

**Issue: Cannot connect to OpenClaw**
- Solution: Check OpenClaw is running on port 8000
- Solution: Verify `openclaw_url` in autonomous-agent `.env`

**Issue: Agent calls failing**
- Solution: Check specialized agents are running
- Solution: Use `/api/health/dependencies` to diagnose

**Issue: Verification failing**
- Solution: Check VMAO verifier logs
- Solution: Adjust quality thresholds if needed

## Future Enhancements

1. LLM-based verification (replace simplified implementation)
2. Dynamic DAG construction
3. Agent discovery and capability negotiation
4. Fault tolerance with automatic failover
