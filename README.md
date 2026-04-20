# Project Chimera

> An AI-powered live theatre platform creating performances that adapt in real-time to audience input.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-operational-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Docker](https://img.shields.io/badge/docker-compose--blue)

*Last Updated: April 20, 2026*

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd Project_Chimera

# Start all services
docker compose up -d

# Verify services are healthy
curl http://localhost:8000/health  # OpenClaw Orchestrator
curl http://localhost:8012/health  # Health Aggregator

# Access the Dashboard
open http://localhost:8013
```

## 📊 Current Cluster Status

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| **OpenClaw Orchestrator** | 8000 | ✅ Healthy | Core coordination and routing |
| **SceneSpeak Agent** | 8001 | ✅ Healthy | LLM dialogue generation |
| **Translation Agent** | 8009 | ✅ Healthy | Multi-language support |
| **Sentiment Agent** | 8004 | ✅ Healthy | DistilBERT sentiment analysis |
| **Safety Filter** | 8006 | ✅ Healthy | Content moderation |
| **Operator Console** | 8007 | ✅ Healthy | Show control UI |
| **Echo Agent** | 8014 | ⚠️ Unhealthy | Simple echo service |
| **Health Aggregator** | 8012 | ✅ Healthy | Unified health monitoring |
| **Dashboard** | 8013 | ✅ Healthy | Web UI for monitoring |

### Infrastructure Services

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| Redis | 6379 | ✅ Healthy | State management |
| Kafka | 9092 | ✅ Healthy | Event streaming |
| Milvus | 19530 | ✅ Healthy | Vector database |
| etcd | 2379-2380 | ✅ Running | Configuration storage |
| Prometheus | 9094 | ✅ Healthy | Metrics collection |
| Grafana | 3000 | ✅ Healthy | Visualization |
| Jaeger | 16686 | ✅ Healthy | Distributed tracing |
| Netdata | 19999 | ✅ Healthy | System monitoring |

**Overall Status: ✅ OPERATIONAL**

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Dashboard (8013)                          │
│              Health Monitoring & Control UI                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Health Aggregator (8012)                     │
│              Polls all services, unified status               │
└───┬───────────┬───────────┬───────────┬────────────────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────┐  ┌─────────┐  ┌──────────┐  ┌───────────┐
│Orchestr│  │SceneSpeak│  │Sentiment │  │Safety     │
│ator    │  │          │  │          │  │Filter     │
│(8000)  │  │  (8001)  │  │  (8004)  │  │  (8006)   │
└────────┘  └─────────┘  └──────────┘  └───────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Shared Infrastructure                    │
│  Redis (6379) │ Kafka (9092) │ Milvus (19530)              │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Project_Chimera/
├── services/
│   ├── openclaw-orchestrator/   # Core coordination service
│   ├── scenespeak-agent/        # LLM dialogue generation
│   ├── sentiment-agent/         # Sentiment analysis
│   ├── safety-filter/           # Content moderation
│   ├── translation-agent/       # Multi-language support
│   ├── echo-agent/              # Simple echo service
│   ├── operator-console/        # Human oversight UI
│   ├── dashboard/               # Health monitoring UI
│   ├── health-aggregator/       # Unified health monitoring
│   └── shared/                  # Shared utilities and middleware
├── docker-compose.yml           # Full stack orchestration
├── docs/                        # Documentation
│   ├── E2E-TEST-REPORT-2026-04-20.md
│   └── ...
└── README.md
```

## 🔧 Service Endpoints

### OpenClaw Orchestrator (Port 8000)
- `GET /health` - Service health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks all agents)
- `POST /api/orchestrate` - Main orchestration endpoint

### SceneSpeak Agent (Port 8001)
- `GET /health` - Service health and model status
- `POST /api/generate` - Generate dialogue

### Sentiment Agent (Port 8004)
- `GET /health` - Service health and model status
- `POST /api/analyze` - Analyze sentiment of text

### Safety Filter (Port 8006)
- `GET /health` - Service health and moderation status
- `POST /api/moderate` - Moderate content (⚠️ known tracing issue)

### Translation Agent (Port 8009)
- `GET /health` - Service health and engine status
- `POST /translate` - Translate text (mock mode)

### Health Aggregator (Port 8012)
- `GET /health` - Unified health status for all services

### Dashboard (Port 8013)
- `GET /` - Web UI
- `GET /health` - Service health
- `GET /api/dashboard` - Dashboard data API

## 🧪 Testing

### Run E2E Tests

```bash
# From project root
docker compose exec openclaw-orchestrator pytest
docker compose exec sentiment-agent pytest
docker compose exec safety-filter pytest
```

### Manual API Testing

```bash
# Test orchestration
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"The hero enters","show_id":"test"}'

# Test sentiment analysis
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I am very happy today!"}'

# Check all services
curl http://localhost:8012/health | jq .
```

## 📈 Monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9094
- **Jaeger UI**: http://localhost:16686
- **Netdata**: http://localhost:19999
- **Health Dashboard**: http://localhost:8013

## 🛠️ Development

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Make (optional)

### Build & Run

```bash
# Build all services
docker compose build

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Individual Service Management

```bash
# Restart specific service
docker compose restart openclaw-orchestrator

# View service logs
docker compose logs -f scenespeak-agent

# Scale a service
docker compose up -d --scale sentiment-agent=3
```

## 📝 Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [E2E Test Report](docs/E2E-TEST-REPORT-2026-04-20.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- FastAPI
- Redis
- Apache Kafka
- Milvus Vector Database
- Docker & Docker Compose

---

**Note**: This project is under active development. Services marked as "unhealthy" may be under development or require additional configuration.
