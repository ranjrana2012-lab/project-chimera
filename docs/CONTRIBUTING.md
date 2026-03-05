# Contributor Guide

**Project:** Project Chimera
**Version:** 3.0.0
**Last Updated:** March 2026

---

## Welcome

Thank you for your interest in contributing to Project Chimera! This guide will help you get started with contributing to our AI-powered live theatre platform.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

---

## Getting Started

### For Students

If you're a student joining Project Chimera, please start with the [Student Quick Start Guide](getting-started/quick-start.md).

### For External Contributors

1. **Fork and Clone:**

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/main.git Project_Chimera
cd Project_Chimera
git remote add upstream https://github.com/project-chimera/main.git
```

2. **Set Up Development Environment:**

```bash
# Run the bootstrap script
make bootstrap

# This will install k3s, build all services, and deploy them
```

3. **Verify Setup:**

```bash
# Check all services are running
make bootstrap-status

# Run tests
make test
```

---

## Development Workflow

### 1. Choose an Issue

- Look for issues tagged `good-first-issue` for beginners
- Check issues assigned to your component
- Or propose a new feature in a discussion

### 2. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Your Changes

```bash
# Edit files
# ...

# Run tests
make test

# Format code
make format

# Lint
make lint
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat(component): description of your changes"
```

**Commit Message Format:**

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `chore` - Maintenance tasks

**Example:**

```
feat(scenespeak): add LoRA adapter switching

Implements ability to switch between different LoRA adapters
for genre-specific dialogue styling. Switching takes <500ms
and maintains existing conversation context.

Closes #123
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

---

## Coding Standards

### Python

We follow PEP 8 with some modifications:

**Line Length:** 100 characters (soft limit), 120 (hard)

**Imports:** Group in this order:
1. Standard library
2. Third-party imports
3. Local imports

```python
# Good
import asyncio
from dataclasses import dataclass

import pytest
from fastapi import FastAPI

from services.scenespeak import generate_dialogue
```

**Type Hints:** Required for all public functions

```python
# Good
def generate_dialogue(
    context: str,
    sentiment: float = 0.0
) -> dict:
    """Generate dialogue for given context."""
    pass

# Bad
def generate_dialogue(context, sentiment=0.0):
    pass
```

**Docstrings:** Google style for all modules, classes, and public functions

```python
def generate_dialogue(context: str, sentiment: float = 0.0) -> dict:
    """Generate dialogue for the given scene context.

    Args:
        context: Scene description and character information
        sentiment: Sentiment value from -1.0 (negative) to 1.0 (positive)

    Returns:
        Dictionary containing generated dialogue and metadata

    Raises:
        ValueError: If context is empty
        ModelTimeoutError: If generation exceeds timeout

    Example:
        >>> generate_dialogue("A garden at sunset", 0.7)
        {'dialogue': 'ROMEO: What light through yonder window breaks?'}
    """
```

### Code Organization

**Service Structure:**

```
services/<service-name>/
├── src/
│   └── <service-name>/
│       ├── __init__.py
│       ├── main.py           # FastAPI app
│       ├── config.py         # Configuration
│       └── handlers/         # Route handlers
├── tests/
│   ├── test_main.py
│   └── test_handlers.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### Error Handling

```python
# Good: Specific exceptions
try:
    result = await generate_dialogue(context)
except ModelTimeoutError as e:
    logger.error(f"Generation timeout: {e}")
    raise
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return {"error": "invalid_input"}

# Bad: Bare except
try:
    result = await generate_dialogue(context)
except:
    pass
```

### Async/Await

Use `async`/`await` for I/O operations:

```python
# Good
async def process_request(request_data: dict) -> dict:
    result = await external_api_call(request_data)
    return result

# Bad
def process_request(request_data: dict) -> dict:
    result = external_api_call(request_data)  # Blocking!
    return result
```

---

## Testing Requirements

### Test Coverage

All new code must have:
- **Minimum 80% code coverage**
- Tests for all public functions
- Edge case and error condition tests
- Integration tests for service interactions

### Writing Tests

```python
# Good: Descriptive test name
def test_safety_filter_blocks_known_harmful_patterns():
    """Verify safety filter blocks known harmful patterns."""
    filter = SafetyFilter()
    result = filter.check("Here is my password: 'secret123'")
    assert result.action == FilterAction.BLOCK

# Bad: Vague test name
def test_filter():
    pass
```

### Test Organization

```python
# Unit tests
class TestSafetyFilter:
    def test_filter_initialization(self):
        pass

    def test_check_safe_content(self):
        pass

# Integration tests
class TestServiceIntegration:
    @pytest.fixture
    async def services(self):
        # Set up services
        pass

    async def test_end_to_end_flow(self, services):
        pass
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage
pytest tests/unit/ --cov=services --cov-report=html

# Specific test
pytest tests/unit/services/scenespeak/test_generation.py::test_generate_dialogue -v
```

---

## Documentation

### Required Documentation

All contributions must include:

1. **Code Comments** - For complex logic
2. **Docstrings** - For all public functions
3. **Type Hints** - For all function parameters
4. **README Updates** - For new features
5. **API Docs** - For new endpoints

### API Documentation

When adding new API endpoints, update the appropriate file in `docs/api/`:

```markdown
### New Endpoint

**Endpoint:** `POST /v1/new-endpoint`

**Request Body:**
...

**Response:**
...

**Status Codes:**
...
```

### Architecture Updates

For significant architectural changes, create an ADR:

```bash
# Create new ADR
cp docs/architecture/001-use-k3s.md docs/architecture/006-your-decision.md
```

---

## Pull Request Process

### Before Submitting

1. **Run Tests:**
   ```bash
   make test
   ```

2. **Format Code:**
   ```bash
   make format
   ```

3. **Lint:**
   ```bash
   make lint
   ```

4. **Update Documentation:**
   - Update README if needed
   - Add/update API docs
   - Update relevant runbooks

### Creating Your PR

1. **Title:** Use the same format as commit message
   ```
   feat(scenespeak): add LoRA adapter switching
   ```

2. **Description:** Include:
   - What changes were made
   - Why they were made
   - How they were tested
   - Screenshots if applicable
   - Related issue number

3. **Labels:** Add appropriate labels:
   - `component-{service}` for affected service
   - `type-{feature,fix,docs,etc}`
   - `size-{small,medium,large}`

4. **Assignees:** Assign reviewers:
   - Technical Lead for review
   - Domain expert if applicable

### Review Process

1. **Automated Checks:**
   - CI/CD pipeline runs tests
   - Code coverage checked
   - Linting verified
   - Security scan performed

2. **Code Review:**
   - Reviewer provides feedback
   - Address all comments
   - Mark as resolved when done

3. **Approval:**
   - At least one approval required
   - Technical Lead approval for significant changes
   - All automated checks must pass

4. **Merge:**
   - Squash and merge for clean history
   - Delete branch after merge

### Trust-Based Auto-Merge

For trusted contributors with a track record:
- Small fixes may be auto-merged if all checks pass
- Requires prior approval from Technical Lead
- Opt-out available per contributor

---

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Assume good intentions
- Help others learn

### Communication

- **Discord/Slack:** Daily chat and questions
- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Design discussions and questions
- **Email:** For sensitive or private matters

### Getting Help

1. **Search first:** Check existing issues and discussions
2. **Be specific:** Include error messages, steps to reproduce
3. **Provide context:** Share what you've tried
4. **Be patient:** Contributors are volunteers

### Meetings

- **Daily Standup:** 15 minutes, share progress and blockers
- **Weekly Planning:** 1 hour, plan upcoming work
- **Office Hours:** For questions and pair programming

---

## Contribution Areas

### For Students

| Role | Component | Focus |
|------|-----------|-------|
| 1 | OpenClaw | Skill routing, orchestration |
| 2 | SceneSpeak | Dialogue generation, LoRA adapters |
| 3 | Captioning | Speech-to-text, streaming |
| 4 | BSL | Translation, avatar rendering |
| 5 | Sentiment | Emotion analysis, trends |
| 6 | Lighting | DMX/sACN control |
| 7 | Safety | Content moderation, ML models |
| 8 | Console | Dashboard, WebSocket updates |
| 9 | Infrastructure | Kubernetes, CI/CD |
| 10 | QA & Docs | Testing, documentation |

### For External Contributors

High-impact contribution areas:
- Bug fixes
- Performance improvements
- Documentation improvements
- Test coverage
- Accessibility improvements
- Security enhancements

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` - All contributors
- Release notes - For significant contributions
- Project demos - For featured work
- Annual summary - Top contributors

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Questions?

- **Technical Lead:** [Contact info]
- **Documentation:** See `docs/` folder
- **Issues:** Open a GitHub issue
- **Chat:** Join our Discord/Slack

---

*Happy Contributing!*

*Contributor Guide v0.4.0*
*Project Chimera*
