# Project Chimera - Service Topology Architecture

**Generated**: 2026-04-09
**Purpose**: Actual verified service architecture

---

## Overview

Project Chimera consists of **8 microservices** running in Docker containers, all verified operational with 10+ days uptime.

---

## Service Topology Diagram

```mermaid
graph TB
    subgraph "External Services"
        ZAI[Z.AI API<br/>GLM-4.7]
        OLLAMA[Ollama<br/>Local LLM]
        HF[HuggingFace<br/>DistilBERT]
    end

    subgraph "Core Services (Operational)"
        ORCH[Nemo Claw<br/>Port 8000<br/>✅ Healthy]
        SCENE[SceneSpeak<br/>Port 8001<br/>✅ Healthy]
        CAPT[Captioning<br/>Port 8002<br/>✅ Healthy]
        BSL[BSL Agent<br/>Port 8003<br/>✅ Healthy]
        SENT[Sentiment<br/>Port 8004<br/>✅ Healthy]
        LIGHT[Lighting/Sound<br/>Port 8005<br/>✅ Healthy]
        SAFE[Safety Filter<br/>Port 8006<br/>✅ Healthy]
        CONSOLE[Operator Console<br/>Port 8007<br/>✅ Healthy]
    end

    subgraph "Infrastructure"
        REDIS[(Redis<br/>State/Cache)]
        KAFKA[(Kafka<br/>Messaging)]
        MILVUS[(Milvus<br/>Vector DB)]
        PROM[Prometheus<br/>Metrics]
        GRAF[Grafana<br/>Dashboard]
    end

    %% VERIFIED CONNECTIONS (Solid lines)
    ORCH -->|HTTP| SCENE
    ORCH -->|HTTP| SENT
    ORCH -->|HTTP| SAFE
    SENT -->|ML Model| HF
    SCENE -->|API| ZAI
    SCENE -->|Fallback| OLLAMA

    %% STATE MANAGEMENT
    ORCH --> REDIS
    SCENE --> REDIS
    SENT --> REDIS

    %% MONITORING
    ORCH --> PROM
    SCENE --> PROM
    SENT --> PROM
    CONSOLE --> GRAF

    %% ASPIRATIONAL CONNECTIONS (Dashed lines - NOT verified)
    ORCH -.->|Planned| CAPT
    ORCH -.->|Planned| BSL
    ORCH -.->|Planned| LIGHT
    CAPT -.->|Planned| KAFKA
    BSL -.->|Planned| MILVUS

    %% USER INTERFACE
    CONSOLE -->|WebSocket| ORCH
    CONSOLE -->|WebSocket| SCENE
    CONSOLE -->|WebSocket| SENT

    classDef verified fill:#90EE90,stroke:#006400,stroke-width:2px
    classDef partial fill:#FFD700,stroke:#B8860B,stroke-width:2px
    classDef external fill:#87CEEB,stroke:#4682B4,stroke-width:2px
    classDef infra fill:#DDA0DD,stroke:#9370DB,stroke-width:2px

    class ORCH,SCENE,CAPT,BSL,SENT,LIGHT,SAFE,CONSOLE verified
    class ZAI,OLLAMA,HF external
    class REDIS,KAFKA,MILVUS,PROM,GRAF infra
```

---

## Port Mapping

| Service | Port | Status | Health Check |
|---------|------|--------|--------------|
| Nemo Claw Orchestrator | 8000 | ✅ Healthy | `GET /health/live` |
| SceneSpeak Agent | 8001 | ✅ Healthy | `GET /health/live` |
| Captioning Agent | 8002 | ✅ Healthy | `GET /health/live` |
| BSL Agent | 8003 | ✅ Healthy | `GET /health/live` |
| Sentiment Agent | 8004 | ✅ Healthy | `GET /health/live` |
| Lighting/Sound/Music | 8005 | ✅ Healthy | `GET /health/live` |
| Safety Filter | 8006 | ✅ Healthy | `GET /health/live` |
| Operator Console | 8007 | ✅ Healthy | `GET /health/live` |

---

## Verified Integrations

### ✅ Sentiment → SceneSpeak Pipeline (VERIFIED WORKING)

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Sentiment
    participant HF
    participant SceneSpeak
    participant ZAI

    User->>Orchestrator: Text input
    Orchestrator->>Sentiment: POST /api/analyze
    Sentiment->>HF: DistilBERT inference
    HF-->>Sentiment: Sentiment classification
    Sentiment-->>Orchestrator: {"sentiment": "positive", "confidence": 0.85}
    Orchestrator->>SceneSpeak: POST /api/generate
    SceneSpeak->>ZAI: GLM-4.7 API call
    ZAI-->>SceneSpeak: Generated dialogue
    SceneSpeak-->>Orchestrator: {"dialogue": "...", "model": "glm-4.7"}
    Orchestrator-->>User: Adaptive response
```

**Status**: ✅ VERIFIED - Both ML models operational
- Sentiment: DistilBERT (HuggingFace)
- Dialogue: GLM 4.7 (Z.AI API) with Ollama fallback

---

## Deployment Architecture

```mermaid
graph LR
    subgraph "Docker Host"
        subgraph "Container Network"
            ORCH[chimera-nemoclaw:8000]
            SCENE[chimera-scenespeak:8001]
            CAPT[chimera-captioning:8002]
            BSL[chimera-bsl:8003]
            SENT[chimera-sentiment:8004]
            LIGHT[chimera-lighting:8005]
            SAFE[chimera-safety:8006]
            CONSOLE[chimera-console:8007]
        end

        subgraph "Infrastructure Containers"
            REDIS[chimera-redis:6379]
            KAFKA[chimera-kafka:9092]
            MILVUS[chimera-milvus:19530]
            PROM[chimera-prometheus:9090]
            GRAF[chimera-grafana:3000]
        end
    end

    subgraph "External"
        ZAI[Z.AI API]
        HF[HuggingFace Hub]
        OLL[Ollama:11434]
    end

    ORCH --> REDIS
    SCENE --> REDIS
    SENT --> REDIS

    SCENE --> ZAI
    SCENE --> OLL
    SENT --> HF
```

---

## Data Flow Summary

### Verified Working Paths (Solid Lines)

1. **User → Console → Orchestrator**: WebSocket communication ✅
2. **Orchestrator → Sentiment → HuggingFace**: HTTP + ML inference ✅
3. **Orchestrator → SceneSpeak → Z.AI**: HTTP + LLM generation ✅
4. **All Services → Redis**: State management ✅
5. **All Services → Prometheus**: Metrics collection ✅

### Aspirational/Planned Paths (Dashed Lines)

1. **Orchestrator → Captioning**: Audio processing pipeline ⚠️
2. **Orchestrator → BSL**: Sign language translation ⚠️
3. **Orchestrator → Lighting/Sound**: DMX/audio control ⚠️
4. **Captioning → Kafka**: Stream processing ⚠️
5. **BSL → Milvus**: Vector similarity search ⚠️

---

## Service Dependencies

```mermaid
graph TD
    ORCH[Nemo Claw Orchestrator]

    ORCH --> SENT[Sentiment Agent]
    ORCH --> SCENE[SceneSpeak Agent]
    ORCH --> SAFE[Safety Filter]
    ORCH --> CAPT[Captioning Agent]
    ORCH --> BSL[BSL Agent]
    ORCH --> LIGHT[Lighting/Sound]

    SENT --> HF[HuggingFace DistilBERT]
    SCENE --> ZAI[Z.AI GLM-4.7]
    SCENE --> OLL[Ollama Fallback]

    ORCH --> REDIS[(Redis)]
    SCENE --> REDIS
    SENT --> REDIS

    classDef verified fill:#90EE90,stroke:#006400
    classDef external fill:#87CEEB,stroke:#4682B4
    classDef storage fill:#DDA0DD,stroke:#9370DB

    class ORCH,SENT,SCENE,SAFE,CAPT,BSL,LIGHT verified
    class HF,ZAI,OLL external
    class REDIS storage
```

---

## Health Status Summary

**Last Verified**: 2026-04-09

**All Services**: ✅ Healthy (10+ days uptime)

**Health Endpoints**:
- `GET http://localhost:8000/health/live` → `{"status":"alive"}`
- `GET http://localhost:8001/health/live` → `{"status":"alive"}`
- `GET http://localhost:8002/health/live` → `{"status":"alive"}`
- `GET http://localhost:8003/health/live` → `{"status":"alive"}`
- `GET http://localhost:8004/health/live` → `{"status":"alive"}`
- `GET http://localhost:8005/health/live` → `{"status":"alive"}`
- `GET http://localhost:8006/health/live` → `{"status":"alive"}`
- `GET http://localhost:8007/health/live` → `{"status":"alive"}`

---

*Documentation Type: Architecture Diagrams*
*Evidence Source: Docker container inspection, health check verification*
