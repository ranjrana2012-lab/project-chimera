# Contributing to Project Chimera

Thank you for your interest in contributing to Project Chimera! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Linux (Ubuntu 22.04 recommended) or macOS
- Python 3.10 or later
- Docker and Docker Compose
- Git
- NVIDIA GPU (optional, for full feature support)

**New contributors:** See [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) for comprehensive developer onboarding guide.

### Initial Setup

1. **Fork and Clone**

   ```bash
   # Fork the repository on GitHub
   git clone https://github.com/YOUR_USERNAME/project-chimera.git
   cd project-chimera
   ```

2. **Install Dependencies**

   ```bash
   # Install Python dependencies
   make install-deps

   # Or manually
   pip install -e ".[dev]"
   ```

3. **Set Up Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start Development Environment**

   ```bash
   make dev
   ```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
pytest --cov=services --cov-report=html
```

## Development Workflow

We follow a Git-based workflow with feature branches:

1. **Create a Branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make Changes**

   - Write clear, concise code
   - Follow our coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**

   ```bash
   # Run linter
   make lint

   # Format code
   make format

   # Run tests
   make test
   ```

4. **Commit Your Changes**

   - Write descriptive commit messages (see [Commit Messages](#commit-messages))
   - Sign off your commits (`git commit -s -m "..."`)

5. **Push and Create Pull Request**

   ```bash
   git push origin feature/your-feature-name
   # Then create a PR on GitHub
   ```

## Coding Standards

### Python Code Style

We follow PEP 8 with these specific tools:

- **Black** - Code formatting (line length: 100)
- **Ruff** - Linting
- **MyPy** - Type checking

### Code Organization

```python
# Standard library imports
import os
from typing import Optional

# Third-party imports
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from services.shared.config import settings


class MyModel(BaseModel):
    """Class docstring."""

    def __init__(self, value: str):
        """Initialize the model."""
        self.value = value

    def method(self) -> str:
        """Method docstring."""
        return self.value
```

### Naming Conventions

- **Modules:** `lowercase_with_underscores`
- **Classes:** `CapitalizedWords`
- **Functions/Methods:** `lowercase_with_underscores`
- **Constants:** `UPPERCASE_WITH_UNDERSCORES`
- **Private:** `_leading_underscore`

### Documentation

- Use docstrings for all modules, classes, and public functions
- Follow Google docstring style
- Include type hints for all functions

```python
def calculate_sentiment(text: str) -> dict[str, float]:
    """Calculate sentiment scores for the given text.

    Args:
        text: The input text to analyze.

    Returns:
        A dictionary containing sentiment scores with keys:
        - positive: float (0-1)
        - negative: float (0-1)
        - neutral: float (0-1)

    Raises:
        ValueError: If text is empty or None.

    Example:
        >>> calculate_sentiment("I love this!")
        {'positive': 0.9, 'negative': 0.05, 'neutral': 0.05}
    """
    ...
```

### Type Hints

```python
from typing import Optional, List, Dict, Any
from services.shared.models import BaseModel

def process_items(
    items: List[BaseModel],
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Process a list of items."""
    ...
```

## Testing Guidelines

### Test Coverage

- Aim for 80%+ code coverage (currently: 78% unit, 75% integration)
- All new features must include tests
- Bug fixes must include regression tests

**Current test infrastructure:**
- Unit tests: 700+ tests
- Integration tests: 25+ tests
- E2E tests: 594 tests (100% passing)
- Load testing: Locust framework with 50+ concurrent users support

See [tests/TEST_SETUP.md](tests/TEST_SETUP.md) for complete testing guide.

### Test Structure

```python
# tests/unit/services/test_scenespeak_agent.py

import pytest
from services.scenespeak_agent.core import LLMEngine


class TestLLMEngine:
    """Test suite for LLMEngine."""

    @pytest.fixture
    def engine(self):
        """Create a test engine instance."""
        return LLMEngine(model_path="test-model")

    def test_generate_dialogue(self, engine):
        """Test dialogue generation."""
        result = engine.generate("Hello", max_tokens=10)
        assert isinstance(result, str)
        assert len(result) > 0
```

### Test Categories

- **Unit Tests:** Test individual functions/classes in isolation
- **Integration Tests:** Test interactions between services
- **E2E Tests:** Test complete user journeys through the system
- **Load Tests:** Test performance under load (Locust framework)
- **Performance Tests:** Benchmark key services and operations
- **Red Team Tests:** Test security and safety features
- **Accessibility Tests:** Test WCAG compliance

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/services/test_scenespeak_agent.py -v

# Specific test
pytest tests/unit/services/test_scenespeak_agent.py::TestLLMEngine::test_generate_dialogue -v

# With coverage
pytest tests/ --cov=services --cov-report=html

# Load tests
pytest tests/load/ -v

# Red team tests
pytest tests/red-team/ -v
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `chore`: Build process or tooling changes
- `ci`: CI/CD changes

### Examples

```
feat(scenespeak): add dialogue caching mechanism

Implement Redis-based caching for generated dialogue to improve
performance and reduce redundant LLM calls.

Closes #123
```

```
fix(safety): handle empty input in content filter

Previously, empty input would cause a crash. Now returns early
with appropriate status code.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass: `make test`
2. Run linter: `make lint`
3. Format code: `make format`
4. Update documentation
5. Add tests for new features
6. Update CHANGELOG.md

### PR Description

Use the provided PR template and fill in:

- Description of changes
- Type of change
- Related issues
- Testing performed
- Security considerations
- Accessibility checklist
- Documentation updates
- Deployment notes

### PR Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code coverage checks
   - Linting and formatting

2. **Code Review**
   - At least one maintainer approval required
   - Address all review comments
   - Keep commits clean (squash if needed)

3. **Approval and Merge**
   - All checks must pass
   - Approval from code owner
   - Merge via squash or rebase

### Getting Reviews

- Tag relevant team members based on code ownership
- See [CODEOWNERS](.github/CODEOWNERS) for ownership details
- Be responsive to review comments

## Documentation

### When to Update Documentation

- New features: Update API documentation
- Breaking changes: Update migration guide
- Configuration changes: Update .env.example
- Architecture changes: Update ARCHITECTURE.md

### Documentation Standards

- Use clear, concise language
- Include examples
- Keep documentation up-to-date
- Use proper formatting (markdown, code blocks)

### API Documentation

- All endpoints must be documented in `docs/API.md`
- Include request/response examples
- Document error codes
- Note any rate limits or restrictions

## Questions or Need Help?

- Open an issue on GitHub
- Start a discussion in the community forum
- Reach out to maintainers

## Recognition

Contributors will be acknowledged in the project documentation and release notes.

Thank you for contributing to Project Chimera!

## Documentation Contributions

For detailed documentation contribution guidelines, see [Documentation Contribution Guide](docs/contributing/documentation.md).

Documentation PRs follow the same review process with additional documentation-specific criteria in the guide.
