# Student Quick Start Guide
## Project Chimera: Development Environment Setup

**Version:** 0.4.0
**Audience:** AI Students joining Project Chimera
**Last Updated:** March 2026

---

## Welcome to Project Chimera

This guide will help you set up your development environment to contribute to Project Chimera, a student-run Dynamic Performance Hub that creates live theatre adapting in real time to audience input. The project uses **k3s** (lightweight Kubernetes) for local development, providing a production-like environment on your machine.

### What You Will Be Working On

As an AI student contributor, you may work on:

- **OpenClaw Skills:** Python modules that integrate with the orchestrator
- **AI Agents:** Containerised services for dialogue generation, captioning, sentiment analysis, BSL translation
- **Model Pipelines:** Fine-tuning, evaluation, and inference optimisation
- **Infrastructure:** Kubernetes manifests, CI/CD pipelines, monitoring
- **Platform Services:** Quality platform including test orchestration, dashboards, CI/CD gateway
- **Performance Optimization:** Profiling, caching, resource monitoring
- **Testing:** Unit tests, integration tests, load tests, safety tests
- **Documentation:** API docs, runbooks, architecture documentation

### Student Role Assignments

Project Chimera is divided into 10 focus areas. Each student will be assigned ownership of one component:

| # | Role | Component | Port | Description |
|---|------|-----------|------|-------------|
| 1 | OpenClaw Orchestrator Lead | `openclaw-orchestrator` | 8000 | Skill routing, agent coordination |
| 2 | SceneSpeak Agent Lead | `SceneSpeak Agent` | 8001 | LLM dialogue generation with LoRA adapters |
| 3 | Captioning Agent Lead | `Captioning Agent` | 8002 | Speech-to-text, live captions |
| 4 | BSL Translation Lead | `BSL Agent` | 8003 | Text-to-BSL gloss + avatar rendering |
| 5 | Sentiment Analysis Lead | `Sentiment Agent` | 8004 | Audience emotion analysis |
| 6 | Lighting Control Lead | `lighting-service` | 8005 | DMX/sACN lighting integration |
| 7 | Safety Filter Lead | `safety-filter` | 8006 | ML-based multi-layer content moderation |
| 8 | Operator Console Lead | `operator-console` | 8007 | Real-time oversight dashboard with WebSocket updates |
| 9 | Infrastructure & DevOps Lead | `infrastructure/` | - | k3s, Kubernetes, monitoring, CI/CD |
| 10 | QA & Documentation Lead | `platform/` | 8010-8013 | Test orchestration, dashboard, CI/CD gateway, quality gate |

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 16 GB | 32 GB+ |
| Disk Space | 30 GB free | 50 GB+ free |
| CPU | 6 cores | 8+ cores |
| OS | Linux (Ubuntu 22.04) | Ubuntu 22.04 LTS |
| GPU | None | NVIDIA GPU (optional) |

**Note:** The k3s bootstrap requires Linux. For macOS/Windows, use WSL2 or a Linux VM.

### Required Software

Before starting, ensure you have the following installed:

#### For Linux (Ubuntu 22.04)

1. **Git** - Version control
   - Verify: `git --version`
   - Install: `sudo apt update && sudo apt install git`

2. **Docker** - Container runtime
   - Verify: `docker --version`
   - Install: https://docs.docker.com/engine/install/ubuntu/

3. **kubectl** - Kubernetes CLI
   - Verify: `kubectl version --client`
   - Install: `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install kubectl /usr/local/bin/`

4. **Python 3.10+** - For local scripts and tools
   - Verify: `python3 --version`
   - Install: `sudo apt install python3 python3-pip`

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

## Quick Start: k3s Bootstrap

The bootstrap process automates the complete setup of Project Chimera on a local k3s cluster.

### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/project-chimera/main.git
cd Project_Chimera

# Or use SSH if you have keys set up
git clone git@github.com:project-chimera/main.git
cd Project_Chimera
```

### Step 2: Run Bootstrap

```bash
# Automated setup (requires sudo for k3s installation)
make bootstrap

# This will:
# 1. Install k3s (lightweight Kubernetes)
# 2. Set up local container registry (localhost:30500)
# 3. Build all 8 service Docker images
# 4. Deploy infrastructure (Redis, Kafka, Milvus)
# 5. Deploy monitoring (Prometheus, Grafana, Jaeger)
# 6. Deploy all AI agents
# 7. Run health checks
```

**Expected runtime:** 15-20 minutes

**Bootstrap Process:**

```
🚀 Bootstrapping Project Chimera...
[01-install-k3s] Installing k3s...
[02-setup-registry] Setting up local registry...
[03-build-images] Building 8 service images...
[04-deploy-infrastructure] Deploying Redis, Kafka, Milvus...
[05-deploy-monitoring] Deploying Prometheus, Grafana, Jaeger...
[06-deploy-services] Deploying AI agents...
[07-verify-deployment] Running health checks...

🎉 Bootstrap complete!
```

### Step 3: Verify Deployment

```bash
# Check all pods are running
make bootstrap-status

# Expected output:
# 📊 Bootstrap Status:
# NAME              STATUS   ROLES    AGE   VERSION
# localhost         Ready    control-plane  10m   v1.28.3+k3s1
#
# Namespace: live
# NAME                                   READY   STATUS    RESTARTS   AGE
# openclaw-orchestrator-...              1/1     Running   0          5m
# SceneSpeak Agent-...                   1/1     Running   0          5m
# Captioning Agent-...                   1/1     Running   0          5m
# ...
```

### Step 4: Access Services

**Monitoring Stack:**

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |

**Service APIs (use port-forward):**

```bash
make run-openclaw    # OpenClaw: localhost:8000
make run-scenespeak  # SceneSpeak: localhost:8001
make run-captioning  # Captioning: localhost:8002
```

### Step 5: Run Tests

```bash
# Run unit tests
make test-unit

# Run with coverage
pytest tests/unit/ --cov=services --cov-report=html

# View coverage report
xdg-open htmlcov/index.html  # Linux
```

---

## Project Structure Overview

```
project-chimera/
├── services/                    # AI Service Implementations
│   ├── openclaw-orchestrator/   # Skill orchestration (port 8000)
│   ├── SceneSpeak Agent/        # Dialogue generation (port 8001) + LoRA adapters
│   ├── Captioning Agent/        # Speech-to-text (port 8002)
│   ├── BSL Agent/               # BSL translation (port 8003) + avatar renderer
│   ├── Sentiment Agent/         # Sentiment analysis (port 8004)
│   ├── lighting-service/        # DMX/sACN control (port 8005)
│   ├── safety-filter/           # ML-based safety (port 8006) + multi-layer filtering
│   └── operator-console/        # Human oversight (port 8007) + real-time updates
├── platform/                    # Chimera Quality Platform (NEW)
│   ├── test-orchestrator/       # Test orchestration (port 8011)
│   ├── dashboard-service/       # Quality dashboard (port 8010)
│   ├── cicd-gateway/           # CI/CD webhook gateway (port 8012)
│   ├── quality-gate/            # Quality threshold enforcement
│   ├── shared/                 # Shared utilities
│   ├── deployment/             # Helm charts, deployment scripts
│   ├── monitoring/             # Prometheus configs, Grafana dashboards
│   └── perf-optimizer/         # Performance profiling utilities
├── skills/                      # OpenClaw skill definitions
├── models/                      # AI models and prompts
│   ├── prompts/                 # LLM prompt templates
│   └── lora-adapters/           # Fine-tuned LoRA adapters
├── infrastructure/              # Kubernetes configurations
│   └── kubernetes/              # Helm charts for deployment
├── scripts/                     # Automation scripts
│   ├── bootstrap/               # Bootstrap scripts
│   ├── operations/              # Deployment and runbook scripts
│   └── cicd/pipelines/          # CI/CD pipeline scripts
├── tests/                       # Test suites (300+ tests passing)
│   ├── platform/                # Platform service tests
│   └── services/                # Service tests
├── docs/                        # Documentation
│   ├── getting-started/         # Student guides
│   ├── architecture/            # Architecture decisions
│   ├── api/                     # API documentation
│   └── runbooks/                # Operations runbooks
└── .github/                     # GitHub workflows
    └── workflows/              # CI/CD, PR validation, automated tests
```

---

## Working with Your Assigned Component

### For Service Owners (Roles 1-8)

Each service follows the same structure:

```bash
cd services/<your-service>/
```

**Service Directory Structure:**

```
services/<service-name>/
├── src/
│   └── <service-name>/
│       ├── __init__.py
│       ├── main.py            # FastAPI application
│       ├── config.py          # Configuration
│       └── handlers/          # Request handlers
├── tests/
│   ├── test_main.py
│   └── test_handlers.py
├── Dockerfile
├── requirements.txt
└── README.md
```

**Rebuild and redeploy your service:**

```bash
# Build new image
docker build -t localhost:30500/project-chimera/<service>:latest services/<service>/

# Push to local registry
docker push localhost:30500/project-chimera/<service>:latest

# Restart deployment
kubectl rollout restart deployment/<deployment-name> -n live

# Follow logs
kubectl logs -f -n live deployment/<deployment-name>
```

### For Infrastructure Lead (Role 9)

**Key responsibilities:**

```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A

# Access monitoring
make run-openclaw  # Port forward to services
kubectl port-forward -n shared svc/grafana 3000:3000

# Deploy infrastructure changes
kubectl apply -k infrastructure/kubernetes/base/redis/
kubectl apply -k infrastructure/kubernetes/base/kafka/
kubectl apply -k infrastructure/kubernetes/base/vector-db/
```

### For QA & Documentation Lead (Role 10)

**Key responsibilities:**

```bash
# Run all tests
make test

# Run specific test suites
make test-unit
make test-integration
make test-load

# Check coverage
pytest tests/ --cov=services --cov-report=html

# Lint and format
make lint
make format
```

---

## Development Workflow

### Making Changes to Your Component

1. **Create a feature branch:**

```bash
git checkout -b feature/<component>-<feature-name>
```

2. **Make your changes:**

```bash
# Edit files in services/<your-service>/
# Or skills/<your-skill>/
# Or infrastructure/
```

3. **Run tests:**

```bash
# Run all tests
make test

# Run specific test suites
make test-unit
make test-integration
```

4. **Format and lint:**

```bash
# Format code
make format

# Lint
make lint
```

5. **Build and test your service:**

```bash
# Build your service image
docker build -t localhost:30500/project-chimera/<service>:test services/<service>/

# Test locally before pushing
# (service-specific testing commands)
```

6. **Commit and push:**

```bash
git add .
git commit -m "feat(<service>): description of your changes"
git push origin feature/<component>-<feature-name>
```

7. **Create pull request:**

- Go to GitHub and create a PR
- Fill in the PR template
- Wait for CI to pass
- Request review from Technical Lead

---

## Service-Specific Quick Reference

### 1. OpenClaw Orchestrator (Port 8000)

```bash
# Port forward to local
make run-openclaw

# Access API
curl http://localhost:8000/health

# Shell access
make shell-openclaw

# View logs
kubectl logs -f -n live deployment/openclaw-orchestrator
```

### 2. SceneSpeak Agent (Port 8001)

```bash
# Port forward to local
kubectl port-forward -n live svc/SceneSpeak Agent 8001:8001

# Test dialogue generation
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Scene: A garden at sunset", "sentiment": 0.7}'
```

### 3. Captioning Agent (Port 8002)

```bash
# Port forward to local
kubectl port-forward -n live svc/Captioning Agent 8002:8002

# View logs
kubectl logs -f -n live deployment/Captioning Agent
```

### 4. BSL-Text2Gloss Agent (Port 8003)

```bash
# Port forward to local
kubectl port-forward -n live svc/bsl-text2gloss-agent 8003:8003

# Test translation
curl -X POST http://localhost:8003/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the theatre."}'
```

### 5. Sentiment Agent (Port 8004)

```bash
# Port forward to local
kubectl port-forward -n live svc/Sentiment Agent 8004:8004

# Test sentiment analysis
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The audience seems excited!"}'
```

### 6. Lighting Control (Port 8005)

```bash
# Port forward to local
kubectl port-forward -n live svc/lighting-control 8005:8005

# View logs
kubectl logs -f -n live deployment/lighting-control
```

### 7. Safety Filter (Port 8006)

```bash
# Port forward to local
kubectl port-forward -n live svc/safety-filter 8006:8006

# Test safety check
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"content": "Test content for safety check"}'
```

### 8. Operator Console (Port 8007)

```bash
# Port forward to local
kubectl port-forward -n live svc/operator-console 8007:8007

# Access web interface
open http://localhost:8007
```

---

## New Features in v0.4.0

Project Chimera v0.4.0 introduces significant enhancements across multiple services:

### Performance Optimization

The `platform/perf-optimizer/` module provides performance profiling and optimization utilities:

```python
from platform.perf_optimizer.performance import PerformanceProfiler, CacheManager

# Profile function performance
profiler = PerformanceProfiler()

@profiler.profile("dialogue_generation")
def generate_dialogue(context):
    # Your code here
    pass

# View profiling results
print(profiler.get_results())
# {'dialogue_generation': {'calls': 100, 'avg_time': 0.05, 'max_time': 0.12}}

# Use caching for expensive operations
cache = CacheManager(redis_url="redis://localhost:6379")

@cache.cached(ttl=300)
def expensive_computation(input_data):
    # Cached for 5 minutes
    return complex_calculation(input_data)
```

### SceneSpeak LoRA Adapters

SceneSpeak now supports LoRA (Low-Rank Adaptation) adapters for efficient model fine-tuning:

```bash
# List available adapters
curl http://localhost:8001/v1/adapters

# Load a specific adapter
curl -X POST http://localhost:8001/v1/adapters/load \
  -H "Content-Type: application/json" \
  -d '{"name": "dramatic-theatre"}'

# Switch between adapters
curl -X POST http://localhost:8001/v1/adapters/switch \
  -H "Content-Type: application/json" \
  -d '{"from": "dramatic-theatre", "to": "comedy"}'

# Generate with loaded adapter
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Scene: A garden", "adapter": "dramatic-theatre"}'
```

### Multi-Layer Safety Filtering

The safety filter now uses three-layer filtering for better content moderation:

1. **Pattern Matching** - Blocks known harmful patterns
2. **ML Classification** - Classifies content into toxic/hateful/sexual/violent categories
3. **Context-Aware Analysis** - Transformer-based context understanding

```bash
# Test safety filtering
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test message",
    "conversation_history": [
      {"user": "Hello"},
      {"assistant": "Hi there!"}
    ]
  }'

# Response:
# {
#   "action": "allow",
#   "layer": "audit",
#   "confidence": 1.0,
#   "reason": "Content passed all safety checks"
# }
```

### BSL Avatar Rendering

BSL agent now includes real-time avatar rendering for sign language visualization:

```bash
# Queue text for avatar signing
curl -X POST http://localhost:8003/api/v1/avatar/sign \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to the theatre!",
    "session_id": "user123"
  }'

# Get avatar state
curl http://localhost:8003/api/v1/avatar/state?session_id=user123

# Response:
# {
#   "state": "signing",
#   "current_gesture": {...},
#   "metrics": {
#     "frames_rendered": 150,
#     "avg_frame_time": 0.033
#   }
# }
```

### Real-Time Console Updates

Operator console now supports WebSocket-based real-time updates:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8007/ws/realtime');

// Subscribe to metrics
ws.send(JSON.stringify({
  action: 'subscribe',
  channels: ['metrics:SceneSpeak Agent', 'alerts']
}));

// Receive updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update);
  // {
  //   "type": "metric",
  //   "service": "SceneSpeak Agent",
  //   "metric": "cpu_percent",
  //   "value": 45.2,
  //   "unit": "%"
  // }
};
```

---

## Quality Platform Services

The Chimera Quality Platform provides comprehensive testing, monitoring, and quality assurance tools:

### Dashboard Service (Port 8010)

Web-based quality dashboards and visualization:

```bash
# Port forward to local
kubectl port-forward -n quality svc/dashboard-service 8010:8010

# Access web interface
open http://localhost:8010

# View logs
kubectl logs -f -n quality deployment/dashboard-service
```

### Test Orchestrator (Port 8011)

Test discovery, execution, and reporting:

```bash
# Port forward to local
kubectl port-forward -n quality svc/test-orchestrator 8011:8011

# Run all tests
curl -X POST http://localhost:8011/api/v1/tests/run

# Run specific test suite
curl -X POST http://localhost:8011/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{"suite": "unit", "module": "services/SceneSpeak Agent"}'

# Get test results
curl http://localhost:8011/api/v1/results/latest
```

### CI/CD Gateway (Port 8012)

GitHub/GitLab webhook integration for CI/CD:

```bash
# Port forward to local
kubectl port-forward -n quality svc/cicd-gateway 8012:8012

# Test health
curl http://localhost:8012/health

# Trigger deployment manually
curl -X POST http://localhost:8012/api/v1/deploy \
  -H "Content-Type: application/json" \
  -d '{"environment": "staging", "ref": "main"}'
```

### Quality Gate (Port 8013)

Quality threshold enforcement and reporting:

```bash
# Port forward to local
kubectl port-forward -n quality svc/quality-gate 8013:8013

# Check quality gate status
curl http://localhost:8013/api/v1/gate/check

# Get quality metrics
curl http://localhost:8013/api/v1/metrics
```

**Platform Quick Reference:**

| Component | Port | Description |
|-----------|-----|-------------|
| Dashboard Service | 8010 | Quality dashboards and visualization |
| Test Orchestrator | 8011 | Test discovery and execution |
| CI/CD Gateway | 8012 | GitHub/GitLab webhook integration |
| Quality Gate | 8013 | Quality threshold enforcement |

**Running Platform Tests:**

```bash
# Run Quality Platform unit tests
cd platform
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=platform --cov-report=html

# View coverage report
xdg-open htmlcov/index.html
```

**Testing New Features:**

```bash
# Test performance optimizer
cd platform/perf-optimizer
python -m pytest tests/ -v

# Test LoRA adapters
cd services/SceneSpeak Agent
python -m pytest tests/test_lora_adapter.py -v

# Test ML safety filter
cd services/safety-filter
python -m pytest tests/test_ml_safety.py -v

# Test BSL avatar renderer
cd services/BSL Agent
python -m pytest tests/test_avatar_renderer.py -v

# Test real-time updates
cd services/operator-console
python -m pytest tests/test_realtime_updates.py -v
```

---

## Troubleshooting

### Common Issues and Solutions

#### k3s Issues

**Problem: k3s won't start**

```bash
# Check k3s status
sudo systemctl status k3s

# View logs
journalctl -u k3s -n 50

# Restart k3s
sudo systemctl restart k3s
```

**Problem: Pods stuck in Pending state**

```bash
# Check pod status
kubectl get pods -A

# Describe pod to see why
kubectl describe pod <pod-name> -n <namespace>

# Common issues:
# - ImagePullBackOff: Check registry is accessible
# - Insufficient resources: Check CPU/memory available
```

**Problem: ImagePullBackOff errors**

The k3s nodes cannot pull from localhost:30500 without manual configuration. Two options:

**Option 1: Configure k3s for insecure registry** (requires sudo):

```bash
sudo mkdir -p /etc/rancher/k3s/
cat <<EOF | sudo tee /etc/rancher/k3s/registries.yaml
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF

sudo systemctl restart k3s
```

**Option 2: Load images directly into k3s**:

```bash
# Save image from Docker
docker save localhost:30500/project-chimera/<service>:latest -o <service>.tar

# Load into k3s
sudo k3s ctr images import <service>.tar

# Clean up
rm <service>.tar
```

#### Docker Issues

**Problem: Docker daemon not running**

```bash
# Start Docker
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

**Problem: Port already in use**

```bash
# Find what's using the port
sudo lsof -i :<port>

# Kill port-forwards
pkill -f "port-forward"

# Or kill specific process
kill <PID>
```

#### Pod Issues

**Problem: Pod keeps restarting**

```bash
# View logs
kubectl logs -f -n live deployment/<deployment-name>

# View previous container logs
kubectl logs -f -n live deployment/<deployment-name> --previous

# Common issues:
# - Application crashes
# - Missing environment variables
# - Failed health checks
```

**Problem: Cannot connect to service**

```bash
# Verify service exists
kubectl get svc -n live

# Port forward to local
kubectl port-forward -n live svc/<service-name> <local-port>:<service-port>

# Test connection
curl http://localhost:<local-port>/health
```

### Verification Checklist

If something isn't working, run through this checklist:

```bash
# 1. k3s is running
sudo systemctl status k3s
kubectl get nodes

# 2. All namespaces exist
kubectl get namespaces

# 3. All pods are running
make bootstrap-status

# 4. Services are accessible
kubectl get svc -A

# 5. Docker is running
docker info

# 6. Tests pass
make test-unit

# 7. Can access Grafana
curl http://localhost:3000
```

### Getting Help

If you're stuck:

1. **Check the documentation:**
   - This guide
   - `/docs/` folder in the repository
   - `/reference/runbooks/bootstrap-setup.md`
   - `/docs/plans/IMPLEMENTATION_DOCUMENTATION.md`

2. **Search existing issues:**
   - GitHub Issues: https://github.com/project-chimera/main/issues

3. **Ask in the team chat:**
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
feat(scenespeak): add dialogue caching

Implements a caching layer for SceneSpeak dialogue to reduce
latency for repeated context. Cache uses Redis with 5-minute TTL.

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

1. **Read the Implementation Documentation:**
   - `/docs/plans/IMPLEMENTATION_DOCUMENTATION.md`
   - Understanding how the scaffold was built helps you contribute effectively

2. **Explore Your Assigned Component:**
   - Review the service/skill code
   - Read the component's README.md
   - Understand the configuration

3. **Join Team Meetings:**
   - Daily standup: [time]
   - Weekly planning: [time]
   - Ask for calendar invite

4. **Introduce Yourself:**
   - Share your interests and what you want to work on
   - Ask questions about your assigned component

5. **Start Contributing:**
   - Look for issues in your component area
   - Start with documentation or test improvements
   - Propose new features for your component

---

## Quick Reference

### Essential Make Commands

| Task | Command |
|------|---------|
| Bootstrap setup | `make bootstrap` |
| Check status | `make bootstrap-status` |
| Clean destroy | `make bootstrap-destroy` |
| Run tests | `make test` |
| Format code | `make format` |
| Lint | `make lint` |
| Port forward OpenClaw | `make run-openclaw` |
| Port forward SceneSpeak | `make run-scenespeak` |
| View logs | `make logs` |
| View all logs | `make logs-all` |

### Service URLs (after port-forward)

| Service | Local Port | Description |
|---------|-----------|-------------|
| OpenClaw | 8000 | Orchestrator API |
| SceneSpeak | 8001 | Dialogue generation (with LoRA adapters) |
| Captioning | 8002 | Speech-to-text |
| BSL-Text2Gloss | 8003 | BSL translation + avatar rendering |
| Sentiment | 8004 | Sentiment analysis |
| Lighting | 8005 | DMX/sACN control |
| Safety Filter | 8006 | ML-based multi-layer content moderation |
| Operator Console | 8007 | Oversight UI with WebSocket updates |
| Dashboard Service | 8010 | Quality platform dashboards |
| Test Orchestrator | 8011 | Test discovery and execution |
| CI/CD Gateway | 8012 | GitHub/GitLab webhook integration |
| Quality Gate | 8013 | Quality threshold enforcement |
| Grafana | 3000 | Monitoring dashboards |
| Prometheus | 9090 | Metrics |
| Jaeger | 16686 | Distributed tracing |

### Useful Files

| File | Purpose |
|------|---------|
| `getting-started/quick-start.md` | This file |
| `Makefile` | Build automation |
| `reference/runbooks/bootstrap-setup.md` | Bootstrap guide |
| `docs/plans/IMPLEMENTATION_DOCUMENTATION.md` | Implementation details |
| `scripts/bootstrap/` | Bootstrap scripts |
| `infrastructure/kubernetes/base/` | Kubernetes manifests |

---

*Welcome to Project Chimera! We're excited to have you on the team.*

*Questions? Reach out to your Technical Lead or check the documentation.*
