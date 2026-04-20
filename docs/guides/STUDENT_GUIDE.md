# Project Chimera - Student Guide

**Last Updated**: 2026-03-30
**Target Audience**: Students, Researchers, Developers learning the system
**Prerequisites**: Basic Python, Docker, and REST API knowledge

---

## 🎓 Learning Objectives

After completing this guide, you will understand:
1. How Project Chimera's microservices architecture works
2. How data flows between services in real-time
3. How to run and test the system locally
4. How the AI/ML components integrate
5. How to extend and modify the system

---

## 🏗️ System Architecture Overview

### High-Level Diagram

```
                    ┌─────────────────────────────────────┐
                    │      Nemo Claw Orchestrator        │
                    │         (Port 8000)                 │
                    │  - Coordinates all services         │
                    │  - Manages show state              │
                    │  - WebSocket hub for real-time      │
                    └───────────┬─────────────────────────┘
                                │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Audience    │   │   Content    │   │   Effect     │
│  Reaction    │   │   Generation │   │   Control    │
│              │   │              │   │              │
│ Sentiment    │   │ SceneSpeak   │   │ Lighting/    │
│ Agent (8004) │   │ Agent (8001) │   │ Sound (8005) │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Accessibility │
                   │                │
                   │ Captioning     │
                   │ (8002)         │
                   │ BSL Avatar     │
                   │ (8003)         │
                   └────────────────┘
```

### Data Flow Example

```
1. Audience member reacts: "This is amazing!"
   │
2. └─> POST /api/analyze {text: "This is amazing!"}
        │
        ▼
   [Sentiment Agent]
   - ML model analyzes text
   - Returns: {sentiment: "positive", score: 0.9}
   │
3. └─> WebSocket broadcast: sentiment_update
        │
        ├──> [Captioning Agent] - Generate subtitle
        ├──> [BSL Agent] - Trigger sign animation
        ├──> [Lighting Agent] - Adjust lighting
        └──> [Sound Agent] - Modify audio
```

---

## 🔬 Service Deep Dives

### 1. Nemo Claw Orchestrator (Port 8000)

**Purpose**: Central coordinator for the entire show

**Key Responsibilities**:
- Manage show state (idle, active, paused, ended)
- Broadcast state updates via WebSocket
- Coordinate agent communication
- Handle audience inputs

**Key Files**:
```
services/nemoclaw-orchestrator/
├── main.py                    # FastAPI app entry point
├── websocket/
│   ├── handlers.py            # WebSocket message handlers
│   └── manager.py             # Connection management
└── core/
    └── state_machine.py       # Show state management
```

**How to Test**:
```bash
# Health check
curl http://localhost:8000/health/live

# WebSocket connection
wscat -c ws://localhost:8000/ws/show
# Send: {"action": "start_show", "show_id": "test"}
```

---

### 2. Sentiment Agent (Port 8004)

**Purpose**: Analyze audience reactions and emotions

**Technology**:
- ML Model: DistilBERT (sentiment classification)
- Lazy loading: Model loads on first request (~5-10s)

**API Endpoint**:
```bash
POST /api/analyze
Content-Type: application/json

{
  "text": "The audience is loving this performance!"
}

Response:
{
  "sentiment": "positive",
  "score": 0.87,
  "confidence": 0.92,
  "emotions": {
    "joy": 0.75,
    "surprise": 0.15,
    "neutral": 0.10
  }
}
```

**Key Files**:
```
services/sentiment-agent/
├── src/sentiment_agent/
│   ├── main.py              # FastAPI app
│   ├── analyzer.py          # ML model wrapper
│   └── models.py            # Pydantic models
```

---

### 3. BSL Avatar Agent (Port 8003)

**Purpose**: Generate sign language animations for deaf accessibility

**Technology**:
- Converts text to NMM (Notation Movement Language)
- Real-time avatar animation

**WebSocket Protocol**:
```javascript
// Connect
ws://localhost:8003/ws/avatar

// Send animation request
{
  "action": "animate",
  "text": "Hello, welcome to the show",
  "timestamp": "2026-03-30T10:00:00Z"
}

// Response
{
  "type": "animation_update",
  "data": {
    "nmm_data": [{"coefficient": 0.5, "value": 1.0}],
    "text": "Hello, welcome to the show"
  }
}
```

---

### 4. Captioning Agent (Port 8002)

**Purpose**: Generate real-time captions/subtitles

**Features**:
- Speech-to-text processing
- Caption formatting and timing
- Multi-language support (planned)

---

### 5. SceneSpeak Agent (Port 8001)

**Purpose**: Generate dialogue for scenes and characters

**Technology**:
- LLM-based dialogue generation
- Character personality consistency
- Scene context awareness

---

## 🔌 WebSocket Communication

### Connection Pattern

All services communicate via WebSocket using a standard message format:

```javascript
{
  "type": "message_type",
  "data": { /* message-specific data */ },
  "timestamp": "2026-03-30T10:00:00Z"
}
```

### Message Types

| Type | Source | Purpose |
|------|--------|---------|
| `show_state` | Orchestrator | Current show state |
| `sentiment_update` | Sentiment Agent | New sentiment detected |
| `animation_update` | BSL Agent | New animation frame |
| `caption_update` | Captioning Agent | New caption text |
| `state_update` | Orchestrator | Generic state change |

### Example: Listening for Sentiment Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/show');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'sentiment_update') {
    console.log('Sentiment:', message.data.sentiment);
    console.log('Score:', message.data.score);

    // Trigger actions based on sentiment
    if (message.data.score > 0.8) {
      // High positive sentiment - enhance lighting
      enhanceLighting();
    }
  }
};
```

---

## 🧪 Running Tests

### Test Structure

```
tests/e2e/
├── api/                    # API contract tests
│   ├── sentiment.spec.ts
│   ├── captioning.spec.ts
│   └── ...
├── websocket/              # WebSocket tests
│   └── sentiment-updates.spec.ts
├── ui/                     # UI tests
│   └── operator-console.spec.ts
└── failures/               # Resilience tests
    └── service-failures.spec.ts
```

### Running Tests

```bash
cd tests/e2e

# All tests
npm test

# Specific category
npm test -- api/sentiment.spec.ts

# With UI (interactive)
npm test -- --ui

# With coverage
npm test -- --coverage
```

### Writing a Test

```typescript
import { test, expect } from '@playwright/test';

test('sentiment analysis works', async ({ request }) => {
  const response = await request.post('http://localhost:8004/api/analyze', {
    data: { text: 'This is amazing!' }
  });

  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toHaveProperty('sentiment');
  expect(body).toHaveProperty('score');
});
```

---

## 🛠️ Development Workflow

### 1. Make Changes

Edit service code in `services/<service-name>/`

### 2. Test Locally

```bash
# Restart affected service
docker compose restart <service-name>

# Run specific tests
cd tests/e2e
npm test -- <test-file>
```

### 3. Verify Integration

```bash
# Run full test suite
npm test

# Check all services healthy
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live | jq .
done
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: description of changes"
git push
```

---

## 📚 Key Concepts

### Microservices Communication

**Synchronous**: HTTP/REST APIs
- Used for: Direct requests, queries
- Example: `POST /api/analyze`

**Asynchronous**: WebSocket broadcasts
- Used for: Real-time updates, events
- Example: `sentiment_update` broadcast

### State Management

- Orchestrator maintains global show state
- Services subscribe to state updates
- WebSocket ensures all clients stay synchronized

### ML Model Lazy Loading

- Models load on first request (not at startup)
- Trade-off: Faster service startup vs slower first request
- Tests account for this with longer timeouts

---

## 🎯 Exercises

### Beginner

1. **Health Checks**: Verify all services are healthy
2. **Sentiment API**: Test different text inputs
3. **WebSocket**: Connect and receive show state updates

### Intermediate

1. **Add a new sentiment test**: Write a test for edge cases
2. **Modify show state**: Use WebSocket to change show state
3. **Analyze data flow**: Trace a sentiment analysis through the system

### Advanced

1. **Add a new service**: Create a simple microservice
2. **Implement a WebSocket handler**: Add custom message processing
3. **Optimize ML loading**: Implement model pre-warming

---

## 📖 Further Reading

### Architecture
- `docs/architecture/` - Detailed architecture documentation
- `DEPLOYMENT.md` - Kubernetes deployment guide
- `DOCKER.md` - Docker configuration details

### Development
- `DEVELOPMENT.md` - Development setup guide
- `tests/e2e/README.md` - E2E testing guide
- `CONTRIBUTING.md` - Contribution guidelines

### Production
- `PRODUCTION_READINESS_CHECKLIST.md` - Production readiness status
- `CHANGELOG.md` - Version history and changes

---

## 🆘 Troubleshooting

### Issue: Service won't start
```bash
# Check logs
docker compose logs <service-name>

# Check port conflicts
netstat -tuln | grep <port>

# Restart service
docker compose restart <service-name>
```

### Issue: Tests failing
```bash
# Ensure services are running
docker compose ps

# Run tests sequentially (debugging)
cd tests/e2e
NODE_ENV=test npm test --workers=1

# Run specific test with debug output
npm test -- <test-file> --debug
```

### Issue: ML model timing out
- First request to ML services takes 5-10s
- Subsequent requests are fast
- Increase timeout in test: `test.setTimeout(60000)`

---

## ✅ Checklist

Before working on Project Chimera:

- [ ] Docker and Docker Compose installed
- [ ] Repository cloned locally
- [ ] Services running: `docker compose up -d`
- [ ] All services healthy: Check health endpoints
- [ ] Tests passing: `cd tests/e2e && npm test`

---

## 🎓 Learning Path

1. **Start Here**: Read `QUICK_START.md` (5 min)
2. **Understand**: Read this Student Guide (30 min)
3. **Explore**: Run the system and test endpoints (1 hour)
4. **Test**: Run E2E tests and review code (2 hours)
5. **Extend**: Make a small change and verify it works (2 hours)

**Total Time**: ~5-6 hours for basic understanding

---

**Happy Learning! 📚✨**

For questions or issues, refer to the documentation or GitHub issues.
