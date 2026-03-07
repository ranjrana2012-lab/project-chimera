# Testing Guide Tutorial

**Type:** Video Script / Screencast Tutorial
**Duration:** 20-25 minutes
**Target Audience:** Students needing to write tests for their contributions
**Prerequisites:** Environment setup complete

---

## Script Outline

### Part 1: Introduction (0:00-1:00)

**Visual:** Title card - "Testing in Project Chimera"

**Speaker:** "Testing is essential for maintaining code quality in Project Chimera. This tutorial covers how to write tests, run them, and ensure your contributions are bug-free."

---

### Part 2: Testing Overview (1:00-3:00)

**Visual:** Diagram showing test structure

**Speaker:** "Project Chimera uses three types of tests:
1. **Unit Tests** - Test individual functions and classes in isolation
2. **Integration Tests** - Test how services work together
3. **End-to-End Tests** - Test complete user flows"

**Visual:** File structure
```
tests/
├── unit/              # Unit tests
│   ├── services/
│   │   ├── scenespeak/
│   │   ├── captioning/
│   │   └── safety/
│   └── platform/
├── integration/       # Integration tests
└── e2e/               # End-to-end tests
```

---

### Part 3: Writing Unit Tests (3:00-8:00)

**Speaker:** "Let's write a unit test for the SceneSpeak Agent. Open the test file:"

**Visual:** VS Code with `tests/unit/services/scenespeak/test_generator.py`

```python
import pytest
from services.scenespeak.generator import DialogueGenerator

@pytest.fixture
def generator():
    """Create a test generator instance."""
    return DialogueGenerator(adapter="test")

def test_generate_dialogue_basic(generator):
    """Test basic dialogue generation."""
    from services.scenespeak.models import DialogueRequest

    request = DialogueRequest(
        prompt="Hello world",
        max_tokens=100
    )

    response = generator.generate(request)

    assert response.text is not None
    assert len(response.text) > 0
    assert response.adapter == "test"
```

**Speaker:** "Key points:
- Use `@pytest.fixture` for reusable test objects
- Use descriptive test names: `test_<function>_<scenario>`
- Arrange-Act-Assert pattern:
  1. Arrange: Set up test data
  2. Act: Call the function
  3. Assert: Verify the result"

**Speaker:** "Let's add a parametrized test:"

```python
@pytest.mark.parametrize("adapter,expected", [
    ("gpt-4", "gpt-4"),
    ("claude", "claude"),
])
def test_adapter_selection(generator, adapter, expected):
    """Test that the correct adapter is selected."""
    generator.adapter = adapter
    assert generator.adapter == expected
```

---

### Part 4: Running Tests (8:00-11:00)

**Speaker:** "Run your tests with pytest:"

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/services/scenespeak/test_generator.py

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run only unit tests
pytest tests/unit/ -m "not integration"
```

**Visual:** Terminal showing test output

```bash
$ pytest tests/unit/services/scenespeak/test_generator.py

========================== test session starts ==========================
tests/unit/services/scenespeak/test_generator.py::test_generate_dialogue_basic PASSED
tests/unit/services/scenespeak/test_generator.py::test_adapter_selection PASSED

========================== 2 passed in 1.5s ==============================
```

---

### Part 5: Test Coverage (11:00-14:00)

**Speaker:** "Track test coverage to ensure you're testing enough code:"

```bash
# Generate coverage report
pytest --cov=services --cov-report=html

# Open coverage report
open htmlcov/index.html
```

**Visual:** Browser showing coverage report

**Speaker:** "Aim for:
- Unit tests: 80%+ coverage
- Integration tests: Critical paths covered
- E2E tests: Main user flows"

**Speaker:** "The coverage report shows:
- Lines covered (green)
- Lines not covered (red)
- Coverage percentage per file"

---

### Part 6: Mocking and Fixtures (14:00-17:00)

**Speaker:** "Use mocks to test code in isolation:"

```python
from unittest.mock import Mock, patch
import pytest

def test_with_mock():
    """Test with mocked external dependencies."""
    # Create mock
    mock_llm = Mock()
    mock_llm.generate.return_value = "Test response"

    # Use mock
    with patch('services.scenespeak.generator.LLM', return_value=mock_llm):
        response = generator.generate(request)

    # Verify mock was called
    mock_llm.generate.assert_called_once()

    # Verify result
    assert response.text == "Test response"
```

**Speaker:** "Use fixtures for complex setup:"

```python
@pytest.fixture
async def async_client():
    """Create async test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_api_endpoint(async_client):
    """Test API endpoint with async client."""
    response = await async_client.post(
        "/api/v1/scenespeak/generate",
        json={"prompt": "Test"}
    )
    assert response.status_code == 200
```

---

### Part 7: Integration Tests (17:00-20:00)

**Speaker:** "Integration tests test how services work together:"

```python
@pytest.mark.integration
def test_dialogue_generation_flow():
    """Test complete dialogue generation flow."""
    # 1. Create request
    request = DialogueRequest(prompt="Test prompt")

    # 2. Call orchestrator
    response = client.post("/api/v1/orchestrator/dialogue", json=request.dict())

    # 3. Verify response
    assert response.status_code == 200
    data = response.json()
    assert "dialogue" in data
    assert "metadata" in data

    # 4. Verify services were called
    # SceneSpeak was called
    # Safety filter was checked
    # Response is safe
```

**Speaker:** "Integration tests are slower but test real interactions between services."

---

### Part 8: Troubleshooting Failed Tests (20:00-22:00)

**Speaker:** "When tests fail, debug systematically:"

**Visual:** Failed test output

```bash
$ pytest tests/unit/services/scenespeak/test_generator.py::test_generate_dialogue_basic

FAILED - assert response.text is not None
AssertionError: assert None is not None
```

**Speaker:** "Debug steps:
1. Read the error message carefully
2. Add print statements or use debugger
3. Check if fixtures are working
4. Verify test data is correct
5. Check if external dependencies are mocked"

**Speaker:** "Use pytest's built-in debugging:"

```bash
# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

---

### Part 9: Best Practices (22:00-25:00)

**Speaker:** "Testing best practices:

1. **One assertion per test** - Keep tests focused
2. **Descriptive names** - `test_<function>_<scenario>`
3. **Arrange-Act-Assert** - Clear test structure
4. **Use fixtures** - Avoid code duplication
5. **Mock external dependencies** - Keep tests fast
6. **Test edge cases** - Empty inputs, nulls, boundaries
7. **Keep tests independent** - No test dependencies
8. **Run tests before committing** - Always!"

**Speaker:** "Test checklist before committing:
- [ ] All tests pass locally
- [ ] New tests added for new code
- [ ] Coverage maintained or improved
- [ ] No hardcoded values
- [ ] Tests are readable and maintainable"

---

## Summary

**Visual:** Recap checklist

- ✅ Understand test types (unit, integration, e2e)
- ✅ Write unit tests with pytest
- ✅ Run tests and check coverage
- ✅ Use mocking and fixtures
- ✅ Write integration tests
- ✅ Debug failed tests
- ✅ Follow best practices

**Speaker:** "You now have the skills to write tests for Project Chimera! Check out:
- [Testing Runbook](../../runbooks/testing-guide.md) - Complete testing documentation
- [API Documentation](../../api/) - Service API references
- [Development Guide](../../DEVELOPMENT.md) - Development workflow

Happy testing! 🧪"

---

**Next Tutorial:** [Debugging Guide](03-debugging-guide.md) - Learn how to troubleshoot common issues.

---

*Testing Guide Tutorial - Project Chimera v0.4.0 - March 2026*
