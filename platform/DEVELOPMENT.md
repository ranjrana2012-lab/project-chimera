# Development Guide

## Setup

```bash
# Clone repository
git clone <repository-url>
cd Project_Chimera/platform

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=platform --cov-report=html

# Run specific test file
pytest tests/unit/test_discovery.py -v

# Run integration tests (requires services)
pytest tests/integration/ -v
```

## Code Style

- Use type hints for all functions
- Follow PEP 8 for Python code
- Write docstrings for all classes and public methods
- Keep functions focused and small (< 50 lines)

## Adding New Tests

1. Write test in appropriate `tests/` subdirectory
2. Run test to verify it fails (TDD)
3. Implement code to make test pass
4. Run all tests to ensure no regressions
5. Commit with descriptive message

## Project Structure

```
platform/
├── orchestrator/      # Test orchestration service
│   ├── discovery.py   # Test discovery
│   ├── scheduler.py   # Test scheduling
│   ├── executor.py    # Parallel execution
│   ├── models.py      # Orchestrator models
│   └── main.py        # FastAPI app
├── dashboard/         # Dashboard service
│   ├── routes.py      # REST API
│   ├── graphql.py     # GraphQL schema
│   ├── frontend/      # React UI
│   └── main.py        # FastAPI app
├── ci_gateway/        # CI/CD webhook handler
│   ├── github.py      # GitHub integration
│   └── main.py        # FastAPI app
├── shared/            # Shared utilities
│   ├── config.py      # Configuration
│   ├── database.py    # Database connection
│   └── models.py      # ORM models
├── testengines/       # Advanced test engines
│   ├── mutmut.py      # Mutation testing
│   └── locust.py      # Performance testing
└── tests/             # Test suite
    ├── unit/          # Unit tests
    ├── integration/   # Integration tests
    └── e2e/           # End-to-end tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request
