# Student Quick Start Guide
## Project Chimera: Development Environment Setup

**Version:** 1.0.0
**Audience:** AI Students joining Project Chimera
**Last Updated:** January 2025

---

## Welcome to Project Chimera

This guide will help you set up your development environment to contribute to Project Chimera, a student-run Dynamic Performance Hub that creates live theatre adapting in real time to audience input. By following this guide, you will have a working local development environment within 30-60 minutes, depending on your internet connection and prior setup.

### What You Will Be Working On

As an AI student contributor, you may work on:

- **OpenClaw Skills:** Python modules that integrate with the orchestrator
- **Microservices:** Containerised services for dialogue generation, captioning, sentiment analysis, etc.
- **Model Pipelines:** Fine-tuning, evaluation, and inference optimisation
- **Infrastructure:** Kubernetes manifests, CI/CD pipelines, monitoring
- **Testing:** Unit tests, integration tests, load tests, safety tests

### Two Development Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Local-Only** | Everything runs on your laptop using Docker | Development, unit testing, skill prototyping |
| **Remote-Connected** | Your laptop connects to DGX Spark services | Integration testing, model access, production-like testing |

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 8 GB | 16 GB+ |
| Disk Space | 20 GB free | 50 GB+ free |
| CPU | 4 cores | 8+ cores |
| OS | Windows 10/11, macOS 12+ | macOS 14+, Windows 11 |

### Required Software

Before starting, ensure you have the following installed:

#### For All Platforms

1. **Git** - Version control
   - Verify: `git --version`
   - Install: https://git-scm.com/downloads

2. **Docker Desktop** - Container runtime
   - Verify: `docker --version` and `docker compose version`
   - Install: https://www.docker.com/products/docker-desktop/
   - **Important:** Ensure Docker Desktop is running before proceeding

3. **Visual Studio Code** (recommended) or your preferred IDE
   - Install: https://code.visualstudio.com/

4. **Python 3.11+** - For local scripts and tools
   - Verify: `python --version` or `python3 --version`
   - Install: https://www.python.org/downloads/

#### Platform-Specific Setup

**Windows:**

```powershell
# Install via winget (recommended)
winget install Microsoft.Git
winget install Docker.DockerDesktop
winget install Microsoft.VisualStudioCode

# Or use Chocolatey
choco install git docker-desktop vscode
```

**macOS:**

```bash
# Install via Homebrew (recommended)
brew install git
brew install --cask docker
brew install --cask visual-studio-code

# Install Python if needed
brew install python@3.11
```

---

## Quick Start: Local-Only Mode

This mode runs a minimal Project Chimera stack on your laptop using Docker. It uses smaller models and mocked services, making it suitable for most development tasks without requiring GPU access.

### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/project-chimera/main.git
cd main

# Or use SSH if you have keys set up
git clone git@github.com:project-chimera/main.git
cd main
```

### Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your details (optional for local mode)
# The defaults work for local development
```

**Environment File Contents:**

```bash
# .env.example - Local Development Configuration

# Mode: local or remote
CHIMERA_MODE=local

# Local model settings (small models for CPU inference)
SCENESPEAK_MODEL=mock
ASR_MODEL=mock
SENTIMENT_MODEL=mock

# Redis (local container)
REDIS_URL=redis://localhost:6379

# Kafka (local container)
KAFKA_BROKERS=localhost:9092

# OpenClaw (local container)
OPENCLAW_URL=http://localhost:8080

# Logging
LOG_LEVEL=DEBUG
```

### Step 3: Start Local Stack

```bash
# Start all services using Docker Compose
docker compose -f docker-compose.local.yml up -d

# This starts:
# - OpenClaw orchestrator (mock mode)
# - Redis for caching
# - Kafka for event streaming
# - Mock model servers
# - Prometheus & Grafana for monitoring
```

**Expected Output:**

```
[+] Running 6/6
 ✔ Network chimera-local      Created
 ✔ Container chimera-redis    Started
 ✔ Container chimera-kafka    Started
 ✔ Container chimera-openclaw Started
 ✔ Container chimera-prometheus Started
 ✔ Container chimera-grafana  Started
```

### Step 4: Verify Installation

```bash
# Check all containers are running
docker compose -f docker-compose.local.yml ps

# Run verification script
./scripts/verify-local-setup.sh
```

**Expected Verification Output:**

```
✓ Docker is running
✓ All containers healthy
✓ Redis connection successful
✓ Kafka connection successful
✓ OpenClaw health check passed
✓ Mock model server responding
✓ Prometheus metrics available
✓ Grafana dashboard accessible at http://localhost:3000

Local setup complete! You can now start developing.
```

### Step 5: Run Tests

```bash
# Run unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=services --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Step 6: Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| OpenClaw API | http://localhost:8080 | Orchestrator API |
| OpenClaw UI | http://localhost:8080/ui | Web interface |
| Grafana | http://localhost:3000 | Monitoring dashboards |
| Prometheus | http://localhost:9090 | Metrics |
| Redis Commander | http://localhost:8081 | Redis GUI |

---

## Remote-Connected Mode

This mode connects your local development environment to the DGX Spark cluster at the university. You can access production-like models, GPU inference, and shared data.

### Prerequisites for Remote Mode

1. **VPN Access:** You must be connected to the university network
2. **SSH Key:** Your SSH key must be registered with the cluster
3. **API Credentials:** Obtain from Technical Lead

### Step 1: Obtain Credentials

Contact the Technical Lead to receive:

- SSH key for cluster access
- API token for OpenClaw remote endpoint
- Kubernetes config file (`kubeconfig`)

Store these securely:

```bash
# Create config directory
mkdir -p ~/.config/chimera

# Save your credentials
# SSH key
chmod 600 ~/.config/chimera/id_rsa

# API token (add to .env)
echo "CHIMERA_API_TOKEN=your-token-here" >> .env
```

### Step 2: Configure Environment for Remote

Create a separate environment file for remote mode:

```bash
# Copy and edit for remote
cp .env.example .env.remote
```

**Remote Environment Configuration:**

```bash
# .env.remote - Remote Development Configuration

# Mode: local or remote
CHIMERA_MODE=remote

# Remote endpoints (replace with actual addresses)
OPENCLAW_URL=https://chimera-api.university.ac.uk
KAFKA_BROKERS=chimera-kafka.university.ac.uk:9092
REDIS_URL=redis://chimera-redis.university.ac.uk:6379

# Authentication
CHIMERA_API_TOKEN=${CHIMERA_API_TOKEN}

# Use remote models
SCENESPEAK_MODEL=remote:7b-quantised
ASR_MODEL=remote:whisper-small
SENTIMENT_MODEL=remote:distilbert

# Logging
LOG_LEVEL=INFO
```

### Step 3: Connect to Cluster

```bash
# Test SSH connection
ssh chimera-user@chimera-cluster.university.ac.uk

# If successful, you'll see:
# Welcome to Project Chimera DGX Spark Cluster
# Last login: [date]

# Exit and continue local setup
exit
```

### Step 4: Start Remote-Connected Stack

```bash
# Start local services that connect to remote
docker compose -f docker-compose.remote.yml up -d

# This starts only local tools (IDE helper, debugging tools)
# All heavy services run on DGX Spark
```

### Step 5: Verify Remote Connection

```bash
# Run verification for remote mode
./scripts/verify-remote-setup.sh
```

**Expected Output:**

```
✓ VPN connection verified
✓ SSH access to cluster confirmed
✓ OpenClaw API reachable
✓ API token valid
✓ Kafka broker accessible
✓ Redis accessible

Remote connection established!
You can now develop against DGX Spark services.
```

---

## Development Workflow

### Project Structure

```
project-chimera/
├── services/                # Microservice implementations
│   ├── scenespeak/         # Dialogue generation
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── captioning/         # ASR and captions
│   ├── safety-filter/      # Content moderation
│   └── ...
├── skills/                  # OpenClaw skill definitions
│   ├── scenespeak-skill/
│   ├── captioning-skill/
│   └── ...
├── models/                  # Prompts, adapters, evaluation
│   ├── prompts/
│   ├── lora-adapters/
│   └── evaluation/
├── infrastructure/          # Kubernetes configs
│   └── kubernetes/
├── tests/                   # Test suites
│   ├── unit/
│   ├── integration/
│   └── load/
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
└── docker-compose*.yml      # Docker configurations
```

### Creating a New Skill

1. **Copy the skill template:**

```bash
./scripts/create-skill.sh my-new-skill
```

2. **Edit the skill definition:**

```yaml
# skills/my-new-skill/skill.yaml
apiVersion: openclaw.io/v1
kind: Skill
metadata:
  name: my-new-skill
  version: 0.1.0
spec:
  description: "Description of what this skill does"
  
  inputs:
    - name: input_param
      type: string
      required: true
      description: "Input description"
  
  outputs:
    - name: output_param
      type: string
      description: "Output description"
  
  config:
    timeout: 5000ms
```

3. **Implement the skill handler:**

```python
# skills/my-new-skill/handler.py

from openclaw import SkillHandler

def handle(inputs: dict) -> dict:
    """
    Skill implementation.
    
    Args:
        inputs: Dictionary of input parameters
        
    Returns:
        Dictionary of output parameters
    """
    input_param = inputs.get("input_param", "")
    
    # Your implementation here
    output = process(input_param)
    
    return {
        "output_param": output
    }

# Register with OpenClaw
skill = SkillHandler(handle)
```

4. **Write tests:**

```python
# skills/my-new-skill/tests/test_handler.py

import pytest
from handler import handle

def test_basic_functionality():
    result = handle({"input_param": "test"})
    assert "output_param" in result
    assert result["output_param"] is not None

def test_empty_input():
    result = handle({})
    # Should handle gracefully
    assert result is not None
```

5. **Test locally:**

```bash
# Run skill tests
pytest skills/my-new-skill/tests/

# Test with Docker
docker build -t chimera/my-new-skill skills/my-new-skill/
docker run --rm chimera/my-new-skill test
```

### Making Changes to Services

1. **Create a feature branch:**

```bash
git checkout -b feature/my-feature-name
```

2. **Make your changes:**

```bash
# Edit files in services/
# Or skills/
# Or models/
```

3. **Run tests:**

```bash
# Run all tests (fast)
pytest tests/unit/

# Run integration tests (slower)
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_safety_filter.py -v
```

4. **Format and lint:**

```bash
# Format code
black services/ skills/
isort services/ skills/

# Lint
ruff check services/ skills/

# Type check
mypy services/
```

5. **Commit and push:**

```bash
git add .
git commit -m "feat: description of your changes"
git push origin feature/my-feature-name
```

6. **Create pull request:**

- Go to GitHub and create a PR
- Fill in the PR template
- Wait for CI to pass
- Request review from Technical Lead

---

## Using Dev Containers (Recommended)

For the most consistent development experience, use VS Code Dev Containers. This ensures all contributors have identical environments.

### Setup Dev Containers

1. **Install VS Code extensions:**

```bash
# In VS Code, install:
# - Dev Containers (ms-vscode-remote.remote-containers)
# - Python (ms-python.python)
# - Docker (ms-azuretools.vscode-docker)
```

2. **Open project in container:**

```bash
# Open VS Code
code .

# When prompted, click "Reopen in Container"
# Or use Command Palette: "Dev Containers: Reopen in Container"
```

3. **Wait for container to build:**

The first build takes 5-10 minutes. Subsequent starts are much faster.

### Dev Container Configuration

The project includes a pre-configured dev container:

```json
// .devcontainer/devcontainer.json
{
  "name": "Project Chimera Dev",
  "dockerComposeFile": ["docker-compose.devcontainer.yml"],
  "service": "devcontainer",
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.formatting.provider": "black",
        "editor.formatOnSave": true
      }
    }
  },
  "forwardPorts": [8080, 3000, 9090],
  "postCreateCommand": "pip install -r requirements-dev.txt"
}
```

---

## Claude Code Integration

Claude Code is an AI-assisted coding tool that can help with development tasks. Here is how to connect it to your Project Chimera workflow.

### Installing Claude Code

**macOS:**

```bash
# Install via Homebrew
brew install claude-code

# Or download directly
curl -fsSL https://claude.ai/code/install.sh | sh
```

**Windows:**

```powershell
# Download installer from https://claude.ai/code
# Or use winget
winget install Anthropic.ClaudeCode
```

### Configuration for Project Chimera

Create a `.claude/config.json` in the project root:

```json
{
  "project": "project-chimera",
  "context": {
    "description": "Student-run Dynamic Performance Hub using OpenClaw on DGX Spark",
    "techStack": ["Python", "Docker", "Kubernetes", "OpenClaw", "PyTorch"],
    "conventions": {
      "testing": "pytest",
      "formatting": "black",
      "linting": "ruff",
      "documentation": "docstrings with Google style"
    }
  },
  "rules": [
    "Always run tests before suggesting code changes",
    "Follow existing code patterns in the codebase",
    "Prefer type hints in function signatures",
    "Include docstrings for public functions"
  ]
}
```

### Using Claude Code Effectively

```bash
# Start Claude Code in project directory
cd project-chimera
claude-code

# Example commands:
# "Help me understand the SceneSpeak agent architecture"
# "Write a unit test for the safety filter"
# "Explain how OpenClaw routing works"
# "Refactor this function to be more efficient"
```

### Connecting to OpenClaw

Claude Code can help you understand and work with OpenClaw:

```bash
# Ask Claude Code to explain OpenClaw concepts
"Explain OpenClaw's policy engine and how to define a new policy"

# Generate skill templates
"Create a new OpenClaw skill for [specific task]"

# Debug issues
"Why might this OpenClaw skill be failing?"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Docker Issues

**Problem: Docker Desktop not starting**

```
Error: Cannot connect to Docker daemon
```

*Solution:*
- Ensure Docker Desktop is running (check system tray/menu bar)
- Restart Docker Desktop
- On Windows, ensure WSL2 is enabled:
  ```powershell
  wsl --install
  ```

**Problem: Port already in use**

```
Error: port is already allocated
```

*Solution:*
```bash
# Find what's using the port
# macOS/Linux
lsof -i :8080

# Windows
netstat -ano | findstr :8080

# Kill the process or change the port in docker-compose.yml
```

**Problem: Out of disk space**

```
Error: no space left on device
```

*Solution:*
```bash
# Clean up Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

#### Python Issues

**Problem: Module not found**

```
ModuleNotFoundError: No module named 'xxx'
```

*Solution:*
```bash
# Ensure you're using the virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements-dev.txt
```

**Problem: Python version mismatch**

```
Error: Python 3.11+ required
```

*Solution:*
```bash
# Check version
python --version

# If outdated, install Python 3.11+
# Use pyenv (macOS/Linux) or download (Windows)
```

#### Connection Issues

**Problem: Cannot connect to OpenClaw**

```
Error: Connection refused to localhost:8080
```

*Solution:*
```bash
# Check if container is running
docker compose -f docker-compose.local.yml ps

# Restart the container
docker compose -f docker-compose.local.yml restart openclaw

# Check logs
docker compose -f docker-compose.local.yml logs openclaw
```

**Problem: Remote connection timeout**

```
Error: Connection timed out
```

*Solution:*
- Verify VPN is connected
- Check if your IP is whitelisted (contact Technical Lead)
- Verify credentials are correct
- Try SSH connection first to verify network access

#### Performance Issues

**Problem: Tests running slowly**

*Solution:*
```bash
# Run only affected tests
pytest tests/unit/test_specific_file.py

# Run tests in parallel
pytest -n auto tests/unit/

# Skip slow tests
pytest -m "not slow" tests/
```

**Problem: Docker container using too much memory**

*Solution:*
```bash
# Check container resource usage
docker stats

# Limit memory in docker-compose
# Add to service definition:
deploy:
  resources:
    limits:
      memory: 2G
```

### Verification Checklist

If something isn't working, run through this checklist:

```bash
# 1. Docker is running
docker info

# 2. All containers are healthy
docker compose -f docker-compose.local.yml ps

# 3. Environment variables are set
env | grep CHIMERA

# 4. Python environment is active
which python
pip list

# 5. Tests pass
pytest tests/unit/ -q

# 6. Can connect to OpenClaw
curl http://localhost:8080/health

# 7. Can connect to Redis
redis-cli ping

# 8. Can connect to Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Getting Help

If you're stuck:

1. **Check the documentation:**
   - This guide
   - `/docs/` folder in the repository
   - Code comments and docstrings

2. **Search existing issues:**
   - GitHub Issues: https://github.com/project-chimera/main/issues

3. **Ask in the team chat:**
   - Slack: #project-chimera-dev
   - Tag: @technical-lead for urgent issues

4. **Create a new issue:**
   - Use the issue template
   - Include: error messages, steps to reproduce, environment details

---

## Development Best Practices

### Code Style

```python
# Good: Well-documented function with type hints
def generate_dialogue(
    scene_context: dict,
    sentiment: float,
    max_tokens: int = 256
) -> dict:
    """
    Generate dialogue for the current scene.
    
    Args:
        scene_context: Dictionary containing scene state and history
        sentiment: Current sentiment value (-1.0 to 1.0)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary with 'lines' and 'metadata' keys
        
    Raises:
        ModelTimeoutError: If generation exceeds timeout
    """
    # Implementation
    pass
```

### Commit Messages

Follow conventional commit format:

```
feat: add BSL translation caching

Implements a caching layer for BSL translations to reduce
latency for repeated phrases. Cache uses Redis with 5-minute TTL.

Closes #123
```

### Testing

- Write tests for all new functionality
- Aim for >80% coverage on new code
- Use descriptive test names
- Test edge cases and error conditions

```python
# Good: Descriptive test name, tests edge case
def test_safety_filter_handles_unicode_profanity():
    """Verify safety filter correctly blocks profanity in unicode."""
    result = safety_filter.filter("Unicode profanity: \uXXXX")
    assert result.decision == "blocked"
```

### Documentation

- Update README.md when adding new features
- Add docstrings to all public functions
- Update architecture docs for significant changes
- Include examples in documentation

---

## Next Steps

After completing this setup:

1. **Read the Architecture Overview:**
   - `/docs/architecture/overview.md`
   - Understanding the system helps you contribute effectively

2. **Pick a Starter Task:**
   - Look for "good first issue" labels in GitHub
   - These are specifically chosen for new contributors

3. **Join Team Meetings:**
   - Daily standup: [time]
   - Weekly planning: [time]
   - Ask for calendar invite

4. **Introduce Yourself:**
   - Post in #project-chimera-introductions
   - Share your interests and what you want to work on

5. **Ask Questions:**
   - No question is too basic
   - We all started somewhere
   - Asking questions helps improve documentation

---

## Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Start local stack | `docker compose -f docker-compose.local.yml up -d` |
| Stop local stack | `docker compose -f docker-compose.local.yml down` |
| View logs | `docker compose -f docker-compose.local.yml logs -f` |
| Run tests | `pytest tests/unit/` |
| Format code | `black . && isort .` |
| Lint | `ruff check .` |
| Build container | `docker build -t chimera/service-name services/service-name/` |

### Important URLs

| Service | Local URL | Remote URL |
|---------|-----------|------------|
| OpenClaw API | http://localhost:8080 | https://chimera-api.university.ac.uk |
| Grafana | http://localhost:3000 | https://chimera-grafana.university.ac.uk |
| Prometheus | http://localhost:9090 | https://chimera-prometheus.university.ac.uk |

### Useful Files

| File | Purpose |
|------|---------|
| `.env.example` | Environment template |
| `docker-compose.local.yml` | Local stack definition |
| `docker-compose.remote.yml` | Remote connection stack |
| `requirements-dev.txt` | Python dependencies |
| `pyproject.toml` | Project configuration |
| `scripts/verify-local-setup.sh` | Installation verification |

---

*Welcome to Project Chimera! We're excited to have you on the team.*

*Questions? Reach out in Slack or contact the Technical Lead directly.*
