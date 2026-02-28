# Chimera Quality Platform - Design Document

**Date:** 2026-02-28
**Type:** Platform Architecture Design
**Status:** ✅ Design Approved

---

## Overview

This document outlines the design for the **Chimera Quality Platform** - a custom, unified testing and quality platform for Project Chimera. This platform will provide enterprise-grade testing infrastructure with real-time dashboards, CI/CD integration, and comprehensive quality gates.

**Vision:** A unified platform that orchestrates, executes, analyzes, and visualizes all testing for Project Chimera's 8 microservices, providing the confidence needed for production deployment.

---

## Requirements Summary

| Area | Choice |
|------|--------|
| **Primary Goal** | Production Readiness (CI/CD, mutation testing, contract testing, chaos engineering) |
| **Test Environment** | Full Staging (production-like k3s environment) |
| **Testing Gaps** | All: CI/CD, Advanced Test Quality, Performance/Resilience, Security |
| **Timeline** | 8-10 weeks comprehensive implementation |
| **Execution** | Run all tests on every commit (parallelized) |
| **Coverage Target** | 95% + dashboards, mutation survival <2% |
| **Platform Stack** | All-Python (FastAPI + React + PostgreSQL + Redis) |
| **Dashboards** | Live Streaming (WebSocket, real-time execution) |
| **Data Retention** | Smart (30-day detailed, aggregated forever) |

---

## Architecture

### System Architecture Diagram

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

                            │
                            ▼
                ┌───────────────────────┐
                │  FULL STAGING ENV     │
                │  (k3s Production-like)│
                └───────────────────────┘
```

---

## Components

### 1. Test Orchestrator Service

**File:** `platform/orchestrator/main.py`

**Responsibilities:**
- Test discovery via pytest collection
- Diff-based test selection (pytest-picked)
- Parallel execution scheduling
- Worker pool management
- Result collection and aggregation

**API Endpoints:**
- `POST /api/v1/run/start` - Start new test run
- `GET /api/v1/run/{run_id}` - Get run status
- `WebSocket /ws/run/{run_id}` - Live execution updates
- `GET /api/v1/tests/discover` - List all discoverable tests

**Key Classes:**
```python
class TestDiscovery:
    """Scan codebase and discover all tests."""
    async def discover_tests(self, path: str) -> List[TestSpec]
    async def build_dependency_graph(self, tests: List[TestSpec]) -> DAG

class TestScheduler:
    """Schedule tests for optimal execution."""
    async def schedule_run(self, commit_sha: str, test_filter: Optional[str]) -> ScheduledRun
    async def select_tests_for_commit(self, commit_sha: str) -> List[TestSpec]

class ParallelExecutor:
    """Execute tests in parallel across worker pools."""
    async def execute_tests(self, scheduled_run: ScheduledRun, max_workers: int) -> AsyncGenerator[TestResult, None]

class ResultCollector:
    """Collect and process test results."""
    async def publish_result(self, result: TestResult)
    async def calculate_coverage_delta(self, run_id: str, base_commit: str)
```

### 2. Dashboard Service

**File:** `platform/dashboard/main.py`

**Responsibilities:**
- Real-time WebSocket streaming of test execution
- Historical data visualization
- Quality gate evaluation
- Test analytics and trends

**API Endpoints:**
- `GET /api/v1/runs` - List test runs
- `GET /api/v1/runs/{run_id}` - Get run summary
- `GET /api/v1/trends` - Get trend data
- `POST /graphql` - GraphQL query endpoint
- `WebSocket /ws/run/{run_id}` - Live updates

**Key Classes:**
```python
class LiveTestStreamer:
    """Stream test execution results in real-time."""
    async def stream_test_run(self, run_id: str, websocket: WebSocket)

class DashboardQueries:
    """Queries for dashboard data."""
    async def get_run_summary(self, run_id: str) -> RunSummary
    async def get_trend_data(self, metric: str, days: int) -> List[TrendPoint]

class QualityGateEvaluator:
    """Evaluate if run meets quality standards."""
    async def evaluate_gates(self, run_id: str) -> GateResult
```

### 3. CI/CD Gateway

**File:** `platform/ci_gateway/main.py`

**Responsibilities:**
- GitHub webhook handling
- GitLab webhook handling
- Commit status updates
- PR comments and notifications

**API Endpoints:**
- `POST /webhooks/github` - GitHub webhooks
- `POST /webhooks/gitlab` - GitLab webhooks
- `GET /api/v1/status/{commit_sha}` - Get commit status

**Key Workflows:**
```python
async def handle_push(data: PushEvent):
    """Start test run on push to main branch."""
    run_id = await orchestrator.start_test_run(commit_sha=data["after"], branch=data["ref"], full_suite=True)
    await github.update_status(sha=data["after"], status="pending", url=f"{DASHBOARD_URL}/runs/{run_id}")

async def handle_pull_request(data: PullRequestEvent):
    """Start test run on PR with diff-based test selection."""
    changed_files = await github.get_changed_files(...)
    affected_tests = await test_selector.select_for_files(changed_files)
    run_id = await orchestrator.start_test_run(commit_sha=data["pull_request"]["head"]["sha"], test_filter=affected_tests)
    await github.post_comment(body=f"🧪 Test running: [View Live Results]({DASHBOARD_URL}/runs/{run_id})")
```

### 4. Database Schema

**File:** `platform/schema.sql`

**Tables:**

```sql
-- Test runs
CREATE TABLE test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_number SERIAL,
    commit_sha VARCHAR(40) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    triggered_by VARCHAR(255),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL,
    total_tests INT NOT NULL,
    passed INT,
    failed INT,
    skipped INT,
    duration_seconds INT,
    INDEX idx_commit_sha (commit_sha),
    INDEX idx_branch (branch),
    INDEX idx_started_at (started_at DESC)
);

-- Individual test results
CREATE TABLE test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    test_id VARCHAR(500) NOT NULL,
    test_file VARCHAR(500),
    test_class VARCHAR(255),
    test_function VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    duration_ms INT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    output TEXT,
    error_message TEXT,
    INDEX idx_run_id (run_id),
    INDEX idx_test_id (test_id),
    INDEX idx_status (status)
);

-- Coverage data
CREATE TABLE coverage_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    line_coverage DECIMAL(5,2),
    branch_coverage DECIMAL(5,2),
    lines_covered INT,
    lines_total INT,
    INDEX idx_run_service (run_id, service_name)
);

-- Mutation testing results
CREATE TABLE mutation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    total_mutations INT,
    killed_mutations INT,
    survived_mutations INT,
    timeout_mutations INT,
    mutation_score DECIMAL(5,2),
    INDEX idx_run_service (run_id, service_name)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    endpoint_name VARCHAR(255) NOT NULL,
    requests_per_second DECIMAL(10,2),
    avg_response_time_ms INT,
    p95_response_time_ms INT,
    p99_response_time_ms INT,
    error_rate DECIMAL(5,2),
    INDEX idx_run_endpoint (run_id, endpoint_name)
);

-- Aggregated daily summaries (for smart retention)
CREATE TABLE daily_summaries (
    date DATE NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    total_runs INT,
    avg_coverage DECIMAL(5,2),
    avg_mutation_score DECIMAL(5,2),
    avg_duration_seconds INT,
    PRIMARY KEY (date, service_name)
);
```

---

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

### Result Data Flow

```
Test Completes (Worker)
        │
        ▼
Publish to Redis (test:result channel)
        │
        ├───► WebSocket Server (Live Dashboard) → Push to clients
        │
        └───► Result Processor (Async Worker)
                │
                ▼
        Quality Gate Eval
                │
        ├───► PASSED → Notify, Archive, Update
        └───► FAILED → Alert, Block, Report
```

### Smart Retention Flow

```
Every night at 2:00 AM:
        │
        ├───► [AGE < 30 DAYS] Keep Everything
        │
        └───► [AGE ≥ 30 DAYS] Aggregate and Prune
                │
                ├───► Aggregate to daily summaries
                ├───► Archive detailed results (S3/Glacier)
                └───► Delete raw detailed data
```

---

## Error Handling

### Test Execution Failures

- **TestTimeoutError** - Test exceeded maximum duration
- **WorkerCrashError** - Worker process crashed
- **DependencyFailureError** - External service unavailable
- **ResourceExhaustionError** - System resources exhausted

### Platform Failures

- **Database Failure** - Switch to degraded mode, write-through cache
- **Redis Failure** - Fall back to database polling
- **Dashboard Crash** - Tests continue, results stored
- **Staging Failure** - Skip service-dependent tests

### Concurrency Management

- Resource locking for shared dependencies
- Semaphore limits (DB: 5, Kafka: 3, External API: 10)
- Test isolation (fresh connections, namespaces, topics)

---

## Testing Strategy

### Platform Test Pyramid

``                    E2E Tests (5% → 20 tests)
                            │
                    Integration Tests (25% → 100 tests)
                            │
                    Unit Tests (70% → 280 tests)

TOTAL: ~400 tests for the platform itself
```

### Quality Gates

- **Coverage:** ≥90% for platform code
- **Mutation Survival:** ≤5% (platform is critical)
- **Lint Issues:** 0 tolerance
- **Type Errors:** 0 tolerance

---

## Technology Stack

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **Redis** - Cache and pub/sub
- **PostgreSQL** - Primary database
- **asyncio** - Async execution

### Frontend
- **React** - UI framework
- **WebSocket** - Real-time updates
- **GraphQL** - Flexible queries
- **Recharts** - Data visualization

### Test Engines
- **pytest** - Test runner
- **Hypothesis** - Property testing
- **mutmut** - Mutation testing
- **Pact** - Contract testing
- **Locust** - Performance testing
- **Chaos Mesh** - Chaos engineering
- **Playwright** - E2E testing
- **Bandit** - Security scanning

---

## Success Criteria

- ✅ All 8 services with 95%+ test coverage
- ✅ Mutation survival <2% across codebase
- ✅ Real-time test execution visualization
- ✅ Automated CI/CD integration
- ✅ Performance baseline tracking
- ✅ Security vulnerability scanning
- ✅ Chaos engineering tests
- ✅ Comprehensive quality dashboards
- ✅ Smart data retention (30-day detailed)

---

## Estimated Deliverables

| Component | Files | Est. Lines |
|-----------|-------|------------|
| Orchestrator Service | 15 | ~3,500 |
| Dashboard Service | 12 | ~2,800 |
| CI/CD Gateway | 8 | ~1,500 |
| Database Schema | 3 | ~400 |
| React Frontend | 20 | ~4,000 |
| Platform Tests | 40 | ~6,000 |
| Documentation | 8 | ~2,000 |
| **TOTAL** | **~106** | **~20,200** |

---

*Design approved: 2026-02-28*
*Project Chimera - Chimera Quality Platform*
