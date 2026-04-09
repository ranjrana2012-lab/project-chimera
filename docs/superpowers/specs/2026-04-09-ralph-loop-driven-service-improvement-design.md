# Ralph Loop-Driven Service Improvement Design

**Date**: April 9, 2026
**Status**: Draft
**Version**: 1.0
**Authors**: Project Chimera Team

---

## Executive Summary

This document defines the design for an 8-week autonomous development cycle where Ralph Loop (Claude Code autonomous agent) continuously improves the Project Chimera codebase while 4 students test, validate, and document the system. The goal is to deploy a functional continuous-loop interactive system by June 5, 2026.

---

## Architecture Overview

### Core Concept
Ralph Loop (autonomous Claude Code agent) runs 24/7 iteratively improving the codebase. Four students self-select two services each to test and validate. A unified dashboard tracks all progress through service health, test pass rates, and git commit activity.

### Active Services (6 services for Ralph Loop + students)
1. **Nemo Claw Orchestrator** - Central coordination and routing
2. **SceneSpeak Agent** - Dialogue generation (GLM-4.7)
3. **Sentiment Agent** - Emotion analysis (DistilBERT ML)
4. **Safety Filter** - Content moderation
5. **Captioning Agent** - Text formatting and accessibility
6. **Audio Controller** - Sound output and integration

### Frozen Services (2 services, left as-is)
1. **OpenClaw Orchestrator** - Removed from active use
2. **BSL Agent** - Not targeted for improvement

### Student Ownership
Each student picks 2 services from the 6 active based on interest/technical comfort. Students are responsible for testing, validating, and documenting their assigned services.

### Continuous Loop System
Multiple interfaces (web, CLI, API) accept user input, route through Nemo Claw to appropriate agents, and return responses to the user in a continuous loop.

### Tracking and Monitoring
Daily dashboard shows service health, test pass rates, git commits, and progress summary.

---

## Components

### Component 1: Ralph Loop Autonomous Agent

**Location**: `services/autonomous-agent/`

**Purpose**: Continuously improve the codebase 24/7

**Inputs**:
- Current test results (pytest exit codes, coverage reports)
- Service health check status (`/health` endpoints)
- Git history and code quality metrics
- `queue.txt` - task queue of pending improvements
- `program.md` - constitutional constraints and rules
- `learnings.md` - historical context and lessons learned

**Process**:
1. Read `queue.txt` for next task
2. Select service to improve (prioritizes by health/test failures)
3. Make bounded changes to service code + tests
4. Run evaluator: `./platform/quality-gate/evaluate.sh`
5. If evaluator returns 0: commit changes, update `learnings.md`
6. If evaluator returns non-zero: revert changes, document failure in `learnings.md`, move to next task

**Outputs**:
- Git commits (code improvements, test additions)
- Updated `learnings.md` (lessons learned, failure analysis)
- Dashboard metrics (test pass rates, coverage trends)

**Constraints**:
- Can make any changes but MUST document in `learnings.md`
- Bounded changes: ONE logical component per iteration
- Must run tests after each change
- Reverts immediately on test failure
- CANNOT modify evaluator.sh (READ-ONLY)
- Cannot skip tests or stub functions

**Quality Gates** (immutable):
1. Functional Correctness: pytest exit code == 0
2. Assertion Density: assertion_count >= baseline
3. Coverage: coverage >= baseline (must stay stable or increase)
4. Deprecation Hygiene: deprecation_warnings == 0

---

### Component 2: Student Testing Component

**Location**: Distributed across students' local environments

**Purpose**: Test, validate, and improve assigned services

**Inputs**:
- Dashboard (service health, test status, Ralph Loop activity)
- Ralph Loop git commits
- Service endpoints for manual testing
- `queue.txt` for adding improvement tasks

**Process**:
1. Each student self-selects 2 services from the 6 active
2. Daily testing of their assigned services
3. Validate Ralph Loop changes in their services
4. Report issues or blockers by adding to `queue.txt`
5. Improve documentation, tests, or bug reports as needed
6. Coordinate with other students for integration testing

**Outputs**:
- Test reports (daily status per service)
- Bug reports to Ralph Loop queue
- Documentation updates
- Final product validation (Week 8)

**Student Responsibilities**:
- Test both services daily using web/CLI/API interfaces
- Verify Ralph Loop changes don't break functionality
- Add improvement tasks to queue when gaps identified
- Document test results and issues
- Participate in end-to-end integration testing

---

### Component 3: Dashboard Component

**Location**: `services/dashboard/` or separate monitoring stack

**Purpose**: Unified tracking for all progress across Ralph Loop and students

**Data Sources**:
- Prometheus metrics (already deployed)
- Grafana dashboards (already deployed)
- Git commit webhooks/API
- Health check aggregation (polls all services)
- Test result aggregation

**Displays**:
- **Service Health Status**: 7 services shown, active vs frozen designation
  - Green: Health check returns 200, tests passing
  - Yellow: Health check returns 200 but some tests failing
  - Red: Health check failing or service down
- **Test Pass Rates**: Per service and overall
- **Recent Git Commits**: Ralph Loop activity feed with commit messages
- **Service Dependency Graph**: Visual representation of service relationships
- **Daily Progress Summary**: Text summary of what changed today

**Update Frequency**:
- Service health: Every 30 seconds
- Test results: After each Ralph Loop iteration
- Git commits: Real-time via webhook
- Daily summary: Generated at midnight

**Technologies**:
- Prometheus (metrics collection)
- Grafana (visualization)
- Custom health aggregator (polls services)
- Git webhook receiver
- Frontend: React or Python-based dashboard

---

## Data Flow

### Continuous Loop System Flow

```
User Input (Multiple Interfaces)
    │
    ├───► Web Interface (Operator Console)
    ├───► CLI Interface (chimera_core.py)
    └───► API Interface (REST/WebSocket)
         ↓
    [Nemo Claw Orchestrator]
         │
         ├───► SceneSpeak Agent (Dialogue Generation)
         ├───► Sentiment Agent (Sentiment Analysis)
         ├───► Safety Filter (Content Validation)
         ├───► Captioning Agent (Text Formatting)
         └───► Audio Controller (Sound Output)
         ↓
    [Response Aggregation]
         ↓
    [Output to User]
         │
         ├───► Web: Display in UI
         ├───► CLI: Print to terminal
         └───► API: Return JSON/WebSocket
```

### Ralph Loop Data Flow

```
[Daily Trigger or Continuous]
    ↓
[Dashboard Polls All Services]
    ├──► Health check /health endpoints
    ├──► Run pytest on each service
    ├───► Fetch git log for commits
    └───► Calculate metrics
         ↓
[Generate Task Queue]
    ├──► Prioritize by health (failing services first)
    ├───► Prioritize by test failures
    ├───► Prioritize by code quality metrics
    └───► Write to queue.txt
         ↓
[Ralph Loop Iteration Loop]
    ├─► Read queue.txt
    ├─► Select service and task
    ├─► Make code changes
    ├─► Run tests
    ├─► Run evaluator.sh
    │    ├─► Pass: Commit changes
    │    └─► Fail: Revert, document in learnings.md
    └─► Loop continues (24/7)
         ↓
[Update Dashboard]
```

---

## Error Handling

### Service Failure Scenarios

**Scenario 1: Service Unreachable**
```
Nemo Claw tries SceneSpeak → Timeout/Failure
↓
Handling:
- Log error to dashboard (mark service as degraded)
- Continue with other services
- Don't block the continuous loop
- Ralph Loop notes service as unhealthy (prioritize for fixing)
```

**Scenario 2: Test Failures**
```
Ralph Loop makes change → Tests fail
↓
Handling:
- Revert changes immediately (git reset --hard)
- Document failure in learnings.md
- Mark service as "blocked" in queue temporarily
- Move to next service or task
- Re-attempt after 3 iterations or human intervention
```

**Scenario 3: Student Reports Bug**
```
Student finds issue during testing
↓
Handling:
- Student adds task to queue.txt (if not present)
- Tag with urgency: [urgent], [bug], [enhancement]
- Ralph Loop prioritizes based on severity and service health
- Student can also implement fix directly and Ralph Loop will validate
```

**Scenario 4: Ralph Loop Gets Stuck**
```
Ralph Loop fails to make progress for 5+ iterations on same service
↓
Handling:
- Daily check-in identifies stagnation (no commits, no coverage increase)
- Human intervention required
- Options:
  - Add specific targeted task to queue
  - Restructure service (human-directed)
  - Skip service temporarily and work on others
  - Increase iteration time limit
```

**Scenario 5: Frozen Service Dependencies**
```
Active service depends on frozen service (OpenClaw/BSL)
↓
Handling:
- Stub/mock frozen service behavior in active service
- Document dependency clearly in code comments
- Don't attempt to fix or improve frozen services
- Ralph Loop ignores frozen services entirely
```

### Error Recovery

**Automatic Recovery**:
- Services auto-restart on failure (Docker restart: unless-stopped)
- Ralph Loop reverts bad changes automatically
- Dashboard recovers when services come back online
- Tests re-run after service recovery

**Manual Recovery** (requires human intervention):
- Ralph Loop completely stuck (no progress for 48+ hours)
- Service won't restart or is critically broken
- Critical security vulnerability discovered
- Student identifies blocking issue that Ralph Loop can't resolve

**Manual Recovery Process**:
1. Pause Ralph Loop (stop autonomous-agent service)
2. Human investigates and fixes blocking issue
3. Add specific recovery task to queue.txt
4. Resume Ralph Loop
5. Monitor until progress resumes

---

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\          ← Continuous Loop System Tests (Weekly)
      /------\
     /        \
    /Unit      Integration\
   /  tests     tests  ← Service-Specific Tests (Per Ralph Loop Iteration)
  /--------------------------------\
```

### Test Categories

**1. Ralph Loop Tests** (runs on every change)
- Unit tests for each service
- Integration tests for service communication
- Coverage gates (must stay ≥80%)
- Quality gate evaluator script (`./platform/quality-gate/evaluate.sh`)
- Blocks commit if tests fail

**2. Student Tests** (daily validation)
- Manual testing of assigned services via web/CLI/API
- Exploratory testing of Ralph Loop changes
- Edge case discovery
- User acceptance testing
- Document results in dashboard or shared doc

**3. Continuous Loop Tests** (weekly validation)
- End-to-end flow: input → Nemo Claw → agents → output
- Interface tests (web, CLI, API all work correctly)
- Load testing (can handle multiple concurrent users)
- Performance benchmarks (response times <5s at 90th percentile)

### Test Execution Schedule

**Ralph Loop**:
- Runs `pytest` after every code change
- Blocks commit if tests fail
- Automatically reverts on failure
- Runs 24/7 (or during scheduled hours)

**Students**:
- Run test suite for their 2 services daily
- Document test results in dashboard or shared doc
- Report failures to Ralph Loop queue

**Automated**:
- Nightly full test suite (all services)
- Weekly continuous loop integration tests
- Performance regression tests (weekly)

### Success Metrics

**Per Service**:
- Health check returns 200
- Unit tests passing ≥80%
- Can handle sample request successfully
- Response time <5s (90th percentile)
- No critical errors in logs

**Overall System**:
- All 6 active services healthy
- Continuous loop accepts input and returns output
- No service in "degraded" state
- Dashboard shows green across the board
- System can run 30 minutes continuously without errors

---

## Success Criteria

### Week 8 Completion Definition (June 5, 2026)

**System Level** (ALL must be true):
- ✅ All 6 active services have `/health` returning 200
- ✅ Continuous loop system accepts input and returns output via web, CLI, and API
- ✅ Dashboard shows all services healthy
- ✅ At least 5 sample input scenarios work end-to-end
- ✅ System can run continuously for 30 minutes without errors
- ✅ All interfaces (web, CLI, API) functional and tested

**Ralph Loop Level** (ALL must be true):
- ✅ Ralph Loop has made ≥50 successful commits to active services
- ✅ Test coverage has increased or stayed stable across all services
- ✅ `learnings.md` has entries showing progress over 8 weeks
- ✅ No services are permanently blocked (stuck >1 week without progress)
- ✅ Quality gate evaluator passing consistently

**Student Level** (ALL must be true):
- ✅ Each student has tested their 2 services and documented results
- ✅ Each student has contributed at least 1 improvement (code, test, or documentation)
- ✅ Final product demonstration shows the continuous loop working
- ✅ Students can explain their services and how the system works

**Quality Level** (ALL must be true):
- ✅ No critical security vulnerabilities in deployed services
- ✅ All services have basic error handling (don't crash on bad input)
- ✅ Documentation exists for how to use each interface (web/CLI/API)
- ✅ GitHub repository is public-facing and accurate (no grant content)
- ✅ `internal/` folder exists with grant tracking (gitignore'd)

### Partial Success Criteria

**Yellow** (Continue Ralph Loop):
- System works but some services degraded
- Ralph Loop making progress but slower than expected
- Some test failures but no critical blockers

**Orange** (Human intervention needed):
- Ralph Loop stuck, services not improving for 48+ hours
- Test coverage decreasing across services
- Critical services failing

**Red** (Re-evaluate approach):
- Multiple services permanently blocked
- Ralph Loop cannot make progress
- System cannot achieve basic continuous loop

---

## Timeline & Milestones

### Week 1 (April 9-15): Foundation & Setup

**Goals**:
- Set up Ralph Loop autonomous agent
- Configure dashboard for tracking
- Students self-select service assignments
- Establish baseline metrics

**Tasks**:
- [ ] Configure autonomous-agent with Ralph Loop constraints
- [ ] Set up task queue (`queue.txt`)
- [ ] Initialize `learnings.md` with baseline state
- [ ] Configure dashboard to poll all services
- [ ] Students pick 2 services each, document assignments
- [ ] Run baseline tests, record pass/fail rates
- [ ] Set up git webhook for dashboard
- [ ] Create communication channels (Slack/Discord)

**Deliverables**:
- Ralph Loop configured with task queue
- Dashboard showing service health
- Student service assignments documented
- Baseline metrics recorded

**Success**: Ralph Loop running, dashboard active, students assigned

---

### Week 2-3 (April 16-29): Ralph Loop Iteration 1

**Goals**:
- Ralph Loop improves lowest-hanging fruit
- Students test their services, report issues
- Establish improvement patterns

**Tasks**:
- [ ] Ralph Loop identifies and fixes basic issues
- [ ] Students test their 2 services daily
- [ ] Students report bugs to queue.txt
- [ ] Ralph Loop addresses student-reported issues
- [ ] Dashboard updated with progress
- [ ] Week 3 check-in: review progress, adjust priorities

**Deliverables**:
- Initial Ralph Loop commits made (≥10 commits)
- Student test reports completed
- Dashboard showing improvement trends
- `learnings.md` has initial entries

**Success**: Ralph Loop making commits, students testing regularly

---

### Week 4-5 (April 30 - May 13): Ralph Loop Iteration 2

**Goals**:
- Focus on integration issues
- Improve orchestrator-agent communication
- Students validate Ralph Loop changes

**Tasks**:
- [ ] Ralph Loop fixes service communication issues
- [ ] Integration tests between Nemo Claw and agents
- [ ] Students validate integration improvements
- [ ] Dashboard enhanced with dependency graph
- [ ] Week 5 check-in: review progress, adjust priorities

**Deliverables**:
- Services can communicate via Nemo Claw reliably
- Test coverage increasing
- Integration tests passing
- Dependency graph visible in dashboard

**Success**: Integration tests passing, services communicating

---

### Week 6-7 (May 14-27): Continuous Loop Implementation

**Goals**:
- Build web/CLI/API interfaces
- End-to-end flow working
- Students test full system

**Tasks**:
- [ ] Implement web interface (Operator Console enhancements)
- [ ] Implement CLI interface (chimera_core.py enhancements)
- [ ] Implement API interface (REST/WebSocket)
- [ ] Wire all interfaces through Nemo Claw
- [ ] Students test all interfaces
- [ ] End-to-end continuous loop functional
- [ ] Week 7 check-in: final review before Week 8

**Deliverables**:
- All 3 interfaces functional
- Continuous loop accepts input and returns output
- Student validation complete
- Interfaces documented

**Success**: Continuous loop working via all interfaces

---

### Week 8 (May 28 - June 5): Final Integration & Demo

**Goals**:
- Full system validation
- Performance optimization
- Demo preparation
- Final documentation

**Tasks**:
- [ ] Run 30-minute continuous test
- [ ] Fix any remaining issues
- [ ] Performance optimization (response times <5s)
- [ ] Load testing (handle multiple users)
- [ ] Prepare demo scenarios
- [ ] Final dashboard all green
- [ ] Student demo presentations
- [ ] Update documentation (README, guides)
- [ ] Final git tag and push

**Deliverables**:
- 30-minute continuous run without errors
- Final dashboard all green
- Demo documentation complete
- README updated with current state
- System tagged and deployed

**Success**: All success criteria met, system ready for handoff

---

## Technical Specifications

### Ralph Loop Configuration

**File**: `.claude/autonomous-refactor/program.md`

**Constraints**:
- Platform: x86_64 Linux, Python 3.10+, FastAPI
- Avoid: `flash-attn`, ARM64-specific wheels
- Use SDPA for attention mechanisms
- Bounded changes: ONE logical component per iteration

**Rules**:
- CAN: Add tests, improve coverage, refactor, add types, fix debt
- CANNOT: Delete assertions, remove failing tests, stub functions, reduce coverage, ignore pytest exit codes

**Quality Gates** (immutable):
1. Functional Correctness: pytest exit code == 0
2. Assertion Density: assertion_count >= baseline
3. Coverage: coverage >= baseline
4. Deprecation Hygiene: deprecation_warnings == 0

**Failure Consequences**:
- Exit 1: Tests failed → git reset
- Exit 2: Reward hacking → git reset, document failure
- Exit 3: Coverage below threshold → git reset
- Exit 4: Deprecation warnings → fix warnings, resubmit

### Dashboard Specifications

**Technologies**:
- Backend: FastAPI or Python
- Frontend: React or Python-based
- Metrics: Prometheus (already deployed)
- Visualization: Grafana (already deployed)

**Data Sources**:
- HTTP: Poll `/health` endpoints every 30s
- Git: Webhook on push events
- Tests: Parse pytest output
- Logs: Aggregate service logs

**Display Components**:
- Service health grid (7 services × status)
- Test pass rate charts
- Commit feed (last 20 commits)
- Dependency graph visualization
- Daily summary text

**Update Frequency**:
- Service health: Every 30s
- Test results: After Ralph Loop iteration
- Git commits: Real-time webhook
- Daily summary: Midnight

### Interface Specifications

**Web Interface** (Operator Console):
- Endpoint: `http://localhost:8007`
- Features: Text input, response display, sentiment viz, audio controls
- Technology: React or FastAPI + HTML

**CLI Interface**:
- Command: `python -m chimera_core.cli --continuous`
- Features: Batch processing, test scenarios, health checks, export
- Input: STDIN or file
- Output: STDOUT or file

**API Interface**:
- Base: `http://localhost:9000/api`
- Endpoints:
  - `POST /input` - Submit text for processing
  - `GET /status` - Get system status
  - `WS /stream` - WebSocket for real-time responses
- Features: REST + WebSocket, CORS enabled, rate limiting

---

## Open Questions & Decisions Needed

1. **Dashboard Technology**: Should we build a custom dashboard or enhance existing Grafana?
   - Recommendation: Start with Grafana enhancements for speed, custom dashboard if needed

2. **Ralph Loop Schedule**: Should Ralph Loop run 24/7 or during scheduled hours?
   - Recommendation: Start with scheduled hours (9am-5pm local), extend if needed

3. **Student Coordination**: How often should students sync up?
   - Recommendation: Daily standup (15 minutes) plus shared Slack/Discord

4. **Frozen Services**: What do we do if a student accidentally breaks a frozen service?
   - Recommendation: Revert from git, document in learnings.md, add to training

5. **Success Threshold**: Is 50 commits enough? Should we adjust based on progress?
   - Recommendation: Review at Week 4 check-in, adjust based on velocity

---

## Glossary

- **Ralph Loop**: Autonomous Claude Code agent that iteratively improves codebase
- **Nemo Claw Orchestrator**: Central coordination and routing service
- **OpenClaw Orchestrator**: Frozen - no longer used for routing
- **Frozen Service**: Service left as-is, not targeted for improvement
- **Active Service**: Service being improved by Ralph Loop
- **Queue**: Task queue (`queue.txt`) of pending improvements
- **Learnings**: Historical context and lessons learned (`learnings.md`)
- **Evaluator**: Quality gate script that validates changes
- **Continuous Loop**: System that accepts input, processes through agents, returns output

---

## Next Steps

1. **Review and approve this design**
2. **Set up Week 1 foundation** (configure Ralph Loop, dashboard, student assignments)
3. **Begin Ralph Loop iterations** (autonomous improvement starts)
4. **Daily check-ins** (track progress, adjust priorities)
5. **Week 4 & 8 checkpoints** (major reviews, course correction)

---

**Status**: ✅ Design Complete - Ready for Review
**Next**: User reviews spec, then invoke writing-plans skill for implementation plan
