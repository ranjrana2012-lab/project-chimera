# Project Chimera - Data Flow Architecture

**Generated**: 2026-04-09
**Purpose**: Document verified data flows vs. aspirational flows

---

## Legend

- **Solid Green Line (→)**: Verified working integration
- **Dashed Yellow Line (-->)**: Partially implemented / Not verified
- **Dotted Red Line (...)**: Aspirational / Not implemented

---

## Complete Data Flow Diagram

```mermaid
flowchart TB
    subgraph "User Interface Layer"
        USER[👤 User]
        CONSOLE[Operator Console<br/>Port 8007<br/>React Dashboard]
    end

    subgraph "Orchestration Layer"
        ORCH[Nemo Claw Orchestrator<br/>Port 8000<br/>State Machine]
    end

    subgraph "AI Services Layer"
        SENT[Sentiment Agent<br/>Port 8004<br/>DistilBERT ML]
        SCENE[SceneSpeak Agent<br/>Port 8001<br/>GLM-4.7 LLM]
        CAPT[Captioning Agent<br/>Port 8002<br/>Whisper ASR]
        BSL[BSL Agent<br/>Port 8003<br/>Dictionary Translation]
    end

    subgraph "Safety & Control Layer"
        SAFE[Safety Filter<br/>Port 8006<br/>Pattern Matching]
        LIGHT[Lighting/Sound<br/>Port 8005<br/>DMX/Audio Control]
    end

    subgraph "External ML/AI"
        HF[HuggingFace<br/>DistilBERT Model]
        ZAI[Z.AI API<br/>GLM-4.7]
        OLL[Ollama<br/>Local LLM]
    end

    subgraph "Data Storage"
        REDIS[(Redis<br/>State/Cache)]
        KAFKA[(Kafka<br/>Message Queue)]
        MILVUS[(Milvus<br/>Vector DB)]
    end

    %% VERIFIED FLOWS (Solid Green)
    USER -->|WebSocket| CONSOLE
    CONSOLE -->|WebSocket| ORCH
    ORCH -->|HTTP POST| SENT
    SENT -->|Inference| HF
    HF -->|Classification| SENT
    SENT -->|HTTP Response| ORCH
    ORCH -->|HTTP POST| SCENE
    SCENE -->|API Call| ZAI
    SCENE -->|Fallback| OLL
    ZAI -->|Dialogue| SCENE
    OLL -->|Dialogue| SCENE
    SCENE -->|HTTP Response| ORCH
    ORCH -->|WebSocket| CONSOLE
    CONSOLE -->|Update| USER

    ORCH -->|Read/Write| REDIS
    SCENE -->|Cache| REDIS
    SENT -->|Cache| REDIS

    ORCH -->|Metrics| PROM[Prometheus]
    SCENE -->|Metrics| PROM
    SENT -->|Metrics| PROM

    %% PARTIAL/UNVERIFIED FLOWS (Dashed Yellow)
    ORCH -.->|Planned| SAFE
    ORCH -.->|Planned| CAPT
    ORCH -.->|Planned| BSL
    ORCH -.->|Planned| LIGHT

    CAPT -.->|Not Verified| KAFKA
    BSL -.->|Not Verified| MILVUS

    %% STYLE DEFINITIONS
    classDef verified fill:#90EE90,stroke:#006400,stroke-width:3px
    classDef partial fill:#FFD700,stroke:#B8860B,stroke-width:2px,stroke-dasharray: 5 5
    classDef external fill:#87CEEB,stroke:#4682B4,stroke-width:2px
    classDef storage fill:#DDA0DD,stroke:#9370DB,stroke-width:2px
    classDef ui fill:#F0E68C,stroke:#DAA520,stroke-width:2px

    class USER,CONSOLE ui
    class ORCH,SENT,SCENE verified
    class SAFE,CAPT,BSL,LIGHT partial
    class HF,ZAI,OLL external
    class REDIS,KAFKA,MILVUS,PROM storage
```

---

## Verified Pipeline: Sentiment → Adaptive Dialogue

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 User
    participant C as Console (8007)
    participant O as Orchestrator (8000)
    participant S as Sentiment (8004)
    participant H as 🤗 HuggingFace
    participant SC as SceneSpeak (8001)
    participant Z as 🧠 Z.AI GLM-4.7
    participant R as Redis

    U->>C: "I love this performance!"
    C->>O: WebSocket message

    Note over O: State: Processing Input

    O->>R: Save input to state
    R-->>O: ACK

    O->>S: POST /api/analyze<br/>{"text": "I love this performance!"}

    Note over S: ML Inference
    S->>H: DistilBERT.forward(text)
    H-->>S: sentiment="positive"<br/>confidence=0.95

    S-->>O: {"sentiment": "positive", "confidence": 0.95}

    Note over O: State: Sentiment Received

    O->>SC: POST /api/generate<br/>{"prompt": "Generate dialogue", "context": {"sentiment": "positive"}}

    Note over SC: LLM Generation
    SC->>Z: API call with Bearer token
    Z-->>SC: "Thank you for the wonderful feedback!"

    SC-->>O: {"dialogue": "Thank you...", "model": "glm-4.7"}

    Note over O: State: Response Ready
    O->>R: Update conversation state
    R-->>O: ACK

    O-->>C: WebSocket message
    C-->>U: Display response

    Note over U,Z: ✅ Pipeline Complete<br/>User receives sentiment-adaptive dialogue
```

**Status**: ✅ VERIFIED WORKING
- Round trip latency: ~2-3 seconds
- Sentiment accuracy: High (DistilBERT)
- Dialogue quality: Good (GLM-4.7)

---

## Component Interaction Matrix

| From | To | Protocol | Status | Notes |
|------|-----|----------|--------|-------|
| Console | Orchestrator | WebSocket | ✅ Verified | Real-time updates |
| Orchestrator | Sentiment | HTTP POST | ✅ Verified | REST API |
| Sentiment | HuggingFace | HTTPS | ✅ Verified | DistilBERT model |
| Orchestrator | SceneSpeak | HTTP POST | ✅ Verified | REST API |
| SceneSpeak | Z.AI | HTTPS | ✅ Verified | GLM-4.7 API |
| SceneSpeak | Ollama | HTTP | ✅ Verified | Fallback LLM |
| Orchestrator | Safety | HTTP POST | ⚠️ Partial | HTTP works, classification uses random numbers |
| Orchestrator | Captioning | HTTP POST | ⚠️ Not Verified | Infrastructure exists, not tested with audio |
| Orchestrator | BSL | HTTP POST | ⚠️ Partial | HTTP works, dictionary-based only |
| Orchestrator | Lighting | HTTP POST | ⚠️ Not Verified | HTTP works, hardware integration untested |
| All Services | Redis | TCP | ✅ Verified | State management |
| All Services | Prometheus | HTTP | ✅ Verified | Metrics collection |

---

## Request/Response Examples

### 1. Sentiment Analysis (VERIFIED)

**Request**:
```http
POST http://localhost:8004/api/analyze
Content-Type: application/json

{
  "text": "I love this performance!"
}
```

**Response**:
```json
{
  "sentiment": "positive",
  "confidence": 0.95,
  "emotion_scores": {
    "joy": 0.85,
    "sadness": 0.05
  }
}
```

### 2. Dialogue Generation (VERIFIED)

**Request**:
```http
POST http://localhost:8001/api/generate
Content-Type: application/json

{
  "prompt": "Welcome the audience!",
  "context": {
    "sentiment": "positive",
    "scene": "opening"
  }
}
```

**Response**:
```json
{
  "dialogue": "Welcome everyone! We are thrilled to have you here tonight...",
  "model": "glm-4.7",
  "latency_ms": 1250
}
```

### 3. Health Check (ALL SERVICES)

**Request**:
```http
GET http://localhost:8004/health/live
```

**Response**:
```json
{
  "status": "alive"
}
```

---

## State Management Flow

```mermaid
graph LR
    ORCH[Orchestrator]
    REDIS[(Redis)]

    ORCH -->|SET show_state| REDIS
    ORCH -->|SET conversation_history| REDIS
    ORCH -->|SET current_sentiment| REDIS

    REDIS -->|GET show_state| ORCH
    REDIS -->|GET conversation_history| ORCH
    REDIS -->|GET current_sentiment| ORCH

    SCENE[SceneSpeak] -->|Cache prompts| REDIS
    SENT[Sentiment] -->|Cache results| REDIS

    classDef service fill:#90EE90,stroke:#006400
    classDef storage fill:#DDA0DD,stroke:#9370DB

    class ORCH,SCENE,SENT service
    class REDIS storage
```

---

## Metrics & Monitoring Flow

```mermaid
graph LR
    SERVICES[All Services]
    PROM[Prometheus]
    GRAF[Grafana]

    SERVICES -->|POST /metrics| PROM
    SERVICES -->|/health/live| PROM

    PROM -->|Query API| GRAF
    GRAF -->|Dashboard| USER[👤 Operator]

    classDef service fill:#90EE90,stroke:#006400
    classDef infra fill:#DDA0DD,stroke:#9370DB
    classDef ui fill:#F0E68C,stroke:#DAA520

    class SERVICES service
    class PROM,GRAF infra
    class USER ui
```

---

## Async Messaging (Planned - Not Verified)

```mermaid
graph TD
    CAPT[Captioning Agent]
    KAFKA[(Kafka)]
    CONSUMER[Future Consumer]

    CAPT -.->|Planned| KAFKA
    KAFKA -.->|Planned| CONSUMER

    classDef partial fill:#FFD700,stroke:#B8860B,stroke-dasharray: 5 5
    classDef storage fill:#DDA0DD,stroke:#9370DB

    class CAPT,CONSUMER partial
    class KAFKA storage
```

---

## Summary

**Verified Working**:
- ✅ User → Console → Orchestrator → Sentiment → HuggingFace
- ✅ Orchestrator → SceneSpeak → Z.AI/Ollama
- ✅ All services → Redis (state management)
- ✅ All services → Prometheus (metrics)
- ✅ WebSocket communication (Console ↔ Orchestrator)

**Partially Implemented**:
- ⚠️ Safety Filter (HTTP works, classification mocked)
- ⚠️ BSL Agent (HTTP works, dictionary-based only)
- ⚠️ Captioning (infrastructure exists, not tested with audio)

**Not Verified**:
- ❌ Captioning → Kafka streaming
- ❌ BSL → Milvus vector search
- ❌ Lighting/Sound hardware integration
- ❌ End-to-end show workflow

---

*Documentation Type: Data Flow Architecture*
*Evidence Source: API testing, service logs, network inspection*
*Date: 2026-04-09*
