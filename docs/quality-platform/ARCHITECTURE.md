# Chimera Quality Platform - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHIMERA QUALITY PLATFORM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   TEST ORCHESTRATOR   │    │  CI/CD GATEWAY   │                  │
│  │  • Scheduler     │◄───┤│  • GitHub Int.   │                  │
│  │  • Parallel Exec │    ││  • GitLab Int.   │                  │
│  │  • Test Discovery│    ││  • Webhook Hand. │                  │
│  │  • Result Collector│  ││  • Status Updates │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌────────────────────────────────────────────────┐             │
│  │           TEST EXECUTION ENGINES               │             │
│  ├──────────────┬──────────────┬────────────────┤             │
│  │  Unit/Integ. │  Property    │  Mutation      │             │
│  │  (pytest)    │  (Hypothesis) │  (mutmut)      │             │
│  ├──────────────┼──────────────┼────────────────┤             │
│  │  Contract    │  Performance │  Chaos         │             │
│  │  (Pact)      │  (Locust)    │  (Chaos Mesh)  │             │
│  ├──────────────┼──────────────┼────────────────┤             │
│  │  Security    │  E2E         │  Fuzzing       │             │
│  │  (Bandit)    │  (Playwright)│  (AFL)         │             │
│  └──────────────┴──────────────┴────────────────┘             │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌────────────────────────────────────────────────┐             │
│  │          RESULT PROCESSING LAYER              │             │
│  │  • Coverage Analysis  • Mutation Score        │             │
│  │  • Performance Metrics • Security Scans        │             │
│  │  • Trend Aggregation   • Quality Gates         │             │
│  └─────────────────────┬──────────────────────────┘             │
│                        │                                        │
│           ┌────────────┴────────────┐                           │
│           ▼                         ▼                           │
│  ┌─────────────────┐      ┌─────────────────┐                 │
│  │  PostgreSQL     │      │  Redis          │                 │
│  │  • Test Runs    │      │  • Cache        │                 │
│  │  • Results      │      │  • Live Queue   │                 │
│  │  • Aggregates   │      │  • Pub/Sub      │                 │
│  │  • Trends       │      │  • Sessions     │                 │
│  └─────────────────┘      └─────────────────┘                 │
│           │                         │                           │
│           ▼                         ▼                           │
│  ┌────────────────────────────────────────────────┐             │
│  │              DASHBOARD SERVICE                  │             │
│  │  FastAPI Backend      React Frontend           │             │
│  │  • WebSocket API      • Live Test Runner       │             │
│  │  • GraphQL Queries    • Real-time Charts       │             │
│  │  • REST API           • Drill-down Views       │             │
│  │  • Auth/Permissions   • Alert Panels          │             │
│  └────────────────────────────────────────────────┘             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Test Orchestrator Service (port 8008)

**Responsibilities:**
- Test discovery via pytest collection
- Diff-based test selection (pytest-picked)
- Parallel execution scheduling
- Worker pool management
- Result collection and aggregation

### Dashboard Service (port 8009)

**Responsibilities:**
- Real-time WebSocket streaming of test execution
- Historical data visualization
- Quality gate evaluation
- Test analytics and trends

### CI/CD Gateway (port 8010)

**Responsibilities:**
- GitHub webhook handling
- GitLab webhook handling
- Commit status updates
- PR comments and notifications

## Data Flow

### Test Execution Flow

```
[1] TRIGGER (GitHub Push/PR, Manual, Scheduled)
        │
[2] TEST DISCOVERY & SELECTION (Scan codebase, git diff, select affected tests)
        │
[3] SCHEDULING (Create TestRun, allocate worker pools, enqueue tasks)
        │
[4] PARALLEL EXECUTION (Workers pop tasks, execute in isolation, stream results)
        │
[5] LIVE DASHBOARD UPDATES (Redis pub/sub → WebSocket → Real-time charts)
        │
[6] RESULT PROCESSING (Collect results, calculate metrics, evaluate gates)
        │
[7] NOTIFICATIONS (GitHub status, PR comment, Slack/Teams, email)
```

## Technology Stack

- **Backend:** FastAPI, SQLAlchemy, Redis, PostgreSQL
- **Frontend:** React, WebSocket, GraphQL, Recharts
- **Test Engines:** pytest, Hypothesis, mutmut, Pact, Locust, Chaos Mesh, Playwright, Bandit
