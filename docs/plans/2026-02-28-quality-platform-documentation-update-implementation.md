# Quality Platform Documentation Update - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update all Project Chimera documentation to reflect the newly completed Chimera Quality Platform.

**Architecture:** Integrate Quality Platform into existing documentation structure with dedicated docs/quality-platform/ section and updates to student guide and main README.

**Tech Stack:** Markdown documentation, cross-references, file system organization

---

## Overview

Update all Project Chimera documentation to reflect the newly completed Chimera Quality Platform - a comprehensive testing infrastructure with test orchestration, real-time dashboards, and CI/CD integration.

**Implementation approach:**
1. Update existing documentation files (Student Quick Start, README, docs/README)
2. Create new dedicated quality-platform documentation section
3. Ensure all cross-references and links work correctly
4. Commit changes with clear commit messages

---

## Phase 1: Update Student Quick Start Guide

### Task 1.1: Update Role 10 Responsibilities

**Files:**
- Modify: `getting-started/quick-start.md` (lines 24-39)

**Step 1: Read current Role 10 section**

Run: `head -40 getting-started/quick-start.md | tail -15`

**Step 2: Update Role 10 entry**

Find line that says:
```markdown
| 10 | QA & Documentation Lead | `tests/`, `docs/` | Testing, quality assurance |
```

Replace with:
```markdown
| 10 | QA & Documentation Lead | `tests/`, `docs/`, `platform/` | Testing, QA, Quality Platform |
```

**Step 3: Verify the change**

Run: `grep -n "QA & Documentation Lead" getting-started/quick-start.md`

Expected: Line 39 shows the updated entry with `platform/` added.

**Step 4: Commit**

```bash
git add getting-started/quick-start.md
git commit -m "docs(student): add platform/ to QA & Documentation Lead responsibilities"
```

---

### Task 1.2: Add Quality Platform Service References

**Files:**
- Modify: `getting-started/quick-start.md` (insert after line 491)

**Step 1: Find insertion point**

Run: `grep -n "### 8. Operator Console" getting-started/quick-start.md`

**Step 2: Add new section after line 491**

Insert after the Operator Console section:
```markdown
---

## Quality Platform Services

### Test Orchestrator (Port 8008)

```bash
# Port forward to local
kubectl port-forward -n quality svc/orchestrator 8008:8008

# Access API
curl http://localhost:8008/health

# View logs
kubectl logs -f -n quality deployment/orchestrator
```

### Dashboard Service (Port 8009)

```bash
# Port forward to local
kubectl port-forward -n quality svc/dashboard 8009:8009

# Access web interface
open http://localhost:8009
```

### CI/CD Gateway (Port 8010)

```bash
# Port forward to local
kubectl port-forward -n quality svc/ci-gateway 8010:8010

# Test webhook endpoint
curl -X POST http://localhost:8010/health
```

**Platform Quick Reference:**

| Component | Port | Description |
|-----------|-----|-------------|
| Test Orchestrator | 8008 | Test discovery and execution |
| Dashboard Service | 8009 | Quality dashboards and visualization |
| CI/CD Gateway | 8010 | GitHub/GitLab webhook integration |

**Running Platform Tests:**

```bash
# Run Quality Platform unit tests
cd platform
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=platform --cov-report=html

# View coverage report
xdg-open htmlcov/index.html
```
```

**Step 3: Verify the addition**

Run: `grep -A 5 "Quality Platform Services" getting-started/quick-start.md`

Expected: New section is present with all three service descriptions.

**Step 4: Commit**

```bash
git add getting-started/quick-start.md
git commit -m "docs(student): add Quality Platform services section with quick reference"
```

---

### Task 1.3: Update Project Structure Section

**Files:**
- Modify: `getting-started/quick-start.md` (lines 208-241)

**Step 1: Find the project structure diagram**

Run: `grep -n "project-chimera/" getting-started/quick-start.md`

**Step 2: Add platform/ directory to structure**

Find line that shows:
```markdown
├── docs/                        # Documentation
```

Add after the `├── docs/` line:
```markdown
├── platform/                   # Chimera Quality Platform
│   ├── orchestrator/            # Test orchestration service
│   ├── dashboard/               # Quality dashboard service
│   ├── ci_gateway/              # CI/CD webhook gateway
│   ├── shared/                   # Shared utilities and models
│   ├── database/                 # Database schema
│   ├── testengines/             # Advanced test engines
│   └── tests/                    # Platform tests
```

**Step 3: Verify structure update**

Run: `grep -A 15 "├── platform/" getting-started/quick-start.md`

Expected: platform/ section shows all subdirectories.

**Step 4: Commit**

```bash
git add getting-started/quick-start.md
git commit -m "docs(student): add platform/ directory to project structure"
```

---

## Phase 2: Update Main README.md

### Task 2.1: Add Quality Platform to Key Components

**Files:**
- Modify: `README.md` (insert after line 33)

**Step 1: Find insertion point in Key Components**

Run: `grep -n "### Safety Filter" README.md`

**Step 2: Add Quality Platform section after Safety Filter**

After the Safety Filter section (around line 33), add:
```markdown
### Quality Platform

- **Chimera Quality Platform** - Unified testing and quality infrastructure
  - Test Orchestrator (port 8008) - Test discovery and execution
  - Dashboard Service (port 8009) - Real-time visualization
  - CI/CD Gateway (port 8010) - GitHub/GitLab integration
```

**Step 3: Verify addition**

Run: `grep -A 6 "### Quality Platform" README.md`

Expected: Quality Platform section is present after Safety Filter.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Quality Platform to key components section"
```

---

### Task 2.2: Update Project Structure

**Files:**
- Modify: `README.md` (lines 130-142)

**Step 1: Find the project structure code block**

Run: `grep -n "project-chimera/" README.md`

**Step 2: Add platform/ directory to structure**

Find the line that shows:
```markdown
├── docs/             # Documentation
```

Add after it:
```markdown
├── platform/          # Chimera Quality Platform
│   ├── orchestrator/   # Test orchestration
│   ├── dashboard/      # Quality dashboards
│   ├── ci_gateway/     # CI/CD integration
│   └── shared/         # Shared utilities
```

**Step 3: Verify structure update**

Run: `grep -A 8 "├── platform/" README.md`

Expected: platform/ section added to project structure.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add platform/ to project structure"
```

---

### Task 2.3: Add Documentation Link

**Files:**
- Modify: `README.md` (Documentation section around line 85-98)

**Step 1: Find the Documentation section**

Run: `grep -n "## Documentation" README.md`

**Step 2: Add Quality Platform link**

In the Documentation section, find:
```markdown
### Reference

- [Technical Requirements](TRD_Project_Chimera.md) - Full technical specification
- [Implementation Documentation](docs/plans/IMPLEMENTATION_DOCUMENTATION.md) - Build details
- [Project Backlog](Backlog_Project_Chimera.md) - Outstanding work and features
```

Add after the Implementation Documentation line:
```markdown
- [Quality Platform Documentation](docs/quality-platform/README.md) - Testing infrastructure
```

**Step 3: Verify link addition**

Run: `grep "Quality Platform Documentation" README.md`

Expected: Link is present in Documentation section.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Quality Platform documentation link"
```

---

## Phase 3: Update docs/README.md

### Task 3.1: Add Quality Platform to Core Documentation

**Files:**
- Modify: `docs/README.md` (Core Documentation section, around line 18)

**Step 1: Find Core Documentation section**

Run: `grep -n "### Getting Started" docs/README.md`

**Step 2: Add Quality Platform entry**

In the Core Documentation section, after:
```markdown
- [Implementation Documentation](plans/IMPLEMENTATION_DOCUMENTATION.md) - How the scaffold was built
```

Add:
```markdown
- [Quality Platform](quality-platform/README.md) - Testing infrastructure and quality gates
```

**Step 3: Verify addition**

Run: `grep "Quality Platform" docs/README.md`

Expected: Link is present in Core Documentation section.

**Step 4: Commit**

```bash
git add docs/README.md
git commit -m "docs(index): add Quality Platform to core documentation"
```

---

### Task 3.2: Add Quality Platform Design References

**Files:**
- Modify: `docs/README.md` (Reference section, around line 35)

**Step 1: Find Reference section**

Run: `grep -n "### Reference" docs/README.md`

**Step 2: Add design document links**

In the Reference section, find:
```markdown
- [Project Backlog](../Backlog_Project_Chimera.md) - Outstanding work and features
```

Add before that line:
```markdown
- [Quality Platform Design](plans/2026-02-28-chimera-quality-platform-design.md) - Platform architecture
- [Quality Platform Implementation](plans/2026-02-28-chimera-quality-platform-implementation.md) - Implementation details
```

**Step 3: Verify additions**

Run: `grep "Quality Platform" docs/README.md`

Expected: Both design document links are present.

**Step 4: Commit**

```bash
git add docs/README.md
git commit -m "docs(index): add Quality Platform design document references"
```

---

### Task 3.3: Create Quality Platform Section

**Files:**
- Modify: `docs/README.md` (add at end, before version section)

**Step 1: Find version information section**

Run: `grep -n "## Version Information" docs/README.md`

**Step 2: Insert Quality Platform section before version section**

Add before the Version Information section:
```markdown
### Quality Platform

- [Overview](quality-platform/README.md) - Platform introduction
- [Architecture](quality-platform/ARCHITECTURE.md) - System design
- [API Documentation](quality-platform/API.md) - Service APIs
- [Development](quality-platform/DEVELOPMENT.md) - Contributing guide
- [Deployment](quality-platform/DEPLOYMENT.md) - Deployment guide
```

**Step 3: Verify section creation**

Run: `grep -A 7 "### Quality Platform" docs/README.md`

Expected: All 5 documentation links are present.

**Step 4: Commit**

```bash
git add docs/README.md
git commit -m "docs(index): add Quality Platform documentation section"
```

---

### Task 3.4: Update Version Information

**Files:**
- Modify: `docs/README.md` (line ~165)

**Step 1: Find version information section**

Run: `grep -n "Documentation Last Updated" docs/README.md`

**Step 2: Update date**

Change:
```markdown
- **Documentation Last Updated:** 2026-02-27
```

To:
```markdown
- **Documentation Last Updated:** 2026-02-28
```

**Step 3: Verify date change**

Run: `grep "Documentation Last Updated" docs/README.md`

Expected: Shows 2026-02-28.

**Step 4: Commit**

```bash
git add docs/README.md
git commit -m "docs(index): update documentation date to 2026-02-28"
```

---

## Phase 4: Create docs/quality-platform/ Directory

### Task 4.1: Create Directory and README

**Files:**
- Create: `docs/quality-platform/README.md`

**Step 1: Create directory**

```bash
mkdir -p docs/quality-platform
```

**Step 2: Create README.md**

Create `docs/quality-platform/README.md`:
```markdown
# Chimera Quality Platform

Unified testing and quality platform for Project Chimera.

## Overview

The Chimera Quality Platform is a custom-built testing infrastructure that orchestrates, executes, analyzes, and visualizes all testing across Project Chimera's 8 microservices.

## Quick Links

- [Architecture](ARCHITECTURE.md) - System architecture and design
- [API Documentation](API.md) - Complete API reference
- [Development Guide](DEVELOPMENT.md) - Contributing guidelines
- [Deployment Guide](DEPLOYMENT.md) - Production deployment

## Services

- **Test Orchestrator** (port 8008) - Schedules and executes tests
- **Dashboard Service** (port 8009) - Real-time visualization
- **CI/CD Gateway** (port 8010) - GitHub/GitLab integration

## Quick Start

```bash
cd platform
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/chimera_quality"
export REDIS_URL="redis://localhost:6379/0"

# Start services
uvicorn orchestrator.main:orchestrator_app --host 0.0.0.0 --port 8008
uvicorn dashboard.main:dashboard_app --host 0.0.0.0 --port 8009
uvicorn ci_gateway.main:ci_gateway_app --host 0.0.0.0 --port 8010

# Access dashboard
open http://localhost:8009
```

## Features

- **Test Discovery** - Automatically finds all tests in the codebase
- **Parallel Execution** - Runs tests concurrently with resource management
- **Real-time Updates** - WebSocket streaming of test execution
- **Quality Gates** - Enforces coverage and mutation testing thresholds
- **CI/CD Integration** - GitHub and GitLab webhook support

## Design Documents

- [Quality Platform Design](../plans/2026-02-28-chimera-quality-platform-design.md)
- [Quality Platform Implementation](../plans/2026-02-28-chimera-quality-platform-implementation.md)

## License

MIT
```

**Step 3: Verify file creation**

Run: `ls -la docs/quality-platform/README.md`

Expected: File exists with proper content.

**Step 4: Commit**

```bash
git add docs/quality-platform/README.md
git commit -m "docs(quality-platform): add quality platform overview"
```

---

### Task 4.2: Create Architecture Documentation

**Files:**
- Create: `docs/quality-platform/ARCHITECTURE.md`

**Step 1: Create ARCHITECTURE.md**

Create `docs/quality-platform/ARCHITECTURE.md`:
```markdown
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
```

**Step 3: Verify file creation**

Run: `ls -la docs/quality-platform/ARCHITECTURE.md`

Expected: File exists with architecture diagram.

**Step 4: Commit**

```bash
git add docs/quality-platform/ARCHITECTURE.md
git commit -m "docs(quality-platform): add architecture documentation"
```

---

### Task 4.3: Create API Documentation

**Files:**
- Create: `docs/quality-platform/API.md`

**Step 1: Create API.md**

Create `docs/quality-platform/API.md`:
```markdown
# Chimera Quality Platform - API Documentation

## Test Orchestrator API (Port 8008)

### POST /api/v1/run/start
Start a new test run for a commit.

**Request:**
```json
{
  "commit_sha": "abc123",
  "branch": "main",
  "test_filter": ["tests/unit/*"],
  "full_suite": true
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "pending",
  "message": "Test run started"
}
```

### GET /api/v1/run/{run_id}
Get status of a test run.

**Response:**
```json
{
  "run_id": "uuid",
  "status": "running",
  "progress": 45,
  "total": 100,
  "passed": 40,
  "failed": 5
}
```

### WebSocket /ws/run/{run_id}
Live test execution updates.

**Message Format:**
```json
{
  "type": "test_complete",
  "test_id": "tests/unit/test_example.py::test_func",
  "status": "passed",
  "duration_ms": 150
}
```

### GET /api/v1/tests/discover
Discover all tests in the codebase.

**Response:**
```json
{
  "total": 500,
  "tests": ["test_id1", "test_id2", ...]
}
```

## Dashboard Service API (Port 8009)

### GET /api/v1/runs
List test runs with pagination.

**Query Parameters:**
- `limit`: Max 100 (default: 10)
- `offset`: For pagination (default: 0)

**Response:**
```json
{
  "runs": [...],
  "total": 50,
  "limit": 10,
  "offset": 0
}
```

### GET /api/v1/runs/{run_id}/summary
Get run summary with coverage and mutation scores.

**Response:**
```json
{
  "run_id": "uuid",
  "commit_sha": "abc123",
  "status": "completed",
  "total": 500,
  "passed": 485,
  "failed": 12,
  "skipped": 3,
  "duration_seconds": 245,
  "coverage_pct": 94.2,
  "mutation_score": 97.8
}
```

### GET /api/v1/trends
Get historical trend data.

**Query Parameters:**
- `metric`: Metric name (coverage, mutations, duration)
- `days`: Number of days (1-365, default: 30)

**Response:**
```json
{
  "metric": "coverage",
  "days": 30,
  "data": [
    {"date": "2026-02-28", "value": 94.2},
    {"date": "2026-02-27", "value": 93.8}
  ]
}
```

### WebSocket /ws/runs/{run_id}
Real-time test execution updates.

**Message Format:**
```json
{
  "type": "test_complete",
  "data": {...}
}
```

## CI/CD Gateway API (Port 8010)

### POST /webhooks/github
GitHub webhook endpoint.

**Headers:**
- `X-Hub-Signature-256`: HMAC signature verification

**Events:**
- `push`: Trigger test run on push to main branch
- `pull_request`: Trigger affected tests on PR

### POST /webhooks/gitlab
GitLab webhook endpoint.

**Events:**
- `Push`: Trigger test run on push
- `Merge Request`: Trigger affected tests

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ci-gateway"
}
```
```

**Step 3: Verify file creation**

Run: `ls -la docs/quality-platform/API.md`

Expected: File exists with API documentation.

**Step 4: Commit**

```bash
git add docs/quality-platform/API.md
git commit -m "docs(quality-platform): add API documentation"
```

---

### Task 4.4: Create Development Guide

**Files:**
- Create: `docs/quality-platform/DEVELOPMENT.md`

**Step 1: Create DEVELOPMENT.md**

Create `docs/quality-platform/DEVELOPMENT.md`:
```markdown
# Quality Platform - Development Guide

## Setting Up Development Environment

```bash
cd platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=platform --cov-report=html

# Integration tests
pytest tests/integration/ -v

# All tests
pytest -v
```

## Code Style

- Use type hints for all functions
- Follow PEP 8
- Write docstrings for all classes and public methods
- Use descriptive variable names

## Testing Guidelines

### Unit Tests

- Test individual functions and classes
- Mock external dependencies
- Test edge cases and error conditions
- Aim for >95% code coverage

### Integration Tests

- Test service interactions
- Use test fixtures for common setup
- Test database operations
- Test API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-change

# 2. Make changes
# Edit files in platform/

# 3. Run tests
pytest tests/unit/ -v

# 4. Format code
make format

# 5. Commit
git add .
git commit -m "feat: describe your changes"

# 6. Push and create PR
git push origin feature/your-change
```

## Useful Commands

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Coverage report | `pytest tests/ --cov=platform --cov-report=html` |
| Format code | `make format` or `black platform/` |
| Lint code | `ruff check platform/` |
| Type check | `mypy platform/` |
```

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the platform directory
cd platform

# Install dependencies
pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Check database is running
kubectl get pods -n quality

# Port forward database
kubectl port-forward -n quality svc/postgres 5432:5432
```

**Redis connection errors:**
```bash
# Check Redis is running
kubectl get pods -n quality

# Port forward Redis
kubectl port-forward -n quality svc/redis 6379:6379
```
```

**Step 3: Verify file creation**

Run: `ls -la docs/quality-platform/DEVELOPMENT.md`

Expected: File exists with development guide.

**Step 4: Commit**

```bash
git add docs/quality-platform/DEVELOPMENT.md
git commit -m "docs(quality-platform): add development guide"
```

---

### Task 4.5: Create Deployment Guide

**Files:**
- Create: `docs/quality-platform/DEPLOYMENT.md`

**Step 1: Create DEPLOYMENT.md**

Create `docs/quality-platform/DEPLOYMENT.md`:
```markdown
# Quality Platform - Deployment Guide

## Prerequisites

- PostgreSQL 16
- Redis 7
- Python 3.11+
- k3s cluster (optional)

## Local Deployment

### Environment Setup

```bash
cd platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Setup

```bash
# Create database
createdb chimera_quality

# Run migrations
python -c "
from platform.shared.database import engine, Base
import asyncio
asyncio.run(engine.connect())
asyncio.run(engine.dispose())
"
```

### Environment Variables

Create `.env` file in platform directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/chimera_quality

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub (optional)
GITHUB_WEBHOOK_SECRET=your-secret-here
GITHUB_TOKEN=your-token-here

# Dashboard
DASHBOARD_URL=http://localhost:8009

# Test Execution
MAX_WORKERS=16
TEST_TIMEOUT_SECONDS=300

# Quality Gates
MIN_COVERAGE_THRESHOLD=95.0
MAX_MUTATION_SURVIVAL=2.0
```

### Start Services

```bash
# Terminal 1: Orchestrator
uvicorn orchestrator.main:orchestrator_app --host 0.0.0.0 --port 8008

# Terminal 2: Dashboard
uvicorn dashboard.main:dashboard_app --host 0.0.0.0 --port 8009

# Terminal 3: CI/CD Gateway
uvicorn ci_gateway.main:ci_gateway_app --host 0.0.0.0 --port 8010
```

### Verify Deployment

```bash
# Check health endpoints
curl http://localhost:8008/health
curl http://localhost:8009/health
curl http://localhost:8010/health

# Should all return: {"status": "healthy", "service": "..."}
```

## Production Deployment

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace quality

# Apply manifests
kubectl apply -f platform/manifests/ -n quality

# Verify deployment
kubectl get pods -n quality
kubectl get svc -n quality
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: quality-platform-ingress
  namespace: quality
spec:
  rules:
  - host: quality.chimera.example.com
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: orchestrator
            port:
              number: 8008
```

## Monitoring

### Prometheus Metrics

All services expose `/metrics` endpoint for Prometheus scraping.

### Grafana Dashboards

Import dashboards from `platform/grafana/` directory.

### Health Checks

Services are configured with liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8008
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8008
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Webhook Configuration

### GitHub

1. Go to repository Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/github`
3. Content type: application/json
4. Secret: Use generated webhook secret
5. Events: Push, Pull requests

### GitLab

1. Go to Settings → Webhooks
2. Add webhook: `https://your-domain.com/webhooks/gitlab`
3. Secret: Use generated webhook secret
4. Events: Push events, Merge request events

## Troubleshooting

### Database Issues

**Problem:** Connection refused

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -l | grep chimera_quality
```

**Problem:** Migration errors

```bash
# Drop and recreate database
dropdb chimera_quality
createdb chimera_quality

# Re-run migrations
python -c "from platform.shared.database import Base, engine; import asyncio; asyncio.run(engine.connect());"
```

### Service Issues

**Problem:** Service won't start

```bash
# Check logs
kubectl logs -n quality deployment/<service>

# Check events
kubectl describe pod -n quality <pod-name>
```

**Problem:** Services can't communicate

```bash
# Check services
kubectl get svc -n quality

# Check network policies
kubectl get networkpolicies -n quality
```
```

**Step 3: Verify file creation**

Run: `ls -la docs/quality-platform/DEPLOYMENT.md`

Expected: File exists with deployment guide.

**Step 4: Commit**

```bash
git add docs/quality-platform/DEPLOYMENT.md
git commit -m "docs(quality-platform): add deployment guide"
```

---

## Phase 5: Final Verification and Cleanup

### Task 5.1: Verify All Cross-References

**Step 1: Test all documentation links**

Run link checker:
```bash
# Find markdown links
grep -r "\[.*\](" docs/ | head -20

# Common issues to check:
# - Relative paths correct
# - File names match actual files
# - No broken internal links
```

**Step 2: Verify Student Quick Start updates**

Run: `grep -A 3 "platform/" getting-started/quick-start.md`

Expected: Multiple references to platform/ in student guide.

**Step 3: Verify README.md updates**

Run: `grep -A 3 "Quality Platform" README.md`

Expected: Quality Platform appears in key components and project structure.

**Step 4: Verify docs/README.md updates**

Run: `grep -A 3 "Quality Platform" docs/README.md`

Expected: Quality Platform appears in multiple sections.

**Step 5: Commit if any fixes needed**

```bash
git add docs/
git commit -m "docs: fix any cross-reference or link issues"
```

---

### Task 5.2: Create docs/quality-platform/__init__.py

**Files:**
- Create: `docs/quality-platform/__init__.py`

**Step 1: Create init file**

Create `docs/quality-platform/__init__.py`:
```python
"""Documentation for the Chimera Quality Platform."""
```

**Step 2: Commit**

```bash
git add docs/quality-platform/__init__.py
git commit -m "docs(quality-platform): add package marker"
```

---

### Task 5.3: Final Commit

**Step 1: Review all changes**

Run: `git status`

Verify all documentation updates are staged.

**Step 2: Create summary commit**

```bash
git add .
git commit -m "docs: complete Quality Platform documentation update

- Updated getting-started/quick-start.md with Role 10 Quality Platform responsibilities
- Added Quality Platform to main README.md key components
- Created docs/quality-platform/ section with:
  - README.md (overview and quick start)
  - ARCHITECTURE.md (system design and data flow)
  - API.md (complete API reference)
  - DEVELOPMENT.md (contributing guide)
  - DEPLOYMENT.md (production deployment)
- Updated docs/README.md with Quality Platform references
- All cross-references and links verified
- Documentation date updated to 2026-02-28

This completes the documentation update for the Chimera Quality Platform.
"
```

---

## Success Criteria

- ✅ getting-started/quick-start.md updated with Quality Platform in Role 10
- ✅ getting-started/quick-start.md has Quality Platform services section
- ✅ main README.md includes Quality Platform in key components
- ✅ main README.md project structure includes platform/ directory
- ✅ docs/README.md has Quality Platform section with all subsections
- ✅ docs/quality-platform/ directory created with 5 documentation files
- ✅ All cross-references and links working
- ✅ Documentation date updated to 2026-02-28
- ✅ All changes committed with clear commit messages

---

**Estimated Timeline:** 30-45 minutes

**Total Files Modified/Created:** ~11 files

---

*Implementation plan created: 2026-02-28*
*Project Chimera - Documentation Update*
