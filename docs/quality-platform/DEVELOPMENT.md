# Quality Platform - Development Guide

## Setting Up Development Environment

```bash
cd platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=platform --cov-report=html

# Integration tests
pytest tests/integration/ -v

# All tests
pytest -v
```

## Code Style

- Use type hints for all functions
- Follow PEP 8
- Write docstrings for all classes and public methods
- Use descriptive variable names

## Testing Guidelines

### Unit Tests

- Test individual functions and classes
- Mock external dependencies
- Test edge cases and error conditions
- Aim for >95% code coverage

### Integration Tests

- Test service interactions
- Use test fixtures for common setup
- Test database operations
- Test API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-change

# 2. Make changes
# Edit files in platform/

# 3. Run tests
pytest tests/unit/ -v

# 4. Format code
make format

# 5. Commit
git add .
git commit -m "feat: describe your changes"

# 6. Push and create PR
git push origin feature/your-change
```

## Useful Commands

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Coverage report | `pytest tests/ --cov=platform --cov-report=html` |
| Format code | `make format` or `black platform/` |
| Lint code | `ruff check platform/` |
| Type check | `mypy platform/` |

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the platform directory
cd platform

# Install dependencies
pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Check database is running
kubectl get pods -n quality

# Port forward database
kubectl port-forward -n quality svc/postgres 5432:5432
```

**Redis connection errors:**
```bash
# Check Redis is running
kubectl get pods -n quality

# Port forward Redis
kubectl port-forward -n quality svc/redis 6379:6379
```
