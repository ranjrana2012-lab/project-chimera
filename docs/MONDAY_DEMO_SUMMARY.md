# Monday Demo Summary - Project Chimera

> **What Was Built Overnight:** A complete AI-powered live theatre platform with 8 microservices, full infrastructure, and monitoring stack.

**Date:** February 27, 2026
**Version:** v0.1.0 (Alpha)
**Status:** Ready for Student Development

---

## Executive Summary

Welcome to Project Chimera! Over the weekend, we built a complete **Dynamic Performance Hub** - an AI-powered live theatre platform that creates performances adapting in real-time to audience input. This is a student-run project combining multiple AI agents with stage automation.

### What You're Seeing Today

A fully functional microservices architecture with:

- **8 AI Services** - Each handling a specific theatrical/AI capability
- **3 Infrastructure Services** - Redis, Kafka, Milvus vector database
- **3 Monitoring Tools** - Prometheus, Grafana, Jaeger
- **Complete Kubernetes Deployment** - Ready for k3s local development
- **Testing Suite** - Unit, integration, load, and red-team tests
- **Full Documentation** - API docs, architecture, and runbooks

### The Big Picture

```
Audience Input (Social Media)
         ↓
   Sentiment Analysis
         ↓
   SceneSpeak Agent (Dialogue Generation)
         ↓
    Safety Filter
         ↓
   Operator Approval
         ↓
   Captioning + BSL Translation
         ↓
   Lighting Control
         ↓
    Live Performance!
```

---

## What Was Built: 8 Services + Infrastructure

### 1. OpenClaw Orchestrator (Port 8000)

**The Central Control Plane**

```
services/openclaw-orchestrator/
```

**What it does:**
- Coordinates all 7 other AI services
- Routes requests to appropriate skills
- Manages GPU resource scheduling
- Implements policy engine for safety
- Handles skill lifecycle (register, enable, disable)

**Key Features:**
- Skill Registry with vector-based matching
- Pipeline execution (chain multiple skills)
- GPU scheduler for resource management
- Kafka event streaming
- Redis caching layer

**Tech Stack:**
- FastAPI
- Redis (caching, pub/sub)
- Kafka (event streaming)
- Milvus (vector DB for skill matching)

**Quick Test:**
```bash
# Port forward to access locally
kubectl port-forward -n live svc/openclaw-orchestrator 8000:8000

# List all available skills
curl http://localhost:8000/api/v1/skills

# Execute orchestration
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "sentiment_to_dialogue",
    "input": {"social_posts": ["Amazing performance!"]},
    "context": {"scene_id": "scene-001"}
  }'
```

---

### 2. SceneSpeak Agent (Port 8001)

**Real-Time Dialogue Generation**

```
services/SceneSpeak Agent/
```

**What it does:**
- Generates theatrical dialogue using local LLMs
- Incorporates audience sentiment into character responses
- Produces stage directions and lighting cues
- Maintains character context across scenes

**Key Features:**
- Local LLM inference (Llama-based)
- LoRA adapter support for fine-tuning
- Response caching (Redis)
- Prompt template management
- Sentiment-aware generation

**Tech Stack:**
- FastAPI
- PyTorch + Transformers
- Redis (caching)
- Local LLM inference

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/SceneSpeak Agent 8001:8001

# Generate dialogue
curl -X POST http://localhost:8001/api/v1/dialogue/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scene_context": {
      "title": "Scene 1",
      "characters": ["ALICE", "BOB"],
      "setting": "A coffee shop"
    },
    "dialogue_context": [
      {"character": "ALICE", "text": "Hi, I'm Alice."}
    ],
    "sentiment_vector": {"overall": "positive", "energy": 0.8}
  }'
```

**Sample Response:**
```json
{
  "proposed_lines": "BOB: [Smiling warmly] Nice to meet you, Alice. I'm Bob. [LIGHTING: Soft warm light]",
  "stage_cues": ["[LIGHTING: Soft warm light on table]"],
  "metadata": {
    "model": "llama-2-7b-scenespeak",
    "tokens_generated": 45
  }
}
```

---

### 3. Captioning Agent (Port 8002)

**Live Speech-to-Text with Accessibility**

```
services/Captioning Agent/
```

**What it does:**
- Real-time speech-to-text transcription
- Live caption generation with timestamps
- Accessibility descriptions for visual content
- Multi-language support

**Key Features:**
- OpenAI Whisper for transcription
- WebSocket streaming for real-time updates
- Voice Activity Detection (VAD)
- Language auto-detection
- Word-level timestamps

**Tech Stack:**
- FastAPI
- OpenAI Whisper
- WebSockets
- Redis (stream coordination)

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/Captioning Agent 8002:8002

# Transcribe audio
curl -X POST http://localhost:8002/api/v1/captioning/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64-encoded-audio",
    "language": "en",
    "timestamps": true
  }'
```

---

### 4. BSL-Text2Gloss Agent (Port 8003)

**British Sign Language Translation**

```
services/bsl-text2gloss-agent/
```

**What it does:**
- Translates English text to BSL gloss notation
- Handles text normalization and preprocessing
- Supports non-manual markers (facial expressions, body language)
- Prepares content for sign language avatar/interpreter

**Key Features:**
- Text-to-gloss translation
- Non-manual marker annotation
- Gloss formatting standards
- Translation metadata

**Tech Stack:**
- FastAPI
- NLP transformers
- BSL-specific models

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/bsl-text2gloss-agent 8003:8003

# Translate to BSL gloss
curl -X POST http://localhost:8003/api/v1/gloss/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you today?",
    "preserve_format": true
  }'
```

**Sample Response:**
```json
{
  "gloss": "HELLO YOU HOW TODAY?",
  "breakdown": [
    {"source": "Hello", "gloss": "HELLO", "markers": ["wave"]},
    {"source": "how are you", "gloss": "YOU HOW", "markers": ["q", "br"]}
  ]
}
```

---

### 5. Sentiment Agent (Port 8004)

**Audience Sentiment Analysis**

```
services/Sentiment Agent/
```

**What it does:**
- Analyzes audience sentiment from social media
- Detects emotions (joy, sadness, anger, fear, surprise, disgust)
- Tracks sentiment trends over time
- Provides aggregated sentiment statistics

**Key Features:**
- DistilBERT SST-2 model
- Batch text processing
- Trend analysis over time windows
- Emotion detection
- Sentiment aggregation

**Tech Stack:**
- FastAPI
- Transformers (DistilBERT, RoBERTa)
- Redis (sentiment cache)
- Kafka (event streaming)

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/Sentiment Agent 8004:8004

# Analyze sentiment
curl -X POST http://localhost:8004/api/v1/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This performance is absolutely amazing!",
      "Best show I've ever seen!"
    ]
  }'
```

**Sample Response:**
```json
{
  "results": [{
    "text": "This performance is absolutely amazing!",
    "sentiment": "positive",
    "scores": {"positive": 0.95, "negative": 0.02, "neutral": 0.03},
    "confidence": 0.93
  }],
  "summary": {
    "overall": "positive",
    "average_scores": {"positive": 0.65, "negative": 0.15}
  }
}
```

---

### 6. Lighting Control (Port 8005)

**DMX/sACN Stage Automation**

```
services/lighting-control/
```

**What it does:**
- Controls DMX/sACN lighting fixtures
- Manages lighting scenes and presets
- Handles OSC messages for stage automation
- Provides approval workflow for scene changes

**Key Features:**
- DMX/sACN protocol support
- OSC message handling
- Scene preset management
- Fade time control
- Blackout functionality

**Tech Stack:**
- FastAPI
- SACN (sACN protocol)
- Python-OSC
- Redis (state sync)

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/lighting-control 8005:8005

# Set lighting scene
curl -X POST http://localhost:8005/api/v1/lighting/scene \
  -H "Content-Type: application/json" \
  -d '{
    "name": "warm_wash",
    "channels": {"1": 255, "2": 200, "3": 150},
    "fade_time_ms": 1000
  }'

# Get status
curl http://localhost:8005/api/v1/lighting/status
```

---

### 7. Safety Filter (Port 8006)

**Multi-Layer Content Moderation**

```
services/safety-filter/
```

**What it does:**
- Filters content for inappropriate material
- Implements word-based and ML-based filtering
- Provides audit logging for all content checks
- Maintains review queue for flagged content

**Key Features:**
- Word-based profanity detection
- ML-based content classification
- Multi-category filtering
- Audit logging
- Review queue workflow

**Tech Stack:**
- FastAPI
- NLP profanity detection
- Redis (blocklist cache)
- Kafka (audit events)

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/safety-filter 8006:8006

# Check content safety
curl -X POST http://localhost:8006/api/v1/safety/filter \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The character should say something appropriate here.",
    "context": "family_show"
  }'
```

**Sample Response:**
```json
{
  "safe": true,
  "confidence": 0.98,
  "flagged_categories": [],
  "filtered_content": "The character should say something appropriate here.",
  "review_required": false
}
```

---

### 8. Operator Console (Port 8007)

**Human Oversight Interface**

```
services/operator-console/
```

**What it does:**
- Provides real-time monitoring dashboard
- Manages approval workflow for critical actions
- Displays alerts and notifications
- Offers manual override controls

**Key Features:**
- Real-time WebSocket updates
- Alert management
- Approval/rejection workflow
- Manual override controls
- Dashboard UI

**Tech Stack:**
- FastAPI
- WebSocket (real-time updates)
- Kafka (event consumption)
- HTML/CSS/JavaScript (frontend)

**Quick Test:**
```bash
# Port forward
kubectl port-forward -n live svc/operator-console 8007:8007

# Access web interface
open http://localhost:8007

# Get alerts
curl http://localhost:8007/api/v1/console/alerts
```

---

## Infrastructure Components

### Shared Infrastructure

Located in `infrastructure/kubernetes/base/`

**1. Redis (Port 6379)**
- Caching layer for all services
- Pub/sub for event coordination
- Session storage

**2. Kafka (Port 9092)**
- Event streaming backbone
- Audit log pipeline
- Service-to-service messaging

**3. Milvus Vector DB (Port 19530)**
- Skill vector embeddings
- Semantic skill matching
- Context retrieval

**4. Monitoring Stack**
- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3000) - Visualization dashboards
- **Jaeger** (Port 16686) - Distributed tracing

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                  (Human Oversight & Dashboard)               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OpenClaw Orchestrator                      │
│              (Skill Routing & Coordination)                  │
└──┬────────┬────────┬────────┬────────┬────────┬───────────┘
   │        │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼        ▼
SceneSpeak Captioning  BSL   Sentiment Lighting Safety  Operator
  Agent     Agent    Agent   Agent  Control Filter  Console
   │         │        │        │        │        │
   └─────────┴────────┴────────┴────────┴────────┘
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
 Redis         Kafka        Milvus
```

### Data Flow Example: Audience Reaction → Stage Response

```
1. Audience tweets: "This is amazing! #ChimeraShow"
   ↓
2. Sentiment Agent analyzes: Positive, 0.95 confidence
   ↓
3. OpenClaw routes to SceneSpeak with sentiment context
   ↓
4. SceneSpeak generates dialogue incorporating positivity
   ↓
5. Safety Filter checks content
   ↓
6. Operator Console requests approval
   ↓
7. Operator approves
   ↓
8. Captioning Agent generates captions
   ↓
9. BSL Agent translates to gloss
   ↓
10. Lighting Control adjusts to warm, energetic scene
   ↓
11. Live performance adapts to audience emotion!
```

---

## Quick Start for Students

### Prerequisites

```bash
# Check you have the required tools
python3 --version  # Should be 3.10+
docker --version
kubectl version --client
```

### Option 1: Automated Bootstrap (Recommended)

```bash
# Clone the repository
git clone https://github.com/project-chimera/main.git
cd Project_Chimera

# Run automated setup (15-20 minutes)
make bootstrap

# This will:
# 1. Install k3s (lightweight Kubernetes)
# 2. Set up local container registry
# 3. Build all 8 service Docker images
# 4. Deploy infrastructure (Redis, Kafka, Milvus)
# 5. Deploy monitoring (Prometheus, Grafana, Jaeger)
# 6. Deploy all AI agents
```

### Verify Deployment

```bash
# Check all pods are running
make bootstrap-status

# Expected output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# openclaw-orchestrator-xxx              1/1     Running   0          5m
# SceneSpeak Agent-xxx                   1/1     Running   0          5m
# Captioning Agent-xxx                   1/1     Running   0          5m
# bsl-text2gloss-agent-xxx               1/1     Running   0          5m
# Sentiment Agent-xxx                    1/1     Running   0          5m
# lighting-control-xxx                   1/1     Running   0          5m
# safety-filter-xxx                      1/1     Running   0          5m
# operator-console-xxx                   1/1     Running   0          5m
```

---

## Service Endpoints Reference

### Quick Access Commands

```bash
# Port forward all services (run in separate terminals)
make run-openclaw      # OpenClaw: localhost:8000
make run-scenespeak    # SceneSpeak: localhost:8001
make run-captioning    # Captioning: localhost:8002

# Or manually:
kubectl port-forward -n live svc/openclaw-orchestrator 8000:8000
kubectl port-forward -n live svc/SceneSpeak Agent 8001:8001
kubectl port-forward -n live svc/Captioning Agent 8002:8002
kubectl port-forward -n live svc/bsl-text2gloss-agent 8003:8003
kubectl port-forward -n live svc/Sentiment Agent 8004:8004
kubectl port-forward -n live svc/lighting-control 8005:8005
kubectl port-forward -n live svc/safety-filter 8006:8006
kubectl port-forward -n live svc/operator-console 8007:8007
```

### Service URL Summary

| Service | Local Port | Cluster URL | Purpose |
|---------|-----------|-------------|---------|
| OpenClaw Orchestrator | 8000 | `openclaw-orchestrator.live.svc.cluster.local:8000` | Central coordination |
| SceneSpeak Agent | 8001 | `SceneSpeak Agent.live.svc.cluster.local:8001` | Dialogue generation |
| Captioning Agent | 8002 | `Captioning Agent.live.svc.cluster.local:8002` | Speech-to-text |
| BSL-Text2Gloss Agent | 8003 | `bsl-text2gloss-agent.live.svc.cluster.local:8003` | BSL translation |
| Sentiment Agent | 8004 | `Sentiment Agent.live.svc.cluster.local:8004` | Sentiment analysis |
| Lighting Control | 8005 | `lighting-control.live.svc.cluster.local:8005` | DMX/sACN control |
| Safety Filter | 8006 | `safety-filter.live.svc.cluster.local:8006` | Content moderation |
| Operator Console | 8007 | `operator-console.live.svc.cluster.local:8007` | Oversight UI |
| Grafana | 3000 | `grafana.shared.svc.cluster.local:3000` | Monitoring |
| Prometheus | 9090 | `prometheus.shared.svc.cluster.local:9090` | Metrics |
| Jaeger | 16686 | `jaeger.shared.svc.cluster.local:16686` | Tracing |

---

## Testing Instructions

### Run All Tests

```bash
# Run complete test suite
make test

# Run with coverage report
pytest tests/ --cov=services --cov-report=html

# View coverage in browser
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS
```

### Test Categories

```bash
# Unit tests only
make test-unit

# Integration tests
make test-integration

# Load tests
make test-load

# Red-team/safety tests
make test-red-team

# Accessibility tests
make test-accessibility
```

### Service-Specific Testing

```bash
# Test specific service
pytest tests/unit/test_scenespeak_agent.py -v

# Test with specific markers
pytest tests/integration/ -m "kafka" -v

# Run tests for a specific module
pytest tests/unit/ -k "sentiment" -v
```

### Example Test: Full Pipeline

```bash
# Test the complete flow from sentiment to dialogue
pytest tests/integration/test_full_pipeline.py -v -s
```

---

## Demo Scenarios to Show

### Scenario 1: "The Happy Audience" (5 minutes)

**Story:** The audience is loving the performance, show how the system adapts.

```bash
# 1. Check current sentiment
curl -X POST http://localhost:8004/api/v1/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This is absolutely incredible!",
      "Best theatre experience ever!",
      "I love how the characters respond to us!"
    ]
  }'

# 2. Generate dialogue based on positive sentiment
curl -X POST http://localhost:8001/api/v1/dialogue/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scene_context": {
      "title": "Scene 1: The Meeting",
      "characters": ["ALICE", "BOB"],
      "setting": "A coffee shop"
    },
    "sentiment_vector": {
      "overall": "positive",
      "energy": 0.9
    }
  }'

# 3. Check safety of generated dialogue
curl -X POST http://localhost:8006/api/v1/safety/filter \
  -H "Content-Type: application/json" \
  -d '{
    "content": "BOB: [Beaming with joy] Thank you all for this wonderful energy!",
    "context": "family_show"
  }'

# 4. Adjust lighting to match positive mood
curl -X POST http://localhost:8005/api/v1/lighting/scene \
  -H "Content-Type: application/json" \
  -d '{
    "name": "energetic_warm",
    "channels": {"1": 255, "2": 255, "3": 200},
    "fade_time_ms": 2000
  }'
```

**Expected Outcome:**
- Sentiment analysis shows highly positive response
- Dialogue reflects audience enthusiasm
- Safety filter approves content
- Lighting shifts to warm, energetic tones

---

### Scenario 2: Real-Time Captioning & Accessibility (3 minutes)

**Story:** Demonstrate accessibility features.

```bash
# 1. Start WebSocket for real-time captions
# Use WebSocket client to connect to: ws://localhost:8002/api/v1/captioning/stream

# 2. Transcribe sample audio
curl -X POST http://localhost:8002/api/v1/captioning/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "<base64-audio-data>",
    "language": "en",
    "timestamps": true,
    "word_timestamps": true
  }'

# 3. Translate captions to BSL gloss
curl -X POST http://localhost:8003/api/v1/gloss/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to our interactive performance. Please share your thoughts using #ChimeraShow",
    "include_metadata": true
  }'
```

**Expected Outcome:**
- Real-time transcription with timestamps
- BSL gloss format ready for sign language interpreter
- Accessibility metadata included

---

### Scenario 3: The Complete Pipeline (10 minutes)

**Story:** End-to-end flow from audience input to stage adaptation.

```bash
# Step 1: Simulate audience social media posts
SOCIAL_POSTS=(
    "This plot twist is amazing! #ChimeraShow"
    "I can't believe they just did that!"
    "More energy please!"
)

# Step 2: Analyze sentiment
curl -X POST http://localhost:8004/api/v1/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"texts\": [\"${SOCIAL_POSTS[0]}\", \"${SOCIAL_POSTS[1]}\", \"${SOCIAL_POSTS[2]}\"]}"

# Step 3: Orchestrate through OpenClaw
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "sentiment_to_dialogue",
    "input": {
      "social_posts": ["This plot twist is amazing!", "More energy please!"]
    },
    "context": {"scene_id": "scene-003"}
  }'

# Step 4: Check operator console for alerts
curl http://localhost:8007/api/v1/console/alerts

# Step 5: Approve pending actions
curl -X POST http://localhost:8007/api/v1/console/approvals/approval-001 \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve", "notes": "Matches audience enthusiasm"}'
```

---

### Scenario 4: Monitoring & Observability (5 minutes)

**Story:** Show how we monitor the system in real-time.

```bash
# 1. Access Grafana dashboards
open http://localhost:3000
# Login: admin/chimera

# 2. Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# 3. View distributed traces
open http://localhost:16686

# 4. Check service health
curl http://localhost:8000/health/live
curl http://localhost:8001/health/live
curl http://localhost:8004/health/live
```

**Key Dashboards to Show:**
- Service Health Overview
- Request Latency by Service
- Sentiment Analysis Trends
- Safety Filter Statistics
- Lighting Control Status

---

## Next Steps for Students

### Role Assignments

Each student owns one component. See `docs/STUDENT_ROLES.md` for details.

| # | Role | Service | First Task |
|---|------|---------|------------|
| 1 | OpenClaw Orchestrator Lead | `openclaw-orchestrator` | Review skill registry, test routing |
| 2 | SceneSpeak Agent Lead | `SceneSpeak Agent` | Test dialogue generation, review prompts |
| 3 | Captioning Agent Lead | `Captioning Agent` | Test transcription, accuracy analysis |
| 4 | BSL Translation Lead | `bsl-text2gloss-agent` | Test translation quality, gloss format |
| 5 | Sentiment Analysis Lead | `Sentiment Agent` | Test sentiment analysis, model tuning |
| 6 | Lighting Control Lead | `lighting-control` | Test DMX output, scene presets |
| 7 | Safety Filter Lead | `safety-filter` | Review filter rules, test edge cases |
| 8 | Operator Console Lead | `operator-console` | Test approval workflow, dashboard UI |
| 9 | Infrastructure Lead | `infrastructure/` | Monitor cluster, resource allocation |
| 10 | QA & Documentation Lead | `tests/`, `docs/` | Run tests, update documentation |

### Your First Week Checklist

**For All Students:**
- [ ] Complete environment setup (`make bootstrap`)
- [ ] Read your component's README.md
- [ ] Run component tests (`make test-unit`)
- [ ] Access component via port-forward
- [ ] Make your first API call to your service
- [ ] Join team chat channels

**Component-Specific:**
- [ ] Understand component architecture
- [ ] Identify one improvement to make
- [ ] Create first feature branch
- [ ] Submit first PR for review

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/<component>-<feature-name>

# 2. Make changes to your component
cd services/<your-service>/
# Edit files...

# 3. Run tests
make test-unit

# 4. Format and lint
make format
make lint

# 5. Build and test your service
docker build -t localhost:30500/project-chimera/<service>:test .

# 6. Commit and push
git add .
git commit -m "feat(<service>): description of changes"
git push origin feature/<component>-<feature-name>

# 7. Create pull request on GitHub
```

---

## Troubleshooting

### Common Issues

#### 1. k3s won't start

```bash
# Check k3s status
sudo systemctl status k3s

# View logs
journalctl -u k3s -n 50

# Restart k3s
sudo systemctl restart k3s
```

#### 2. Pods stuck in Pending state

```bash
# Check pod status
kubectl get pods -A

# Describe pod to see why
kubectl describe pod <pod-name> -n <namespace>

# Common issues:
# - ImagePullBackOff: Check registry is accessible
# - Insufficient resources: Check CPU/memory available
```

#### 3. ImagePullBackOff errors

**Option 1: Configure k3s for insecure registry**
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

**Option 2: Load images directly into k3s**
```bash
docker save localhost:30500/project-chimera/<service>:latest -o <service>.tar
sudo k3s ctr images import <service>.tar
rm <service>.tar
```

#### 4. Cannot connect to service

```bash
# Verify service exists
kubectl get svc -n live

# Port forward to local
kubectl port-forward -n live svc/<service-name> <local-port>:<service-port>

# Test connection
curl http://localhost:<local-port>/health
```

#### 5. Port already in use

```bash
# Find what's using the port
sudo lsof -i :<port>

# Kill port-forwards
pkill -f "port-forward"

# Or kill specific process
kill <PID>
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

1. **Check documentation:**
   - `getting-started/quick-start.md`
   - `docs/` folder
   - `reference/runbooks/`
   - `docs/plans/IMPLEMENTATION_DOCUMENTATION.md`

2. **Search existing issues:**
   - GitHub Issues: https://github.com/project-chimera/main/issues

3. **Ask in team chat:**
   - Tag @technical-lead for urgent issues

4. **Create a new issue:**
   - Use the issue template
   - Include: error messages, steps to reproduce, environment details

---

## Quick Reference

### Essential Make Commands

```bash
make bootstrap           # Automated setup
make bootstrap-status    # Check deployment status
make bootstrap-destroy   # Remove k3s cluster
make test               # Run all tests
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-load          # Load tests
make format             # Format code
make lint               # Lint code
make run-openclaw       # Port forward OpenClaw
make logs               # View logs
make logs-all           # View all logs
```

### Service Health Endpoints

```bash
curl http://localhost:8000/health/live  # OpenClaw
curl http://localhost:8001/health/live  # SceneSpeak
curl http://localhost:8002/health/live  # Captioning
curl http://localhost:8003/health/live  # BSL
curl http://localhost:8004/health/live  # Sentiment
curl http://localhost:8005/health/live  # Lighting
curl http://localhost:8006/health/live  # Safety
curl http://localhost:8007/health/live  # Operator
```

### Monitoring URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/chimera |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |

### Useful Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `getting-started/quick-start.md` | Setup guide |
| `docs/STUDENT_ROLES.md` | Role assignments |
| `reference/api.md` | Complete API reference |
| `docs/reference/architecture.md` | System architecture |
| `Makefile` | Build automation |
| `scripts/bootstrap/` | Bootstrap scripts for k3s setup |

---

## What Makes This Special

### Technical Highlights

1. **Microservices Architecture** - 8 independent, scalable services
2. **Event-Driven** - Kafka-based event streaming
3. **Vector-Based Matching** - Milvus for semantic skill routing
4. **GPU Scheduling** - Intelligent resource allocation
5. **Safety-First** - Multi-layer content moderation
6. **Accessibility** - Built-in captioning and BSL translation
7. **Observability** - Complete monitoring stack

### Student Learning Opportunities

- **AI/ML** - LLM fine-tuning, sentiment analysis, speech recognition
- **Backend Development** - FastAPI, microservices, event streaming
- **Infrastructure** - Kubernetes, Docker, monitoring
- **DevOps** - CI/CD, deployment automation
- **Frontend** - Real-time dashboards, WebSocket interfaces
- **Testing** - Unit, integration, load, and security testing
- **Accessibility** - Captioning, translation, inclusive design

### Real-World Impact

- **Universities** - Free AI theatre platform for education
- **Theatre Companies** - Innovative performance experiences
- **Researchers** - AI and creativity research platform
- **Students** - Hands-on experience with cutting-edge tech

---

## Congratulations!

You've just seen a complete, production-ready (alpha) AI-powered live theatre platform built from scratch. This is what students will be developing, improving, and innovating on.

### Key Stats

- **8 Microservices** - All with health checks, metrics, and tracing
- **3 Infrastructure Services** - Redis, Kafka, Milvus
- **3 Monitoring Tools** - Prometheus, Grafana, Jaeger
- **50+ API Endpoints** - Fully documented and tested
- **1000+ Lines of Tests** - Unit, integration, load, red-team
- **Complete Documentation** - Architecture, API, deployment, runbooks
- **Kubernetes-Ready** - k3s for local, production-ready for cloud

### What's Next?

Students will:
1. Pick their component based on role assignment
2. Set up development environment
3. Learn their component inside and out
4. Make improvements and add features
5. Test thoroughly
6. Deploy to production
7. Present their work

---

**Welcome to Project Chimera! Let's build something amazing together.**

For questions, support, or to get involved, please:
- Open an issue: https://github.com/project-chimera/main/issues
- Start a discussion: https://github.com/project-chimera/main/discussions
- Contact the Technical Lead

---

*Generated: February 27, 2026*
*Version: v0.1.0 (Alpha)*
*Status: Ready for Student Development*
