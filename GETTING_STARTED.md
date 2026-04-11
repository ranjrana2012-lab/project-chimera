# Getting Started with Project Chimera

## 5-Minute Quick Start

Get Project Chimera up and running in under 5 minutes with Docker Compose.

### Prerequisites

**Required:**
- Docker Engine 20.10+ and Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Linux, macOS, or Windows with WSL2

**Optional (for LLM features):**
- GLM API key from Z.ai (https://open.bigmodel.cn/)
- Local LLM setup (Nemotron 3 Super 120B)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# 2. Configure environment variables (optional)
cp .env.example .env
# Edit .env and add your GLM_API_KEY if using LLM features

# 3. Start all services
docker-compose -f docker-compose.mvp.yml up -d

# 4. Verify services are running
curl http://localhost:8000/health  # OpenClaw Orchestrator
curl http://localhost:8001/health  # SceneSpeak Agent
curl http://localhost:8004/health  # Sentiment Agent
curl http://localhost:8007/health  # Operator Console

# 5. Access the Operator Console
open http://localhost:8007  # macOS
xdg-open http://localhost:8007  # Linux
start http://localhost:8007  # Windows
```

**That's it!** Project Chimera is now running.

## Service Endpoints

Once running, these services are available:

| Service | URL | Purpose |
|---------|-----|---------|
| OpenClaw Orchestrator | http://localhost:8000 | Core coordination |
| SceneSpeak Agent | http://localhost:8001 | Dialogue generation |
| Sentiment Agent | http://localhost:8004 | Sentiment analysis |
| Safety Filter | http://localhost:8005 | Content moderation |
| Translation Agent | http://localhost:8006 | Translation |
| Operator Console | http://localhost:8007 | Control UI |
| Hardware Bridge | http://localhost:8008 | DMX simulation |
| Redis | localhost:6379 | State management |

## Verification

### Check Service Health
```bash
# Check all services at once
for port in 8000 8001 8004 8005 8006 8007 8008; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health | jq '.status' 2>/dev/null || echo "Service not responding"
done
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.mvp.yml logs -f

# Specific service
docker-compose -f docker-compose.mvp.yml logs -f openclaw-orchestrator
docker-compose -f docker-compose.mvp.yml logs -f scenespeak-agent
```

### Run Health Check
```bash
docker-compose -f docker-compose.mvp.yml ps
```

## First API Call

Test the orchestrator with a simple request:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a short scene about a sunrise",
    "max_length": 100
  }'
```

## Environment Configuration

### Minimum Setup (No LLM)
For testing without LLM features:

```bash
# Create .env file
cat > .env << EOF
# Service Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://redis:6379

# LLM Configuration (Optional - will use mock if not provided)
GLM_API_KEY=
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v/
EOF
```

### Full Setup (With LLM)
For complete LLM functionality:

```bash
# Create .env file with API keys
cat > .env << EOF
# Service Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://redis:6379

# GLM API (Primary LLM)
GLM_API_KEY=your_glm_api_key_here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4/

# Local LLM Fallback
LOCAL_LLM_ENABLED=true
LOCAL_LLM_URL=http://host.docker.internal:8012
LOCAL_LLM_MODEL=nemotron-3-super-120b-a12b-nvfp4
EOF
```

## Local Development Setup

For development without Docker:

```bash
# 1. Install Python 3.10+
python --version

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Start Redis (using Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 6. Run services individually
python services/openclaw-orchestrator/main.py
python services/scenespeak-agent/main.py
python services/sentiment-agent/main.py
```

## Testing Installation

Verify your installation works correctly:

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests (requires all services running)
pytest tests/e2e/ -v

# Check coverage
pytest tests/ --cov=services --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Change port in docker-compose.mvp.yml
ports:
  - "8001:8000"  # Use different external port
```

### Out of Memory
```bash
# Check Docker resources
docker system df

# Clean up unused resources
docker system prune -a

# Increase Docker memory limit (Docker Desktop settings)
# Recommended: 8GB minimum, 16GB for LLM features
```

### Services Not Starting
```bash
# Check service logs
docker-compose -f docker-compose.mvp.yml logs [service-name]

# Restart services
docker-compose -f docker-compose.mvp.yml restart

# Rebuild containers
docker-compose -f docker-compose.mvp.yml build --no-cache
docker-compose -f docker-compose.mvp.yml up -d
```

### LLM API Errors
```bash
# Verify API key is set
docker-compose -f docker-compose.mvp.yml exec openclaw-orchestrator env | grep GLM

# Test API key
curl https://open.bigmodel.cn/api/paas/v4/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Use mock mode for testing
# Set TRANSLATION_AGENT_USE_MOCK=true in .env
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Or run with appropriate permissions
docker-compose -f docker-compose.mvp.yml --user $(id -u):$(id -g) up -d
```

## Next Steps

### Learn the Architecture
- Read [MVP_OVERVIEW.md](MVP_OVERVIEW.md) for architecture details
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
- Review [TESTING.md](TESTING.md) for testing procedures

### Explore the Features
- Try the Operator Console at http://localhost:8007
- Test sentiment analysis via API
- Generate dialogue with SceneSpeak Agent
- Monitor service health

### Development
- Set up your development environment
- Read the development guide
- Contribute to the project

## Common Use Cases

### Test Sentiment Analysis
```bash
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The audience loved the performance!"}'
```

### Generate Dialogue
```bash
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A hero enters the scene", "max_tokens": 50}'
```

### Check System Health
```bash
curl http://localhost:8012/health | jq '.'
```

## Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.mvp.yml down

# Stop and remove volumes
docker-compose -f docker-compose.mvp.yml down -v

# Stop and remove everything including images
docker-compose -f docker-compose.mvp.yml down -v --rmi all
```

## Getting Help

- **Documentation**: See [docs/](docs/) for detailed guides
- **Issues**: Report bugs at GitHub Issues
- **Community**: Join our Discord (coming soon)
- **Email**: support@projectchimera.org

## What's Next?

Now that Project Chimera is running:

1. **Explore the Operator Console** - Access the UI at http://localhost:8007
2. **Run the Tests** - Verify everything works: `pytest tests/`
3. **Read the API Docs** - Learn about all available endpoints
4. **Customize Configuration** - Modify `.env` for your needs
5. **Deploy to Production** - Follow [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Welcome to Project Chimera!** 🎭

For more information, visit:
- [MVP Overview](MVP_OVERVIEW.md)
- [Testing Guide](TESTING.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Main README](README.md)
