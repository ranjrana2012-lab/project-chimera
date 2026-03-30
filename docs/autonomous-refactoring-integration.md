# Autonomous Codebase Refactoring - Integration Summary

**Date**: 2026-03-30
**Status**: Phase 1 Complete - Ready for Testing
**Architecture**: Ralph Loop + AutoResearch (adapted for Project Chimera x86_64)

## Executive Summary

The autonomous codebase refactoring system has been successfully integrated into Project Chimera. This system implements a continuous, unsupervised test-hardening and refactoring loop that follows the **Ralph pattern** (stateless iteration with external memory) and the **AutoResearch methodology** (immutable evaluator, mutable sandbox, human instructions).

**Key Achievement**: The system is designed to prevent **reward hacking** — the agent cannot "win" by deleting tests, removing assertions, or stubbing functions. Quality must genuinely improve for changes to be committed.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS REFACTORING LOOP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────────┐  │
│  │   Ralph     │──────▶│  Claude     │──────▶│     Immutable Evaluator     │  │
│  │ Orchestrator│      │  Code CLI   │      │     (evaluate.sh)           │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────────┘  │
│         │                    │                           │                   │
│         ▼                    ▼                           ▼                   │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────────┐  │
│  │   Memory    │      │   Git       │      │      Quality Gates          │  │
│  │  System     │      │  Worktree   │      │  (Functional, Coverage,      │  │
│  │             │      │  (ephemeral)│      │   Assertions, Deprecations)  │  │
│  │ program.md  │      └─────────────┘      └─────────────────────────────┘  │
│  │ learnings.md│                                                       │
│  │ queue.txt   │                                                       │
│  └─────────────┘                                                       │
│                                                                              │
│  If Evaluator returns 0:    git commit -m "AutoQA: [description]"            │
│  If Evaluator returns != 0: git reset --hard && git clean -fd                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Files Created

### Core Components

| File | Purpose |
|------|---------|
| `platform/quality-gate/gate/anti_gaming_evaluator.py` | Immutable evaluator with ungameable metrics |
| `platform/quality-gate/evaluate.sh` | CLI wrapper for evaluator (exit codes 0-5) |
| `platform/quality-gate/run_evaluation.py` | Python runner for evaluator |
| `services/autonomous-agent/test_hardening_task.py` | Task definitions for Ralph Engine |
| `services/autonomous-agent/orchestrator.py` | Main Ralph Loop orchestrator |

### Memory System

| File | Purpose |
|------|---------|
| `.claude/autonomous-refactor/program.md` | Constitutional constraints (READ-ONLY) |
| `.claude/autonomous-refactor/learnings.md` | Historical failure context (APPEND-ONLY) |
| `.claude/autonomous-refactor/queue.txt` | Task queue (MODIFIED by loop) |

### Deployment

| File | Purpose |
|------|---------|
| `.claude/autonomous-refactor/chimera-autonomous-refactor.service` | Systemd service definition |

## Quality Gates (Anti-Gaming Metrics)

The evaluator enforces **four ungameable metrics**:

### 1. Functional Correctness
```bash
pytest exit code must be 0
```
- If tests fail, the change is rejected
- No partial credit for "almost passing"

### 2. Assertion Density
```python
assertion_count >= baseline
```
- Agent cannot delete assertions to pass tests
- Counted via AST analysis of test files
- Baseline tracked in `baseline_metrics.json`

### 3. Coverage Growth
```python
coverage_percent >= baseline
```
- Must stay stable (refactor) or increase (test-gen)
- Coverage below 80% fails immediately
- Decreases > 2% from baseline fail

### 4. Deprecation Hygiene
```bash
deprecation_warnings == 0
```
- No PyTorch 2.5/2.6 deprecation warnings
- Catches patterns like `XNNPACKQuantizer` (deprecated)
- Prevents technical debt accumulation

## Exit Code Mapping

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All checks passed | `git commit` |
| 1 | Functional test failure | `git reset --hard` |
| 2 | Reward hacking detected | `git reset --hard` + document failure |
| 3 | Coverage below threshold | `git reset --hard` |
| 4 | Deprecation warnings | `git reset --hard` |
| 5 | Evaluation error | `git reset --hard` |

## Task Queue Format

```
PRIORITY | MODE | MODULE_PATH | TEST_PATH | DESCRIPTION
```

**Modes**:
- `test_hardening`: Add tests only (no module changes)
- `refactor`: Refactor module only (ensure tests still pass)
- `both`: Both refactor and harden tests

**Priorities**: `HIGH`, `MEDIUM`, `LOW`

## How to Use

### Manual Testing

```bash
# 1. Activate the project's virtual environment
source services/autonomous-agent/venv/bin/activate

# 2. Run a single iteration
python services/autonomous-agent/orchestrator.py --max-iterations 1

# 3. Check the results
cat evaluation_results.json
cat .claude/autonomous-refactor/learnings.md
```

### Background Service

```bash
# 1. Install the systemd service
sudo cp .claude/autonomous-refactor/chimera-autonomous-refactor.service \
   /etc/systemd/system/

# 2. Enable and start
sudo systemctl enable chimera-autonomous-refactor
sudo systemctl start chimera-autonomous-refactor

# 3. Check status
sudo systemctl status chimera-autonomous-refactor

# 4. View logs
journalctl -u chimera-autonomous-refactor -f
tail -f .claude/autonomous-refactor/loop.log
```

## Integration with Existing Components

### Ralph Engine (Already Exists)
- **Location**: `services/autonomous-agent/ralph_engine.py`
- **Purpose**: Persistent execution loop with Flow-Next architecture
- **Integration**: Extended with `TestHardeningTask` class

### Quality Gate Service (Already Exists)
- **Location**: `platform/quality-gate/gate/quality.py`
- **Purpose**: SLO-based deployment blocking
- **Integration**: Extended with `AntiGamingEvaluator` class

### E2E Tests (Playwright/TypeScript)
- **Location**: `tests/e2e/`
- **Purpose**: End-to-end integration tests
- **Integration**: Excluded from autonomous refactoring (Python pytest only)

## Differences from DGX Spark Specification

| DGX Spec | Project Chimera | Reason |
|----------|-----------------|--------|
| ARM64 (Grace-Blackwell) | x86_64 | Project Chimera runs on x86 |
| PyTorch nightly cu130 | Standard PyTorch wheels | x86_64 compatible |
| `flash-attn` prohibited | SDPA recommended | Both valid, SDPA more portable |
| Docker required | Optional (systemd) | Already running natively |

## What's Next? (Phase 2-6)

### Phase 2: Mutation Testing (Optional)
```bash
# Install mutmut
pip install mutmut

# Enable in evaluator
export CHIMERA_MUTATION_TESTS=true
```

### Phase 3: Git Worktree Isolation
- Already implemented in orchestrator
- Worktrees created in `.claude/autonomous-refactor/worktrees/`

### Phase 4: Claude Code CLI Integration
- Requires Claude Code CLI to be installed
- Executed via `claude -p` (headless mode)
- Maximum 15 tool calls per iteration

### Phase 5: Telemetry and Monitoring
```bash
# Metrics are written to:
# - .claude/autonomous-refactor/loop.log
# - evaluation_results.json
# - baseline_metrics.json
```

### Phase 6: Advanced Memory System
- `program.md`: Constitutional constraints
- `learnings.md`: Historical failures
- `queue.txt`: Task queue
- Future: `telemetry.json`: Performance metrics

## Troubleshooting

### Evaluator Always Returns Exit Code 5
```bash
# Check if Python dependencies are installed
pip install pytest pytest-cov

# Verify the script is executable
chmod +x platform/quality-gate/evaluate.sh
```

### Claude Code Not Found
```bash
# Install Claude Code CLI
npm install -g @anthropics/claude-code

# Verify installation
claude --version
```

### Worktree Creation Fails
```bash
# Check git status
git status

# Ensure main branch exists
git branch

# Clean up stale worktrees
git worktree prune
```

## Safety Features

1. **Ephemeral Worktrees**: Changes isolated from main branch
2. **Immutable Evaluator**: Agent cannot modify evaluation criteria
3. **Hard Reset on Failure**: Corrupted state purged automatically
4. **Resource Limits**: Max 20% CPU, 4GB memory (systemd)
5. **Commit Atomicity**: Changes only committed if ALL gates pass

## References

- **Original Specification**: DGX Spark GB101 Autonomous Refactoring Blueprint
- **Ralph Pattern**: Stateless iteration with external memory
- **AutoResearch**: Karpathy's tripartite environment (prepare.py, train.py, program.md)
- **Project Chimera**: https://github.com/project-chimera

## License

This autonomous refactoring system is part of Project Chimera and follows the same license terms.
