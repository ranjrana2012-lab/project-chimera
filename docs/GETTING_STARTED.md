# Project Chimera - Getting Started Guide

> **Setup Time**: 5 minutes | **Difficulty**: Beginner | **Prerequisites**: Docker

---

## Quick Start (5 Minutes)

### 1. Clone and Start

```bash
# Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Start all services with Docker Compose
docker-compose -f docker-compose.mvp.yml up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.mvp.yml ps
```

### 2. Verify Deployment

```bash
# Check all services are healthy
curl http://localhost:8000/health  # OpenClaw Orchestrator
curl http://localhost:8001/health  # SceneSpeak Agent
curl http://localhost:8004/health  # Sentiment Agent
curl http://localhost:8005/health  # Safety Filter
curl http://localhost:8006/health  # Translation Agent
curl http://localhost:8007/health  # Operator Console
curl http://localhost:8008/health  # Hardware Bridge
```

**Expected Response:** `{"status": "healthy"}`

### 3. Access the UI

```bash
# Open Operator Console in browser
open http://localhost:8007  # macOS
xdg-open http://localhost:8007  # Linux
start http://localhost:8007  # Windows
```

### 4. Test the System

```bash
# Test sentiment analysis
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The audience loved the performance!"}'

# Test dialogue generation
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A hero enters the scene", "max_tokens": 50}'
```

---

## Prerequisites

### Required

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for cloning the repository
- **8GB RAM** minimum (16GB recommended)
- **20GB free disk space**

### Optional (Development)

- **Python** 3.10+
- **pip** for Python packages
- **virtualenv** for isolation

### Platform-Specific

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker

# Verify installation
docker --version
docker-compose --version
```

**Linux (Ubuntu/Debian):**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
- Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Enable WSL 2 backend
- Restart terminal

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration (required for dialogue generation)
LLM_API_KEY=your_glm47_api_key_here

# Optional Configuration
LLM_MODEL=glm-4.7
LLM_FALLBACK=nemotron
ORCHESTRATOR_PORT=8000
SENTIMENT_PORT=8004
SAFETY_PORT=8005
TRANSLATION_PORT=8006
CONSOLE_PORT=8007
HARDWARE_PORT=8008
```

### Obtaining an LLM API Key

**Z.ai (GLM-4.7):**
1. Visit [Z.ai](https://z.ai)
2. Sign up for an account
3. Navigate to API Keys
4. Create a new key
5. Add to `.env` file

**Note:** The system includes a local fallback (Nemotron 3 Super 120B) if no API key is provided, but responses will be slower.

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Start Services

```bash
# Option A: Docker Compose (recommended)
docker-compose -f docker-compose.mvp.yml up -d

# Option B: Manual start (development)
python -m services.openclaw_orchestrator.main &
python -m services.scenespeak_agent.main &
python -m services.sentiment_agent.main &
python -m services.safety_filter.main &
python -m services.translation_agent.main &
python -m services.operator_console.main &
python -m services.hardware_bridge.main &
```

### 5. Verify Installation

```bash
# Run health checks
python scripts/check_health.py

# Run integration tests
pytest tests/integration/mvp/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html
```

---

## Common Issues

### Docker Issues

**Problem:** `Cannot connect to Docker daemon`
```bash
# Solution: Start Docker Desktop
# macOS/Windows: Open Docker Desktop application
# Linux: sudo systemctl start docker
```

**Problem:** Port already in use
```bash
# Solution: Find and kill process using port
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Or change port in .env file
ORCHESTRATOR_PORT=8001
```

**Problem:** Out of memory
```bash
# Solution: Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory -> 16GB
```

### Python Issues

**Problem:** `ModuleNotFoundError`
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or reinstall virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem:** Python version mismatch
```bash
# Solution: Use correct Python version
python3 --version  # Should be 3.10+
```

### Service Issues

**Problem:** Service not starting
```bash
# Solution: Check logs
docker-compose -f docker-compose.mvp.yml logs <service-name>

# Example:
docker-compose -f docker-compose.mvp.yml logs orchestrator
```

**Problem:** LLM API timeout
```bash
# Solution: Check API key and network
curl -I https://api.z.ai

# Verify API key in .env
cat .env | grep LLM_API_KEY
```

**Problem:** Redis connection refused
```bash
# Solution: Restart Redis
docker-compose -f docker-compose.mvp.yml restart redis

# Or verify Redis is running
docker ps | grep redis
```

---

## Testing Your Setup

### Health Check Script

```bash
# Run comprehensive health check
python scripts/check_health.py
```

Expected output:
```
✓ OpenClaw Orchestrator (8000): healthy
✓ SceneSpeak Agent (8001): healthy
✓ Sentiment Agent (8004): healthy
✓ Safety Filter (8005): healthy
✓ Translation Agent (8006): healthy
✓ Operator Console (8007): healthy
✓ Hardware Bridge (8008): healthy
✓ Redis (6379): healthy
All systems operational!
```

### Manual Test

```bash
# Test end-to-end flow
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The audience is excited!",
    "generate_dialogue": true,
    "max_tokens": 50
  }'
```

Expected response:
```json
{
  "sentiment": {
    "label": "positive",
    "score": 0.85
  },
  "safety": {
    "safe": true,
    "categories": {}
  },
  "dialogue": "The hero steps forward, greeting the cheering crowd with a warm smile...",
  "translation": null
}
```

---

## Stopping the System

### Stop All Services

```bash
# Stop Docker Compose
docker-compose -f docker-compose.mvp.yml down

# Stop and remove volumes
docker-compose -f docker-compose.mvp.yml down -v
```

### Stop Individual Services

```bash
# Stop specific service
docker-compose -f docker-compose.mvp.yml stop orchestrator

# Start specific service
docker-compose -f docker-compose.mvp.yml start orchestrator
```

---

## Next Steps

### Learn More

- **[MVP_OVERVIEW.md](MVP_OVERVIEW.md)** - Complete architecture documentation
- **[TESTING.md](TESTING.md)** - Testing guide
- **[docs/api/README.md](docs/api/README.md)** - API reference

### Explore Features

- Try the [Operator Console](http://localhost:8007)
- Test [API endpoints](docs/api/README.md)
- Run [integration tests](TESTING.md)

### Contribute

- Read [CONTRIBUTING.md](CONTRIBUTING.md)
- Check [GitHub Issues](https://github.com/ranjrana2012-lab/project-chimera/issues)
- Join [Discussions](https://github.com/ranjrana2012-lab/project-chimera/discussions)

---

## Performance Tips

### Faster Startup

```bash
# Use Docker build cache
export DOCKER_BUILDKIT=1
docker-compose -f docker-compose.mvp.yml build

# Parallel build
docker-compose -f docker-compose.mvp.yml build --parallel
```

### Reduce Memory Usage

```bash
# Limit container resources
# Add to docker-compose.mvp.yml:
services:
  orchestrator:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Improve Response Times

```bash
# Use local LLM fallback
# In .env:
LLM_FALLBACK=nemotron
LLM_FORCE_LOCAL=true
```

---

## Troubleshooting Commands

```bash
# Check container status
docker-compose -f docker-compose.mvp.yml ps

# View service logs
docker-compose -f docker-compose.mvp.yml logs -f

# Restart all services
docker-compose -f docker-compose.mvp.yml restart

# Rebuild from source
docker-compose -f docker-compose.mvp.yml up -d --build

# Clean and restart
docker-compose -f docker-compose.mvp.yml down -v
docker-compose -f docker-compose.mvp.yml up -d
```

---

## Support

### Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ranjrana2012-lab/project-chimera/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ranjrana2012-lab/project-chimera/discussions)

### Reporting Bugs

When reporting issues, include:
1. OS and Docker version
2. Error messages
3. Steps to reproduce
4. Logs (`docker-compose logs`)

---

**Project Chimera v1.0.0** - Ready in 5 Minutes ✅

*Creating the future of interactive live theatre*
