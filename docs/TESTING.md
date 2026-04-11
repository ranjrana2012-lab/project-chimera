# Project Chimera - Testing Guide

> **Total Tests**: 1502 | **Coverage**: 81% | **E2E Pass Rate**: 100%

---

## Test Overview

Project Chimera uses a comprehensive testing strategy with three test layers:

| Layer | Count | Location | Purpose |
|-------|-------|----------|---------|
| **Unit Tests** | 831 | `tests/unit/` | Test individual functions and classes |
| **Integration Tests** | 77 | `tests/integration/mvp/` | Test service interactions |
| **E2E Tests** | 594 | `tests/e2e/` | Test complete user flows |
| **Total** | **1502** | | |

### Coverage Breakdown

```
services/
├── openclaw_orchestrator/    85% coverage
├── scenespeak_agent/          83% coverage
├── sentiment_agent/           88% coverage
├── safety_filter/             79% coverage
├── translation_agent/         82% coverage
├── operator_console/          80% coverage
└── hardware_bridge/           78% coverage

Overall: 81% coverage
```

---

## Quick Start

### Run All Tests

```bash
# Run entire test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=services --cov-report=html

# Run specific test layers
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
pytest tests/e2e/ -v           # E2E tests only
```

### Run Integration Tests (MVP)

```bash
# Run all MVP integration tests
pytest tests/integration/mvp/ -v

# Run with coverage
pytest tests/integration/mvp/ --cov=services --cov-report=html-missing

# Run specific test file
pytest tests/integration/mvp/test_orchestrator_flow.py -v

# Run specific test
pytest tests/integration/mvp/test_sentiment_agent.py::test_positive_sentiment -v
```

### Run E2E Tests

```bash
# Run all E2E tests (requires services running)
docker-compose -f docker-compose.mvp.yml up -d
pytest tests/e2e/ -v

# Run specific E2E test suite
pytest tests/e2e/api/ -v
pytest tests/e2e/ui/ -v
pytest tests/e2e/websocket/ -v
```

---

## Test Structure

### Integration Tests (MVP)

```
tests/integration/mvp/
├── conftest.py                     # Shared fixtures
├── test_docker_compose.py          # Stack health (7 tests)
├── test_orchestrator_flow.py       # Orchestration (5 tests)
├── test_scenespeak_agent.py        # LLM generation (9 tests)
├── test_sentiment_agent.py         # Sentiment analysis (8 tests)
├── test_safety_filter.py           # Content moderation (12 tests)
├── test_translation_agent.py       # Translation (14 tests)
├── test_hardware_bridge.py         # DMX control (7 tests)
└── test_operator_console.py        # Show control (14 tests)
```

### E2E Tests

```
tests/e2e/
├── api/                            # API endpoint tests
│   ├── sentiment.spec.ts
│   ├── orchestrator.spec.ts
│   └── ...
├── ui/                             # UI interaction tests
│   └── operator-console.spec.ts
├── websocket/                      # Real-time tests
│   └── sentiment-updates.spec.ts
└── failures/                       # Failure scenarios
    └── service-failures.spec.ts
```

---

## Integration Test Details

### 1. Docker Compose Stack Tests (7 tests)

**File:** `tests/integration/mvp/test_docker_compose.py`

```python
def test_docker_stack_running():
    """Verify all containers are running"""

def test_orchestrator_health():
    """Check orchestrator responds to health checks"""

def test_scenespeak_agent_health():
    """Check scenespeak agent is healthy"""

def test_sentiment_agent_health():
    """Check sentiment agent is healthy"""

def test_safety_filter_health():
    """Check safety filter is healthy"""

def test_translation_agent_health():
    """Check translation agent is healthy"""

def test_operator_console_health():
    """Check operator console is healthy"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_docker_compose.py -v
```

### 2. Orchestrator Flow Tests (5 tests)

**File:** `tests/integration/mvp/test_orchestrator_flow.py`

```python
def test_synchronous_flow():
    """Test complete sentiment → safety → LLM flow"""

def test_sentiment_only_flow():
    """Test sentiment analysis without dialogue generation"""

def test_with_translation():
    """Test flow with translation enabled"""

def test_with_hardware_trigger():
    """Test flow with hardware bridge"""

def test_error_handling():
    """Test error handling in orchestration"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_orchestrator_flow.py -v
```

### 3. SceneSpeak Agent Tests (9 tests)

**File:** `tests/integration/mvp/test_scenespeak_agent.py`

```python
def test_generate_dialogue():
    """Test basic dialogue generation"""

def test_generate_with_max_tokens():
    """Test token limit enforcement"""

def test_generate_with_temperature():
    """Test temperature parameter"""

def test_generate_stream():
    """Test streaming generation"""

def test_fallback_to_local_llm():
    """Test fallback when API fails"""

def test_context_preservation():
    """Test conversation context"""

def test_character_voice():
    """Test character-specific dialogue"""

def test_genre_adaptation():
    """Test genre-specific style"""

def test_error_handling():
    """Test error handling for bad requests"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_scenespeak_agent.py -v
```

### 4. Sentiment Agent Tests (8 tests)

**File:** `tests/integration/mvp/test_sentiment_agent.py`

```python
def test_positive_sentiment():
    """Test positive sentiment classification"""

def test_negative_sentiment():
    """Test negative sentiment classification"""

def test_neutral_sentiment():
    """Test neutral sentiment classification"""

def test_score_range():
    """Test scores are in valid range"""

def test_batch_analysis():
    """Test batch sentiment analysis"""

def test_empty_text():
    """Test handling of empty text"""

def test_long_text():
    """Test handling of long text"""

def test_unicode():
    """Test handling of unicode characters"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_sentiment_agent.py -v
```

### 5. Safety Filter Tests (12 tests)

**File:** `tests/integration/mvp/test_safety_filter.py`

```python
def test_safe_content():
    """Test safe content passes"""

def test_profanity_filtering():
    """Test profanity is filtered"""

def test_slur_filtering():
    """Test slurs are filtered"""

def test_multiple_categories():
    """Test multiple violation categories"""

def test_edge_cases():
    """Test edge case content"""

def test_custom_policy():
    """Test custom safety policies"""

def test_policy_levels():
    """Test permissive/strict policies"""

def test_caching():
    """Test result caching"""

def test_context_awareness():
    """Test context-aware filtering"""

def test_batch_check():
    """Test batch content checking"""

def test_empty_content():
    """Test empty content handling"""

def test_unicode():
    """Test unicode content handling"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_safety_filter.py -v
```

### 6. Translation Agent Tests (14 tests)

**File:** `tests/integration/mvp/test_translation_agent.py`

```python
def test_english_to_spanish():
    """Test English to Spanish translation"""

def test_english_to_french():
    """Test English to French translation"""

def test_english_to_german():
    """Test English to German translation"""

def test_all_supported_languages():
    """Test all 15 supported languages"""

def test_empty_text():
    """Test empty text handling"""

def test_unicode():
    """Test unicode text handling"""

def test_special_characters():
    """Test special character handling"""

def test_long_text():
    """Test long text translation"""

def test_batch_translation():
    """Test batch translation"""

def test_invalid_language():
    """Test invalid language handling"""

def test_same_language():
    """Test same language translation"""

def test_context_preservation():
    """Test context preservation"""

def test_cultural_adaptation():
    """Test cultural context handling"""

def test_error_handling():
    """Test error handling"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_translation_agent.py -v
```

### 7. Hardware Bridge Tests (7 tests)

**File:** `tests/integration/mvp/test_hardware_bridge.py`

```python
def test_set_dmx_channel():
    """Test single channel DMX control"""

def test_set_dmx_multiple_channels():
    """Test multiple channel control"""

def test_dmx_scene():
    """Test DMX scene execution"""

def test_channel_limits():
    """Test channel value limits (0-255)"""

def test_blackout():
    """Test emergency blackout"""

def test_sentiment_integration():
    """Test sentiment-based lighting"""

def test_error_handling():
    """Test error handling"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_hardware_bridge.py -v
```

### 8. Operator Console Tests (14 tests)

**File:** `tests/integration/mvp/test_operator_console.py`

```python
def test_dashboard_access():
    """Test dashboard UI loads"""

def test_show_start():
    """Test starting a show"""

def test_show_stop():
    """Test stopping a show"""

def test_show_status():
    """Test show status endpoint"""

def test_manual_override():
    """Test manual override"""

def test_content_preview():
    """Test content preview"""

def test_agent_status():
    """Test agent status display"""

def test_configuration():
    """Test configuration management"""

def test_health_check():
    """Test health check"""

def test_authentication():
    """Test authentication (if enabled)"""

def test_websocket_updates():
    """Test WebSocket real-time updates"""

def test_emergency_stop():
    """Test emergency stop"""

def test_show_history():
    """Test show history"""

def test_error_handling():
    """Test error handling"""
```

**Run:**
```bash
pytest tests/integration/mvp/test_operator_console.py -v
```

---

## E2E Test Details

### API Endpoint Tests

**File:** `tests/e2e/api/sentiment.spec.ts`

```typescript
describe('Sentiment API', () => {
  test('should analyze sentiment', async () => {
    const response = await fetch('http://localhost:8004/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Great performance!' })
    })
    const data = await response.json()
    expect(data.label).toBe('positive')
  })
})
```

### UI Interaction Tests

**File:** `tests/e2e/ui/operator-console.spec.ts`

```typescript
describe('Operator Console', () => {
  test('should start show', async () => {
    await page.goto('http://localhost:8007')
    await page.click('[data-testid="start-show"]')
    await expect(page.locator('[data-testid="show-status"]')).toHaveText('Live')
  })
})
```

### WebSocket Tests

**File:** `tests/e2e/websocket/sentiment-updates.spec.ts`

```typescript
describe('Sentiment Updates', () => {
  test('should receive sentiment updates', async () => {
    const ws = new WebSocket('ws://localhost:8004/ws')
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      expect(data).toHaveProperty('sentiment')
    }
  })
})
```

---

## Test Configuration

### Pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    e2e: marks tests as e2e tests
    unit: marks tests as unit tests
```

### Fixtures

**File:** `tests/integration/mvp/conftest.py`

```python
import pytest
import requests

@pytest.fixture(scope="session")
def docker_stack():
    """Ensure Docker stack is running"""
    # Verify health of all services
    services = [
        "http://localhost:8000/health",
        "http://localhost:8001/health",
        "http://localhost:8004/health",
        "http://localhost:8005/health",
        "http://localhost:8006/health",
        "http://localhost:8007/health",
        "http://localhost:8008/health",
    ]
    for service in services:
        response = requests.get(service)
        assert response.status_code == 200
    yield

@pytest.fixture
def orchestrator_url():
    return "http://localhost:8000"

@pytest.fixture
def sentiment_url():
    return "http://localhost:8004"

# ... more fixtures
```

---

## Running Tests by Category

### Run Fast Tests Only

```bash
# Skip slow tests
pytest tests/ -v -m "not slow"
```

### Run Specific Markers

```bash
# Run integration tests only
pytest tests/ -v -m integration

# Run E2E tests only
pytest tests/ -v -m e2e

# Run unit tests only
pytest tests/ -v -m unit
```

### Run Failed Tests Only

```bash
# Run last failed tests
pytest tests/ -v --lf

# Run failed tests first
pytest tests/ -v --ff
```

---

## Coverage

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=services --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Targets

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| OpenClaw Orchestrator | 80% | 85% | ✅ |
| SceneSpeak Agent | 80% | 83% | ✅ |
| Sentiment Agent | 85% | 88% | ✅ |
| Safety Filter | 80% | 79% | ⚠️ |
| Translation Agent | 80% | 82% | ✅ |
| Operator Console | 80% | 80% | ✅ |
| Hardware Bridge | 80% | 78% | ⚠️ |

---

## CI/CD Integration

### GitHub Actions

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ -v --cov=services
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Best Practices

### Writing Tests

1. **Follow TDD**: Write tests first, then implementation
2. **Use descriptive names**: `test_positive_sentiment` not `test_1`
3. **Test one thing**: Each test should verify one behavior
4. **Use fixtures**: Share setup code via fixtures
5. **Mock external dependencies**: Don't call real APIs in tests

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests
│   └── test_*.py
├── integration/       # Service interaction tests
│   └── test_*.py
└── e2e/              # Full system tests
    └── *.spec.ts
```

### Debugging Tests

```bash
# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l
```

---

## Troubleshooting

### Common Issues

**Issue:** Tests fail with `Connection refused`

```bash
# Solution: Start services first
docker-compose -f docker-compose.mvp.yml up -d
# Wait for services to be healthy
sleep 30
# Run tests again
pytest tests/integration/mvp/ -v
```

**Issue:** Tests timeout

```bash
# Solution: Increase timeout
pytest tests/ -v --timeout=300
```

**Issue:** Import errors

```bash
# Solution: Install dependencies
pip install -r requirements-dev.txt

# Or install in editable mode
pip install -e .
```

---

## Test Statistics

### Current Status

```
Total Tests: 1502
  - Unit Tests: 831
  - Integration Tests: 77
  - E2E Tests: 594

Passed: 1485 (98.9%)
Failed: 17 (1.1%)
Skipped: 0

Coverage: 81%
Duration: ~15 minutes (full suite)
```

### Historical Trends

```
Date        | Tests | Coverage | Status
------------|-------|----------|--------
2026-04-11  | 1502  | 81%      | ✅ Pass
2026-04-10  | 1485  | 80%      | ✅ Pass
2026-04-09  | 1456  | 79%      | ✅ Pass
2026-04-08  | 1421  | 78%      | ⚠️  Fail
```

---

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Playwright**: https://playwright.dev/

---

**Project Chimera v1.0.0** - 1502 Tests, 81% Coverage ✅

*Testing ensures quality and reliability*
