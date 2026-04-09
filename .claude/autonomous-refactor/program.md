# Ralph Loop Constitutional Constraints

## Platform Constraints

**Target Runtime:**
- **OS:** x86_64 Linux (Ubuntu 22.04+)
- **Python:** 3.10+
- **Framework:** FastAPI
- **Deployment:** Vercel (Services runtime)

**Hard Constraints:**
- No macOS-specific code (e.g., `/Applications`, `.app` bundles)
- No Windows-specific code (e.g., `C:\`, Registry)
- No ARM64-specific optimizations
- No Python 3.12+ features (f-strings with debugging, type parameter defaults)
- No async framework changes (FastAPI required)
- No breaking changes to Vercel deployment config

## Bounded Changes Rule

**ONE logical component per iteration**

Ralph Loop MUST NOT:
- Modify multiple services in one commit
- Change deployment architecture
- Add new framework dependencies
- Refactor across service boundaries

Ralph Loop MUST:
- Scope changes to one service/module
- Verify tests pass before committing
- Document what was changed and why

## What Ralph Loop CAN Do

### Code Quality Improvements
- Add missing unit tests
- Improve test coverage (target: 80%+)
- Add type hints to untyped functions
- Fix deprecation warnings
- Improve error handling
- Add docstrings to undocumented functions
- Extract magic values to named constants
- Improve variable/function naming
- Reduce code duplication

### Architectural Improvements
- Extract utility functions to shared modules
- Improve module organization
- Add missing error logging
- Implement proper exception handling
- Add input validation
- Improve API response consistency

### Documentation
- Add inline comments for complex logic
- Update module docstrings
- Document API endpoints
- Add examples in docstrings

## What Ralph Loop CANNOT Do

### Forbidden Actions
- **NEVER delete or disable tests** (even if they fail)
- **NEVER stub failing tests** (must fix the underlying issue)
- **NEVER remove error handling** (only improve it)
- **NEVER silence warnings** (fix the root cause)
- **NEVER reduce test coverage** (only increase)
- **NEVER add new dependencies** without explicit justification
- **NEVER change deployment config** (vercel.json, infrastructure)
- **NEVER modify frozen services** (OpenClaw, BSL)

### Forbidden Patterns
- `# type: ignore` comments (fix the actual type issue)
- `pytest.mark.skip` decorators (fix the test)
- `except: pass` or `except Exception: pass` (handle errors properly)
- Commenting out failing code
- Reducing assertion specificity

## Quality Gates

### Pre-Commit Checks

1. **pytest exit code MUST be 0**
   ```bash
   pytest services/<service>/tests/ -v
   ```
   Exit code 0 is the only acceptable result.

2. **Assertion density MUST NOT decrease**
   - Count assertions before: `grep -r "assert" services/<service>/tests/ | wc -l`
   - Count assertions after: must be >= before

3. **Coverage MUST NOT decrease**
   - Generate coverage: `pytest --cov=services.<service> --cov-report=term-missing`
   - Current coverage >= baseline coverage

4. **Deprecation warnings MUST be fixed**
   - Run tests: `pytest -W error::DeprecationWarning`
   - Zero deprecation warnings allowed

### Test Quality Standards

- **No stubbed tests:** Every test must verify real behavior
- **No commented-out tests:** Delete or fix, never comment out
- **No broad exceptions:** Tests must fail for the right reason
- **No hardcoded values:** Use fixtures or test data factories

## Failure Consequences

| Failure Type | Consequence | Recovery |
|--------------|-------------|----------|
| pytest exits non-zero | Commit rejected | Fix tests, retry |
| Assertion count decreases | Rollback required | Restore deleted assertions |
| Coverage decreases | Rollback required | Restore removed code/tests |
| New deprecation warning | Rollback required | Fix deprecation source |
| Frozen service modified | Critical violation | Revert all changes |
| Type comment added | Warning | Replace with proper type hint |

## Active Services

Ralph Loop may improve these 6 services:

1. **nemo-claw** - LLM orchestration service
2. **scenespeak** - Scene dialogue generation
3. **sentiment** - Sentiment analysis engine
4. **safety** - Content moderation & safety
5. **captioning** - Image captioning service
6. **audio** - Audio processing & TTS

## Frozen Services

These 2 services are OFF LIMITS:

1. **OpenClaw** - Legacy claw machine control (DO NOT MODIFY)
2. **BSL** - British Sign Language generation (DO NOT MODIFY)

**Reason:** These services have external hardware dependencies and are outside the autonomous refactor scope.

## Workflow Steps

For each iteration:

1. **Read queue.txt** - Select highest-priority task
2. **Read learnings.md** - Understand progress context
3. **Create branch** - `git checkout -b ralph-loop-<task-name>`
4. **Make changes** - Follow bounded changes rule
5. **Run quality gates** - Verify all 4 gates pass
6. **Write commit message** - Conventional commit format
7. **Update learnings.md** - Document what changed
8. **Update queue.txt** - Remove completed task, add new tasks if needed
9. **Commit** - `git commit -m "<type>: <description>"`
10. **Repeat** - Move to next task

## Documentation Requirements

Every commit MUST include:

1. **Commit message body** explaining:
   - What was changed
   - Why it was an improvement
   - What tests were added/modified
   - Any trade-offs or considerations

2. **Update to learnings.md** with:
   - Date and timestamp
   - Service affected
   - Change description
   - Test coverage impact
   - Any issues encountered

## Success Criteria

**By June 5, 2026 (8 weeks):**

- [ ] 50+ commits to main branch
- [ ] All 6 active services have 80%+ test coverage
- [ ] Zero deprecation warnings across all services
- [ ] All public APIs have type hints
- [ ] All services have comprehensive docstrings
- [ ] No `# type: ignore` comments remain
- [ ] No stubbed or skipped tests remain
- [ ] Baseline metrics improved by 20%+

## Emergency Stop

If ANY of these occur, STOP immediately and contact human:

1. **Test suite becomes permanently broken** (>3 iterations failing)
2. **Deployment fails** (Vercel build or runtime errors)
3. **Frozen service is modified** (even accidentally)
4. **Platform constraint violated** (macOS/Windows code added)
5. **Quality gate cannot be satisfied** (fundamental issue discovered)

---

**Constitution Version:** 1.0
**Last Updated:** 2026-04-09
**Agent:** Ralph Loop (autonomous-refactor)
