# Development Setup Guide

Set up your local development environment for contributing to Project Chimera.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git
- Make (optional, for using Makefiles)
- Node.js 18+ (for frontend development)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your local configuration
# You may need to set API keys for external services
```

**Common environment variables:**
- `GLM_API_KEY` - For SceneSpeak LLM (if using GLM API)
- `OPENAI_API_KEY` - For Whisper/Captioning (if using OpenAI)
- `LOG_LEVEL` - Logging level (default: INFO)
- `ENVIRONMENT` - development, staging, or production

## Step 3: Start Development Services

```bash
# Start all services
docker compose up -d

# Verify services are healthy
make health-check
# Or manually:
curl http://localhost:8000/health/live
curl http://localhost:8003/health/live
curl http://localhost:8007/health/live
```

## Step 4: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific service tests
pytest tests/services/test_bsl_agent.py

# Run E2E tests
cd tests/e2e
npm install
npm test
```

## Step 5: Code Style

We use:
- **Python**: PEP 8, Black formatter, isort imports
- **JavaScript**: ESLint with AirBnB style

Format your code before committing:

```bash
# Format Python code
black services/
isort services/

# Check JavaScript
cd tests/e2e
npm run lint
```

## Development Workflow

1. Create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests locally:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black services/ && isort services/
   ```

5. Commit with descriptive message:
   ```bash
   git commit -m "feat: add your feature"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a pull request

See [Contributing](../CONTRIBUTING.md) for PR guidelines.

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter (Microsoft)
- isort (ms-python.isort)
- Docker (Microsoft)

**Workspace settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Open project folder
2. Configure Python interpreter to use venv:
   - Settings → Project → Python Interpreter → Add → Existing Environment
   - Select `venv/bin/python`
3. Enable Black:
   - Settings → Tools → External Tools → Black
4. Enable isort:
   - Settings → Tools → External Tools → isort

## Running Individual Services

For development, you can run services individually instead of using Docker Compose:

```bash
# Activate virtual environment
source venv/bin/activate

# Run BSL Agent
cd services/bsl-agent
python main.py

# Run SceneSpeak Agent
cd services/scenespeak-agent
python main.py

# Run Orchestrator
cd services/openclaw-orchestrator
python main.py
```

## Debugging

### Python Services

Use your IDE's debugger or:

```bash
# Run with pdb
python -m pdb services/bsl-agent/main.py

# Run with ipdb (if installed)
python -m ipdb services/bsl-agent/main.py
```

### Frontend

Open browser developer tools:
- Chrome/Edge: F12
- Firefox: Ctrl+Shift+K

Check console for JavaScript errors.

### Docker Logs

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for specific service
docker compose logs -f bsl-agent

# Last 100 lines
docker compose logs --tail=100 bsl-agent
```

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8003

# Kill process
kill -9 <PID>
```

### Virtual Environment Issues

```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Docker Issues

```bash
# Clean Docker cache
docker system prune -a

# Rebuild containers
docker compose up -d --build
```

## Performance Profiling

For Python services:

```bash
# Profile with cProfile
python -m cProfile -o profile.stats services/bsl-agent/main.py

# View profile
python -m pstats profile.stats
```

## Next Steps

- Read [Contributing Guidelines](../CONTRIBUTING.md) for PR workflow
- Check [Testing Guide](testing.md) for test writing
- See [Code Style](../standards/python-style.md) for coding conventions
