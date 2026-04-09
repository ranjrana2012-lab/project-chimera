# Project Chimera Phase 2 - Test Coverage Guide

**Version:** 1.0.0
**Last Updated:** April 9, 2026
**Target Audience:** Developers, QA Engineers, Technical Leads

---

## Table of Contents

1. [Overview](#overview)
2. [Coverage Requirements](#coverage-requirements)
3. [Running Tests](#running-tests)
4. [Generating Reports](#generating-reports)
5. [Coverage Targets](#coverage-targets)
6. [Improving Coverage](#improving-coverage)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to measure, analyze, and improve test coverage for Project Chimera Phase 2 services. We require **80% minimum test coverage** for all code.

### Coverage Metrics

- **Statement Coverage**: Percentage of executable statements run
- **Branch Coverage**: Percentage of code branches executed
- **Function Coverage**: Percentage of functions called
- **Line Coverage**: Percentage of code lines executed

---

## Coverage Requirements

### Minimum Thresholds

| Component | Statement | Branch | Function |
|-----------|-----------|--------|----------|
| DMX Controller | 80% | 75% | 80% |
| Audio Controller | 80% | 75% | 80% |
| BSL Avatar Service | 80% | 75% | 80% |
| Orchestration | 80% | 75% | 80% |
| Integration Tests | 70% | 65% | N/A |

### Critical Paths

100% coverage required for:

- Emergency stop/mute functionality
- Scene activation logic
- Audio volume limiting
- BSL translation safety

---

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=services --cov-report=html --cov-report=term

# Run with verbose output
pytest -v --cov=services --cov-report=html
```

### Run Service-Specific Tests

```bash
# DMX Controller tests
pytest tests/dmx-controller/test_*.py --cov=services/dmx_controller --cov-report=html

# Audio Controller tests
pytest tests/audio-controller/test_*.py --cov=services/audio_controller --cov-report=html

# BSL Avatar Service tests
pytest tests/bsl-avatar-service/test_*.py --cov=services/bsl_avatar_service --cov-report=html
```

### Run with Coverage Filter

```bash
# Only show coverage below threshold
pytest --cov=services --cov-fail-under=80

# Combine coverage from multiple runs
pytest --cov=services/dmx_controller --cov=services/audio_controller \
    --cov-append --cov-report=html
```

---

## Generating Reports

### HTML Report

```bash
# Generate HTML report
pytest --cov=services --cov-report=html:htmlcov

# Open report
python -m http.server 8000 --directory htmlcov
# Navigate to http://localhost:8000
```

### JSON Report

```bash
# Generate JSON report for CI/CD
pytest --cov=services --cov-report=json:coverage.json
```

### Terminal Report

```bash
# Show coverage in terminal
pytest --cov=services --cov-report=term-missing
```

### XML Report

```bash
# Generate XML report for CI tools
pytest --cov=services --cov-report=xml:coverage.xml
```

---

## Coverage Targets

### By Service Type

#### DMX Controller

| Module | Target | Current |
|-------|--------|---------|
| `dmx_controller.py` | 80% | ? |
| `fixtures.py` | 80% | ? |
| `scenes.py` | 80% | ? |

#### Audio Controller

| Module | Target | Current |
|-------|--------|---------|
| `audio_controller.py` | 80% | ? |
| `tracks.py` | 80% | ? |
| `volume.py` | 80% | ? |

#### BSL Avatar Service

| Module | Target | Current |
|-------|--------|---------|
| `bsl_avatar_service.py` | 80% | ? |
| `translator.py` | 80% | ? |
| `renderer.py` | 80% | ? |

### By Feature

| Feature | Target | Priority |
|---------|--------|----------|
| Emergency Procedures | 100% | Critical |
| Scene Activation | 90% | High |
| Audio Control | 85% | High |
| BSL Translation | 85% | High |
| Configuration | 75% | Medium |
| Logging | 70% | Low |

---

## Improving Coverage

### Identify Gaps

```bash
# Generate coverage report with missing lines
pytest --cov=services --cov-report=term-missing

# View HTML report to see uncovered lines
open htmlcov/index.html
```

### Common Gaps

1. **Error Handling**: Add tests for error paths
2. **Edge Cases**: Test boundary conditions
3. **Async Code**: Test async/await paths
4. **Configuration**: Test with different configs

### Writing Tests for Coverage

```python
# Example: Test error path
def test_emergency_stop_when_active():
    controller = DMXController()
    controller.activate_scene("test_scene")

    controller.emergency_stop()

    assert controller.state == DMXState.EMERGENCY_STOP
    assert all(ch.value == 0 for ch in get_all_channels())

# Example: Test edge case
def test_scene_with_zero_fixtures():
    controller = DMXController()
    scene = Scene("empty_scene", {}, transition_time_ms=0)

    controller.activate_scene("empty_scene")

    # Should handle gracefully
    assert controller.current_scene == "empty_scene"

# Example: Test async operation
@pytest.mark.asyncio
async def test_async_scene_activation():
    controller = DMXController()
    await controller.activate_scene_async("test_scene")

    assert controller.current_scene == "test_scene"
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -e ".[test]"
      - name: Run tests with coverage
        run: |
          pytest --cov=services --cov-report=xml --cov-report=term
      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest --cov=services --cov-fail-under=80
if [ $? -ne 0 ]; then
    echo "Coverage below 80% - commit blocked"
    exit 1
fi
```

### Makefile Integration

```makefile
.PHONY: test coverage

test:
    pytest tests/ -v

coverage:
    pytest --cov=services --cov-report=html --cov-report=term
    @echo "Coverage report generated in htmlcov/"

coverage-check:
    pytest --cov=services --cov-fail-under=80
```

---

## Troubleshooting

### Coverage Not Calculated

**Problem**: Coverage shows 0%

**Solution**:
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Check if tests are running
pytest -v tests/

# Verify coverage package structure
python -c "import services.dmx_controller"
```

### Import Errors in Coverage

**Problem**: `ModuleNotFoundError` during coverage

**Solution**:
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest with path
pytest --cov=services --cov-context=test
```

### Slow Coverage Calculation

**Problem**: Coverage takes too long

**Solution**:
```bash
# Use parallel execution
pytest -n auto --cov=services

# Profile slow tests
pytest --durations=10

# Run specific test files
pytest tests/dmx-controller/ --cov=services/dmx_controller
```

---

## Coverage Badges

### Adding Badge to README

```markdown
![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)
```

### Dynamic Badge with Codecov

```markdown
[![codecov](https://codecov.io/gh/ranjrana2012-lab/project-chimera/branch/main/graph/badge.svg)](https://codecov.io/gh/ranjrana2012-lab/project-chimera)
```

---

## Best Practices

### 1. Test Behavior, Not Implementation

```python
# GOOD: Tests behavior
def test_scene_activation_sets_current_scene():
    controller = DMXController()
    controller.activate_scene("test_scene")
    assert controller.current_scene == "test_scene"

# BAD: Tests implementation
def test_scene_activation_calls_internal_method():
    controller = DMXController()
    # Tests internal method that may change
    assert controller._internal_method_called()
```

### 2. Use Fixtures for Common Setup

```python
@pytest.fixture
def dmx_controller():
    return DMXController(universe=1)

def test_with_fixture(dmx_controller):
    dmx_controller.activate_scene("test")
    assert dmx_controller.current_scene == "test"
```

### 3. Parametrize Tests

```python
@pytest.mark.parametrize("scene_name", ["scene1", "scene2", "scene3"])
def test_multiple_scenes(dmx_controller, scene_name):
    dmx_controller.activate_scene(scene_name)
    assert dmx_controller.current_scene == scene_name
```

### 4. Test Async Code Properly

```python
@pytest.mark.asyncio
async def test_async_operation():
    controller = DMXController()
    result = await controller.async_operation()
    assert result is not None
```

---

## Coverage Tracking

### Track Coverage Over Time

```bash
# Generate baseline
pytest --cov=services --cov-report=json:coverage-baseline.json

# Compare with current
pytest --cov=services --cov-report=json:coverage-current.json

# Diff coverage
diff-cover coverage-baseline.json coverage-current.json
```

### Set Up Coverage Tracking

1. **Baseline**: Establish initial coverage
2. **Monitor**: Track changes in CI/CD
3. **Enforce**: Block PRs that reduce coverage
4. **Improve**: Regular coverage sprints

---

## References

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026
**Next Review:** When coverage drops below threshold
