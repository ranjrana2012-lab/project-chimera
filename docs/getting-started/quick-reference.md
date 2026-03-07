# Project Chimera Quick Reference

**Version:** 1.0.0
**Last Updated:** March 2026
**Purpose:** Essential commands and information for Project Chimera development

---

## Essential Commands

### Start All Services

```bash
# Start all services in detached mode
docker-compose up -d

# Start specific service
docker-compose up -d [service-name]

# Start with logs
docker-compose up

# Force rebuild before starting
docker-compose up -d --build
```

### Check Service Health

```bash
# Check all services status
docker-compose ps

# Check specific service health
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # SceneSpeak
curl http://localhost:8002/health  # Captioning
curl http://localhost:8003/health  # BSL
curl http://localhost:8004/health  # Sentiment
curl http://localhost:8005/health  # Lighting
curl http://localhost:8006/health  # Safety
curl http://localhost:8007/health  # Console
curl http://localhost:8011/health  # Music Generation

# Watch health status
watch -n 2 'docker-compose ps'
```

### View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f [service-name]

# View last 100 lines
docker-compose logs --tail=100 [service-name]

# View logs since specific time
docker-compose logs --since 1h [service-name]

# Follow multiple services
docker-compose logs -f service1 service2
```

### Stop Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop [service-name]

# Stop and remove containers
docker-compose down

# Stop and remove containers, volumes, and networks
docker-compose down -v
```

---

## Common Tasks

### Add a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/[feature-name]

# 2. Make your changes
# Edit files...

# 3. Run tests
pytest services/[service-name]/tests/

# 4. Run linting
pylint services/[service-name]/

# 5. Commit changes
git add .
git commit -m "feat: description of changes"

# 6. Push to remote
git push origin feature/[feature-name]

# 7. Create pull request on GitHub
gh pr create --title "Feature: [name]" --body "Description of changes"
```

### Debug a Service

```bash
# 1. Check logs
docker-compose logs -f [service-name]

# 2. Enter container
docker-compose exec [service-name] bash

# 3. Check health
curl http://localhost:[port]/health

# 4. Check environment variables
docker-compose exec [service-name] env

# 5. Run tests inside container
docker-compose exec [service-name] pytest

# 6. Restart service
docker-compose restart [service-name]
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific service tests
pytest services/[service-name]/tests/

# Run with coverage
pytest --cov=services/[service-name] --cov-report=html

# Run specific test
pytest tests/test_specific.py::test_function

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Build Services

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build [service-name]

# Build without cache
docker-compose build --no-cache [service-name]

# Build and push
docker-compose build [service-name] && docker push [image-name]
```

### Update Dependencies

```bash
# Update Python dependencies
pip-compile requirements.in

# Update specific package
pip install --upgrade package-name
pip freeze > requirements.txt

# Update system packages
apt-get update && apt-get upgrade
```

---

## Port Reference

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| Orchestrator | 8000 | Central coordinator | `/health` |
| SceneSpeak | 8001 | Dialogue generation | `/health` |
| Captioning | 8002 | Speech-to-text | `/health` |
| BSL | 8003 | Sign language gloss | `/health` |
| Sentiment | 8004 | Sentiment analysis | `/health` |
| Lighting | 8005 | Stage automation | `/health` |
| Safety | 8006 | Content moderation | `/health` |
| Console | 8007 | Operator dashboard | `/health` |
| Quality Dashboard | 8009 | Quality metrics | `/health` |
| CI/CD Gateway | 8010 | CI/CD integration | `/health` |
| Test Orchestrator | 8011 | Test automation | `/health` |
| Music Generation | 8011 | AI music generation | `/health` |
| Quality Gate | 8013 | SLO enforcement | `/health` |
| Prometheus | 9090 | Metrics collection | `/-/healthy` |
| AlertManager | 9093 | Alert routing | `/-/healthy` |
| Grafana | 3000 | Visualization | `/api/health` |
| Jaeger | 16686 | Distributed tracing | `/` |

---

## Environment Variables

### Common Environment Variables

```bash
# Service Configuration
PORT=8000                    # Service port
HOST=0.0.0.0                 # Bind address
WORKERS=4                    # Number of worker processes
LOG_LEVEL=INFO              # Logging level

# Database/Cache
REDIS_URL=redis://redis:6379
KAFKA_BROKERS=kafka:9092
DATABASE_URL=postgresql://user:pass@host:5432/db

# Model Configuration
MODEL_NAME=gpt-4
DEVICE=cuda                  # or cpu
BATCH_SIZE=32
MAX_TOKENS=2048

# Monitoring
ENABLE_TRACING=true
JAEGER_HOST=jaeger
JAEGER_PORT=6831
```

### Creating .env File

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env

# Verify file exists
cat .env

# Set permissions
chmod 600 .env
```

---

## Git Workflow

### Branch Naming

```bash
feature/[feature-name]    # New features
fix/[bug-name]           # Bug fixes
hotfix/[issue-name]      # Critical fixes
refactor/[component]     # Code refactoring
docs/[documentation]     # Documentation updates
test/[test-name]         # Test updates
```

### Commit Message Format

```bash
# Format: <type>: <description>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation changes
style:    Code style changes (formatting)
refactor: Code refactoring
test:     Test changes
chore:    Build process or auxiliary tool changes

# Examples
git commit -m "feat: add sentiment analysis endpoint"
git commit -m "fix: resolve race condition in state machine"
git commit -m "docs: update API documentation"
```

### Common Git Commands

```bash
# Check status
git status

# View changes
git diff

# View commit history
git log --oneline --graph --all

# Stash changes
git stash
git stash pop

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Rebase branch
git rebase main

# Resolve merge conflicts
git mergetool
```

---

## Docker Commands

### Container Management

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Remove stopped containers
docker container prune

# Remove all containers
docker rm -f $(docker ps -aq)

# Execute command in container
docker exec -it [container-id] bash

# View container stats
docker stats

# Inspect container
docker inspect [container-id]
```

### Image Management

```bash
# List images
docker images

# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Build image
docker build -t [image-name]:[tag] .

# Push image
docker push [image-name]:[tag]

# Pull image
docker pull [image-name]:[tag]
```

### Volume Management

```bash
# List volumes
docker volume ls

# Remove unused volumes
docker volume prune

# Inspect volume
docker volume inspect [volume-name]

# Create volume
docker volume create [volume-name]
```

### Network Management

```bash
# List networks
docker network ls

# Create network
docker network create [network-name]

# Connect container to network
docker network connect [network-name] [container-id]

# Disconnect from network
docker network disconnect [network-name] [container-id]
```

---

## Troubleshooting Quick Tips

### Service Won't Start

```bash
# Check logs
docker-compose logs [service]

# Check port conflicts
lsof -i :8000

# Check .env file
cat .env

# Rebuild
docker-compose build --no-cache [service]
```

### Slow Performance

```bash
# Check resources
docker stats

# Check GPU
nvidia-smi

# Check disk space
df -h

# Check memory
free -h
```

### Network Issues

```bash
# Check connectivity
docker-compose exec service1 ping service2

# Check DNS
docker-compose exec service cat /etc/resolv.conf

# Check network
docker network inspect project-chimera_default
```

### GPU Issues

```bash
# Check GPU
nvidia-smi

# Check CUDA
nvcc --version

# Check Docker GPU
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Fallback to CPU
echo "DEVICE=cpu" >> .env
```

---

## Monitoring Commands

### Check System Resources

```bash
# CPU and memory
htop

# Disk usage
df -h

# Disk I/O
iotop

# Network stats
iftop

# Docker stats
docker stats
```

### View Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Service metrics
curl http://localhost:8000/metrics

# Jaeger traces
curl http://localhost:16686/api/traces

# Grafana dashboards
curl http://localhost:3000/api/dashboards
```

---

## Development Tips

### Code Quality

```bash
# Format code
black services/

# Lint code
pylint services/

# Type check
mypy services/

# Security check
bandit -r services/

# Import sort
isort services/
```

### Testing Tips

```bash
# Run specific test module
pytest tests/test_module.py

# Run specific test function
pytest tests/test_module.py::test_function

# Run with markers
pytest -m "not slow"

# Generate coverage report
pytest --cov=services --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Debugging Tips

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Use Python debugger
import pdb; pdb.set_trace()

# Use IPython debugger
import ipdb; ipdb.set_trace()

# Debug with pytest
pytest --pdb

# Debug with VS Code
# Add launch configuration in .vscode/launch.json
```

---

## Useful URLs

### Service URLs

```
http://localhost:8000          # Orchestrator API
http://localhost:8000/docs     # Orchestrator Swagger UI
http://localhost:8001/docs     # SceneSpeak Swagger UI
http://localhost:8002/docs     # Captioning Swagger UI
http://localhost:8003/docs     # BSL Swagger UI
http://localhost:8004/docs     # Sentiment Swagger UI
http://localhost:8005/docs     # Lighting Swagger UI
http://localhost:8006/docs     # Safety Swagger UI
http://localhost:8007          # Operator Console
http://localhost:3000          # Grafana
http://localhost:9090          # Prometheus
http://localhost:16686         # Jaeger
```

### Documentation

```
https://docs.project-chimera.org          # Main documentation
https://api.project-chimera.org           # API documentation
https://github.com/your-org/project-chimera  # GitHub repository
```

---

## Keyboard Shortcuts

### Docker Compose

```
Ctrl+C        # Stop services (when running without -d)
Ctrl+P, Ctrl+Q # Detach from container
```

### Vim

```
:q            # Quit
:q!           # Quit without saving
:w            # Save
:wq           # Save and quit
i             # Insert mode
Esc           # Normal mode
/dd           # Delete line
/u            # Undo
```

### System

```
Ctrl+C        # Cancel current command
Ctrl+D        # Logout
Ctrl+L        # Clear screen
Ctrl+R        # Search command history
!!            # Last command
!*            # Last command arguments
```

---

**Related Documentation:**
- [Getting Started Guide](./quick-start.md)
- [Development Guide](../DEVELOPMENT.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Troubleshooting](../runbooks/troubleshooting.md)
