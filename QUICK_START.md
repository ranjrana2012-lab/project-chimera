# Project Chimera - Quick Start Guide

**Last Updated**: 2026-03-30
**Status**: Production Ready ✅
**E2E Tests**: 149/149 passing (100%)

---

## 🚀 What is Project Chimera?

Project Chimera is an **AI-powered live theatre platform** that creates real-time, interactive performances by combining:

- **Sentiment Analysis** - Audience reaction tracking
- **BSL Avatar** - Sign language translation avatar
- **Captioning** - Real-time subtitle generation
- **Lighting/Sound Control** - Dynamic atmosphere adjustment
- **Music Generation** - AI-composed soundscapes
- **Orchestrator** - Coordinates all services in real-time

**Architecture**: 13 microservices using FastAPI, WebSocket communication, and ML models.

---

## 📋 Prerequisites

### Required
- **Docker & Docker Compose** - for running all services
- **Git** - for cloning the repository
- **Node.js 18+** - for E2E tests

### Recommended
- **8GB+ RAM** - for running all services + ML models
- **Python 3.12+** - for local development
- **VS Code** - with Python and Docker extensions

---

## 🏃 Quick Start (5 Minutes)

### 1. Clone & Start Services

```bash
# Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Start all services (takes ~2-3 minutes first time)
docker compose up -d

# Verify all services are healthy
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done
```

Expected output:
```
{"status":"healthy"} : Port 8000 OK
{"status":"healthy"} : Port 8001 OK
...
```

### 2. Try the Features

**Test Sentiment Analysis**:
```bash
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This performance is absolutely amazing!"}'
```

**Test WebSocket Connection**:
```bash
# Connect to show state updates
wscat -c ws://localhost:8000/ws/show
# Send: {"action": "ping"}
```

**View Service Logs**:
```bash
docker compose logs -f sentiment-agent
```

### 3. Run E2E Tests

```bash
cd tests/e2e
npm install
npm test
```

Expected: `149 passed, 45 skipped`

---

## 📁 Project Structure

```
project-chimera/
├── services/              # All microservices
│   ├── sentiment-agent/   # Sentiment analysis (port 8004)
│   ├── bsl-agent/         # BSL avatar/sign language (port 8003)
│   ├── captioning-agent/  # Real-time captions (port 8002)
│   ├── scenespeak-agent/  # Scene dialogue generation (port 8001)
│   ├── nemoclaw-orchestrator/  # Main orchestrator (port 8000)
│   └── ...               # Other services
├── tests/
│   └── e2e/              # End-to-end tests (Playwright)
├── docker-compose.yml    # Development configuration
├── docker-compose.prod.yml  # Production configuration
├── PRODUCTION_READINESS_CHECKLIST.md
└── README.md
```

---

## 🔧 Common Tasks

### View All Services
```bash
docker compose ps
```

### Restart a Service
```bash
docker compose restart sentiment-agent
```

### View Service Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f orchestrator
```

### Stop All Services
```bash
docker compose down
```

### Run Tests
```bash
cd tests/e2e
npm test

# Run specific test file
npm test -- websocket/sentiment-updates.spec.ts

# Run with UI
npm test -- --ui
```

---

## 🌐 Service Endpoints

| Service | Port | Health | Purpose |
|---------|------|--------|---------|
| Orchestrator | 8000 | `/health/live` | Main coordinator |
| SceneSpeak | 8001 | `/health/live` | Dialogue generation |
| Captioning | 8002 | `/health/live` | Real-time captions |
| BSL Avatar | 8003 | `/health/live` | Sign language avatar |
| Sentiment | 8004 | `/api/analyze` | Sentiment analysis |
| Lighting/Sound | 8005 | `/health/live` | Atmosphere control |
| Safety Filter | 8006 | `/health/live` | Content moderation |
| Operator Console | 8007 | `/health/live` | Human interface |

---

## 🧪 Testing

### Run All E2E Tests
```bash
cd tests/e2e
npm test
```

### Run Specific Test Categories
```bash
# API tests only
npm test -- api/

# WebSocket tests only
npm test -- websocket/

# UI tests only
npm test -- ui/
```

### View Test Results
```bash
# HTML report
open playwright-report/index.html

# JSON results
cat test-results/results.json
```

---

## 🐛 Troubleshooting

**Services not starting?**
```bash
# Check port conflicts
netstat -tuln | grep -E '800[0-7]'

# Clean restart
docker compose down -v
docker compose up -d
```

**ML model loading slowly?**
- First request to sentiment/captioning services takes 5-10s
- Subsequent requests are fast
- This is intentional (lazy loading)

**Tests timing out?**
- Ensure services are fully started: `docker compose ps`
- Check service health: `curl http://localhost:8004/health`
- Run tests sequentially: `workers: 1` in playwright.config.ts

---

## 📚 Next Steps

1. **Read the Architecture**: `docs/architecture/`
2. **Review the Deployment Guide**: `DEPLOYMENT.md`
3. **Check Production Readiness**: `PRODUCTION_READINESS_CHECKLIST.md`
4. **Explore E2E Tests**: `tests/e2e/` directory

---

## 🆘 Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Test Results**: `tests/e2e/playwright-report/`

---

**Happy Coding! 🎭**
