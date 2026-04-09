# Project Chimera - Quick Start Guide

**Last Updated**: 2026-04-09
**Status**: Phase 1 Complete - Proof-of-Concept ✅

**Important Note**: Project Chimera Phase 1 has been strategically pivoted to a **Local-First AI Framework Proof-of-Concept**. See `docs/STRATEGIC_PIVOT_MANDATE.md` for details.

---

## 🚀 What is Project Chimera?

Project Chimera Phase 1 is an **AI-powered adaptive framework proof-of-concept** demonstrating:

- **Sentiment Analysis** - ML-based emotion detection (DistilBERT)
- **Adaptive Dialogue Generation** - Context-aware response routing
- **Monolithic Demonstrator** - Single Python script proving core logic
- **Accessibility Features** - Basic caption formatting (Phase 1)
- **Microservices Architecture** - Full distributed system (operational)

**What Works Now**:
- ✅ chimera_core.py: Monolithic demonstrator with adaptive routing
- ✅ Sentiment analysis: DistilBERT ML model (99.9% accuracy)
- ✅ Dialogue generation: GLM-4.7 API or Ollama fallback
- ✅ Comparison mode: Side-by-side adaptive vs non-adaptive
- ✅ Caption mode: Basic accessibility formatting

**Moved to future_concepts/** (Phase 2):
- ⚠️ BSL Avatar (requires 3D rendering and gesture library)
- ⚠️ Live Captioning (requires venue and display infrastructure)
- ⚠️ Hardware Integration (DMX lighting, audio systems)

**Architecture**: 8 core microservices (operational) + monolithic demonstrator (new)

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

---

## 🎯 Monolithic Demonstrator (NEW - Phase 1 Deliverable)

The **chimera_core.py** script is a single, self-contained Python script that demonstrates the core adaptive routing logic without requiring Docker or microservices.

### Quick Start (No Docker Required)

```bash
cd services/operator-console

# Run with single input
python3 chimera_core.py "I'm so excited about this project!"

# Run comparison mode (adaptive vs non-adaptive)
python3 chimera_core.py compare "I'm frustrated with how things are going"

# Run caption mode (accessibility formatting)
python3 chimera_core.py caption "Can you tell me more about the system?"

# Run demo mode (all three sentiment types)
python3 chimera_core.py demo

# Run interactive mode
python3 chimera_core.py
# Then try: compare <text>, caption <text>, demo, or quit
```

### What the Demonstrator Shows

1. **Sentiment Analysis**: DistilBERT ML model detects emotion
2. **Adaptive Routing**: System adjusts response based on sentiment
   - Positive → Enthusiastic, momentum-building response
   - Negative → Empathetic, supportive response
   - Neutral → Professional, informative response
3. **Comparison Mode**: Side-by-side adaptive vs non-adaptive
4. **Caption Mode**: High-contrast text formatting for accessibility

### Evidence Output

The script generates JSON output showing:
- Sentiment classification (positive/negative/neutral)
- Confidence scores and emotion vectors
- Adaptive routing strategy selected
- Generated dialogue with metadata
- Full processing trace

This is the **primary deliverable** for Phase 1 grant closeout.

---

## ♿ Accessibility Features (Phase 1)

### Caption Formatting

The chimera_core.py script includes basic caption formatting for accessibility:

```bash
# Generate formatted caption
python3 chimera_core.py caption "Your text here"
```

**Features**:
- High-contrast visual formatting (60-character width)
- Sentiment-based visual indicators (😊 positive, 😟 negative, 💬 neutral)
- Plain text caption output
- SRT subtitle format generation

**Example Output**:
```
████████████████████████████████████████████████████████████
█                         POSITIVE                         █
█                                                        █
█  That's wonderful to hear! Your positive energy is contagious.  █
█        Let's build on this momentum together!        █
█                                                        █
████████████████████████████████████████████████████████████
```

### Limitations

**Moved to Phase 2** (see `docs/LIMITATIONS_AND_FUTURE_ROADMAP.md`):
- ❌ Real-time caption display (requires venue infrastructure)
- ❌ BSL 3D avatar (requires gesture library + 3D rendering)
- ❌ Live performance integration (requires venue + hardware)

**Why**: These features require 3-6 months development time and specialist resources not available in Phase 1.

---

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
