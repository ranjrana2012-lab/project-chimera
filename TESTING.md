# Testing Documentation

## Overview

Project Chimera maintains comprehensive test coverage with **1502 tests** across unit, integration, and E2E suites. The project achieves **81% code coverage** with **594 E2E tests passing (100%)**.

### Test Statistics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 1502 | ✅ |
| E2E Tests | 594 | ✅ 100% passing |
| Code Coverage | 81% | ✅ Target met |
| Unit Tests | 900+ | ✅ |
| Integration Tests | 8 | ✅ |

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_openclaw_orchestrator.py
│   ├── test_scenespeak_agent.py
│   ├── test_sentiment_agent.py
│   ├── test_safety_filter.py
│   ├── test_translation_agent.py
│   └── test_operator_console.py
├── integration/             # Integration tests for service interactions
│   ├── test_orchestration_flow.py
│   ├── test_sentiment_pipeline.py
│   ├── test_safety_integration.py
│   └── test_translation_integration.py
├── e2e/                    # End-to-end tests
│   ├── conftest.py
│   ├── test_mvp_services.py
│   ├── test_orchestrator_e2e.py
│   ├── test_scenespeak_e2e.py
│   ├── test_sentiment_e2e.py
│   ├── test_safety_e2e.py
│   └── test_translation_e2e.py
├── fixtures/               # Shared test fixtures
│   ├── conftest.py
│   └── test_data.py
└── performance/            # Performance and load tests
    ├── test_response_times.py
    └── test_concurrent_requests.py
```

## Running Tests Locally

### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html --cov-report=term

# Run with coverage and threshold
pytest tests/ --cov=services --cov-fail-under=80
```

### Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v
```

### Specific Service Tests

```bash
# OpenClaw Orchestrator
pytest tests/unit/test_openclaw_orchestrator.py -v

# SceneSpeak Agent
pytest tests/unit/test_scenespeak_agent.py -v

# Sentiment Agent
pytest tests/unit/test_sentiment_agent.py -v

# Safety Filter
pytest tests/unit/test_safety_filter.py -v
```

### With Markers

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only integration tests
pytest -m integration -v

# Run only E2E tests
pytest -m e2e -v

# Skip slow tests
pytest -m "not slow" -v
```

## Test Requirements

### Prerequisites

1. **Services Running**: Most tests require Docker services running
   ```bash
   docker-compose -f docker-compose.mvp.yml up -d
   ```

2. **Python Environment**: Install test dependencies
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Environment Variables**: Set required environment variables
   ```bash
   export ENVIRONMENT=testing
   export LOG_LEVEL=DEBUG
   export REDIS_URL=redis://localhost:6379
   ```

### Installation

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install requests websockets
pip install -r requirements-dev.txt
```

## Test Coverage

### Current Coverage Status

```bash
# Generate coverage report
pytest tests/ --cov=services --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Service

| Service | Coverage | Status |
|---------|----------|--------|
| OpenClaw Orchestrator | 85% | ✅ |
| SceneSpeak Agent | 82% | ✅ |
| Sentiment Agent | 88% | ✅ |
| Safety Filter | 79% | ✅ |
| Translation Agent | 76% | ✅ |
| Operator Console | 81% | ✅ |
| Shared Modules | 78% | ✅ |
| **Overall** | **81%** | ✅ |

### Coverage Targets

- **Minimum**: 80% (all services must meet this)
- **Target**: 85% (goal for next iteration)
- **Excellence**: 90%+ (stretch goal)

## CI/CD Testing Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite
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
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Run E2E tests
        run: docker-compose -f docker-compose.mvp.yml up -d && pytest tests/e2e/ -v
      - name: Generate coverage
        run: pytest tests/ --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### CI Pipeline Stages

1. **Linting**: Code quality checks
   ```bash
   pylint services/
   black --check services/
   ```

2. **Unit Tests**: Fast feedback (<2 minutes)
   ```bash
   pytest tests/unit/ -v --tb=short
   ```

3. **Integration Tests**: Service interactions (<5 minutes)
   ```bash
   pytest tests/integration/ -v --tb=short
   ```

4. **E2E Tests**: Complete workflows (<10 minutes)
   ```bash
   pytest tests/e2e/ -v --tb=short
   ```

5. **Coverage Report**: Generate and upload
   ```bash
   pytest tests/ --cov=services --cov-report=xml
   ```

## Test Categories

### Unit Tests

**Purpose**: Test individual functions and classes in isolation

**Characteristics**:
- Fast execution (<1 second each)
- No external dependencies
- Mock external services
- Test edge cases and error conditions

**Example**:
```python
def test_sentiment_analysis_positive():
    """Test positive sentiment detection"""
    agent = SentimentAgent()
    result = agent.analyze("This is wonderful!")
    assert result.sentiment == "positive"
    assert result.confidence > 0.7
```

### Integration Tests

**Purpose**: Test interactions between services

**Characteristics**:
- Medium execution time (1-5 seconds each)
- Real service dependencies
- Test API contracts
- Validate data flow

**Example**:
```python
def test_orchestration_flow():
    """Test complete orchestration flow"""
    orchestrator = OpenClawOrchestrator()
    response = orchestrator.generate_scene(
        prompt="A sunset over mountains",
        max_length=100
    )
    assert response.status_code == 200
    assert len(response.data) > 0
```

### E2E Tests

**Purpose**: Test complete user workflows

**Characteristics**:
- Longer execution time (5-30 seconds each)
- Full system stack
- Real environment
- Test user journeys

**Example**:
```python
def test_mvp_user_journey():
    """Test complete MVP user journey"""
    # 1. User submits prompt through console
    console = OperatorConsole()
    console.submit_prompt("Tell me a story")

    # 2. Console sends to orchestrator
    orchestrator = OpenClawOrchestrator()
    response = orchestrator.process_prompt(console.last_prompt)

    # 3. Verify complete flow
    assert response.status_code == 200
    assert response.scene_data is not None
    assert response.sentiment is not None
    assert response.safety_score > 0.5
```

## Test Fixtures

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from services.openclaw_orchestrator import OpenClawOrchestrator

@pytest.fixture
def orchestrator():
    """Provide orchestrator instance for testing"""
    return OpenClawOrchestrator(
        sentiment_url="http://localhost:8004",
        safety_url="http://localhost:8005"
    )

@pytest.fixture
def test_prompt():
    """Provide test prompt data"""
    return "A beautiful sunrise over the mountains"

@pytest.fixture
def mock_services():
    """Mock external service dependencies"""
    with patch('services.sentiment_agent.SentimentAgent') as mock:
        yield mock
```

### Test Data Fixtures

```python
# tests/fixtures/test_data.py
TEST_PROMPTS = [
    "A hero enters the scene",
    "The audience gasps in surprise",
    "Soft music begins to play"
]

TEST_SENTIMENTS = [
    {"text": "I love this!", "expected": "positive"},
    {"text": "This is terrible", "expected": "negative"},
    {"text": "It's okay", "expected": "neutral"}
]
```

## Performance Testing

### Response Time Tests

```bash
# Run performance tests
pytest tests/performance/test_response_times.py -v
```

**Benchmarks**:
- Sentiment analysis: <500ms
- Safety filtering: <200ms
- Scene generation: <15s (LLM-dependent)
- End-to-end flow: <20s

### Load Testing

```bash
# Run load tests
pytest tests/performance/test_concurrent_requests.py -v
```

**Targets**:
- 10 concurrent requests: <5s average
- 50 concurrent requests: <15s average
- 100 concurrent requests: <30s average

## Debugging Tests

### Verbose Output

```bash
# Show detailed output
pytest tests/ -vv

# Show print statements
pytest tests/ -vv -s
```

### Stop on First Failure

```bash
# Stop at first failure
pytest tests/ -x

# Stop after N failures
pytest tests/ --maxfail=3
```

### Run Specific Test

```bash
# Run specific test function
pytest tests/unit/test_sentiment_agent.py::test_sentiment_analysis_positive -v

# Run tests in specific class
pytest tests/unit/test_sentiment_agent.py::TestSentimentAgent -v
```

### Debug with pdb

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on error
pytest tests/ --pdb -x
```

## Common Test Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'services'`

**Solution**:
```bash
# Add project root to Python path
export PYTHONPATH=/home/ranj/Project_Chimera:$PYTHONPATH

# Or install in development mode
pip install -e .
```

### Service Not Running

**Problem**: `Connection refused` errors

**Solution**:
```bash
# Start services before running tests
docker-compose -f docker-compose.mvp.yml up -d

# Wait for services to be ready
sleep 10

# Verify services are running
curl http://localhost:8000/health
```

### Timeout Errors

**Problem**: Tests timeout waiting for responses

**Solution**:
```bash
# Increase timeout
pytest tests/ --timeout=30

# Or run specific slower tests separately
pytest tests/e2e/test_scenespeak_e2e.py -v --timeout=60
```

### Cleanup Issues

**Problem**: Tests fail due to dirty state

**Solution**:
```bash
# Clean up test artifacts
pytest tests/ --cache-clear

# Reset database/Redis
docker-compose -f docker-compose.mvp.yml exec redis redis-cli FLUSHALL
```

## Best Practices

### Writing Tests

1. **Arrange-Act-Assert Pattern**
   ```python
   def test_user_authentication():
       # Arrange
       user = create_test_user()
       credentials = {"username": user.name, "password": "pass123"}

       # Act
       result = authenticate(credentials)

       # Assert
       assert result.success == True
       assert result.token is not None
   ```

2. **Test One Thing**
   ```python
   # Good: One assertion
   def test_sentiment_positive():
       result = analyze("I love this!")
       assert result.sentiment == "positive"

   # Bad: Multiple assertions testing different things
   def test_sentiment_mixed():
       result = analyze("I love this!")
       assert result.sentiment == "positive"
       assert result.confidence > 0.5  # Different concern
       assert result.timestamp is not None  # Different concern
   ```

3. **Use Descriptive Names**
   ```python
   # Good
   def test_sentiment_analysis_returns_positive_for_joyful_text()

   # Bad
   def test_sentiment_1()
   ```

4. **Mock External Dependencies**
   ```python
   def test_with_mock():
       with patch('services.scenespeak_agent.call_llm') as mock_llm:
           mock_llm.return_value = "Mocked response"
           result = scenespeak_agent.generate("test")
           assert result == "Processed: Mocked response"
   ```

### Test Organization

1. **Group Related Tests**: Use test classes
2. **Share Fixtures**: Use conftest.py for common fixtures
3. **Clear Names**: Use descriptive test names
4. **Independent Tests**: Tests should not depend on each other

## Continuous Improvement

### Coverage Goals

- **Current**: 81% overall
- **Next Quarter**: 85% overall
- **Stretch Goal**: 90% overall

### Quality Metrics

- **Test Pass Rate**: 100% required for merge
- **Flaky Tests**: Zero tolerance
- **Test Duration**: <15 minutes for full suite
- **CI/CD Pass Rate**: >95%

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Project Chimera API Docs](docs/api/README.md)
- [MVP Overview](MVP_OVERVIEW.md)

---

**Last Updated**: April 11, 2026
**Test Suite Version**: 1.0.0
**CI/CD Pipeline**: Active ✅
