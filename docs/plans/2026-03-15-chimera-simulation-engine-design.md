# Chimera Simulation Engine Design Document

**Version:** 1.0
**Date:** March 15, 2026
**Status:** Design Phase - Pending Approval
**Author:** Project Chimera Team

---

## Executive Summary

This document outlines the design for a **Chimera-native simulation engine** inspired by BaiFu ecosystem patterns (BettaFish, MiroFish, OASIS) but built with clean-room implementation to avoid licensing restrictions and data sovereignty concerns.

### Vision Statement

Build a production-grade swarm intelligence simulation platform that:
1. Enables "what-if" scenario testing for live theatre and policy decisions
2. Uses multi-agent debate (ForumEngine pattern) for robust evaluation
3. Maintains data sovereignty with local graph storage (no cloud dependencies)
4. Controls costs through tiered LLM routing
5. Integrates seamlessly with existing Project Chimera services

### Key Differentiators from BaiFu

| Aspect | BaiFu/MiroFish | Chimera Simulation Engine |
|--------|---------------|---------------------------|
| **Licensing** | GPL-2.0 + commercial ban / AGPL-3.0 | MIT/Apache-2.0 (permissive) |
| **Memory Storage** | Zep Cloud (SaaS) | Local Neo4j + pgvector |
| **Cost Control** | Unbounded LLM API calls | Tiered routing with local LLMs |
| **Data Sovereignty** | Third-party dependency | Full local control |
| **Integration** | Standalone ecosystem | Native Chimera integration |

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow & Integration](#data-flow--integration)
4. [Technology Stack](#technology-stack)
5. [API Specification](#api-specification)
6. [Deployment Architecture](#deployment-architecture)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Risk Mitigation](#risk-mitigation)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Project Chimera                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │ Sentiment    │    │   Visual      │    │   Simulation     │   │
│   │   Agent      │───▶│    Core       │───▶│     Engine      │   │
│   │  (8004)      │    │   (8014)      │    │     (8016)       │   │
│   └─────────────┘    └──────────────┘    └──────────────────┘   │
│          │                   │                      │              │
│          ▼                   ▼                      ▼              │
│   ┌────────────────────────────────────────────────────────────┐ │
│   │               OpenClaw Orchestrator (8000)                │ │
│   │                   Task Routing & Coordination              │ │
│   └────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Five-Stage Pipeline

```
Seed Documents (BettaFish reports, LTX scripts, policy docs)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: KNOWLEDGE GRAPH CONSTRUCTION                     │
│ • GraphRAG entity extraction                               │
│ • Neo4j graph storage (local)                              │
│ • pgvector embeddings                                      │
│ • Temporal fact management (valid_at/invalid_at)           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: ENVIRONMENT SETUP                                 │
│ • Agent Profile Generator (MBTI + demographics)            │
│ • Persona template library                                 │
│ • Initial state distribution                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: SIMULATION EXECUTION                              │
│ • OASIS-inspired parallel simulation                       │
│ • Tiered LLM routing (vLLM for agents, Claude for critical) │
│ • SQLite trace logging                                     │
│ • Action type system (23 social actions)                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: REPORT GENERATION                                 │
│ • ForumEngine multi-agent debate                           │
│ • ReACT-pattern ReportAgent                                │
│ • Consensus synthesis                                     │
│ • Confidence interval calculation                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: DEEP INTERACTION                                  │
│ • IPC bridge for agent queries                             │
│ • Agent state persistence                                  │
│ • Interview mode                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Knowledge Graph Construction (Stage 1)

**Purpose:** Extract entities, relationships, and temporal facts from seed documents.

**Components:**

```python
# graph/builder.py
class GraphBuilder:
    """Builds knowledge graph from seed documents using GraphRAG"""

    async def build_from_documents(self, documents: List[str]) -> Graph:
        """Extract entities and relationships"""
        pass

    async def create_temporal_facts(self, facts: List[Fact]) -> None:
        """Create facts with validity windows"""
        pass

# graph/neo4j_client.py
class Neo4jClient:
    """Local Neo4j graph database client"""

    async def create_entity(self, entity: Entity) -> None:
        """Create or update entity node"""
        pass

    async def create_relationship(self, rel: Relationship) -> None:
        """Create relationship between entities"""
        pass

# graph/pgvector_client.py
class PgvectorClient:
    """Vector embedding storage"""

    async def store_embedding(self, text: str, embedding: List[float]) -> None:
        """Store text embedding"""
        pass

    async def similarity_search(self, query: List[float], k: int) -> List[str]:
        """Find similar documents by embedding"""
        pass
```

**Data Model:**

```python
@dataclass
class Entity:
    id: str
    type: EntityType  # PERSON, ORGANIZATION, LOCATION, EVENT, etc.
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime]

@dataclass
class Relationship:
    source: str
    target: str
    type: RelationType  # KNOWS, WORKS_FOR, LOCATED_IN, etc.
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime]

@dataclass
class Fact:
    subject: str
    predicate: str
    object: str
    confidence: float
    valid_at: datetime
    invalid_at: Optional[datetime]
```

### 2. Environment Setup (Stage 2)

**Purpose:** Generate agent personas with unique characteristics.

```python
# agents/profile.py
class AgentProfile:
    """Agent persona definition"""

    mbti: MBTIType  # INTJ, ENFP, etc.
    demographics: Demographics
    behavioral_logic: BehavioralProfile
    information_sources: List[DataSource]
    memory_capacity: int

# agents/persona.py
class PersonaGenerator:
    """Generate diverse agent personas"""

    async def generate_population(
        self,
        count: int,
        diversity_config: DiversityConfig
    ) -> List[AgentProfile]:
        """Generate N diverse agent profiles"""
        pass
```

### 3. Simulation Execution (Stage 3)

**Purpose:** Run parallel agent simulation with cost-conscious LLM routing.

```python
# simulation/runner.py
class SimulationRunner:
    """OASIS-inspired simulation orchestrator"""

    async def run_simulation(
        self,
        agents: List[AgentProfile],
        knowledge_graph: Graph,
        config: SimulationConfig
    ) -> SimulationResult:
        """Execute simulation rounds"""
        pass

# simulation/tiered_router.py
class TieredLLMRouter:
    """Route LLM calls based on cost and criticality"""

    async def route_decision(self, context: DecisionContext) -> LLMBackend:
        """Decide which LLM to use"""
        # Tier 1: Local vLLM (Llama 3 8B, Qwen 7B) - 95% of calls
        # Tier 2: API (Claude 3.5 Haiku, GPT-4o-mini) - 4% of calls
        # Tier 3: Frontier (Claude 3.5 Sonnet, GPT-4o) - 1% of calls
        pass
```

**Action Type System:**

```python
class ActionType(Enum):
    """Social action types from OASIS framework"""
    POST = "post"
    REPLY = "reply"
    RETWEET = "retweet"
    QUOTE = "quote"
    LIKE = "like"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    BLOCK = "block"
    MUTE = "mute"
    DIRECT_MESSAGE = "direct_message"
    # ... 13 more actions
```

### 4. Report Generation (Stage 4)

**Purpose:** Generate consensus reports through multi-agent debate.

```python
# reporting/forum_engine.py
class ForumEngine:
    """Multi-agent debate for consensus building"""

    async def debate_topic(
        self,
        topic: str,
        participants: List[Agent],
        rounds: int = 3
    ) -> DebateResult:
        """Facilitate structured debate"""
        pass

# reporting/react_agent.py
class ReACTReportAgent:
    """Report generation using ReACT pattern"""

    async def generate_report(
        self,
        simulation_trace: SimulationTrace,
        knowledge_graph: Graph
    ) -> Report:
        """Generate comprehensive report"""
        pass
```

**ForumEngine Debate Pattern:**

```
Round 1: Each agent presents initial analysis
    ↓
Round 2: Agents critique and cross-validate
    ↓
Round 3: Agents refine based on feedback
    ↓
Consensus: Synthesize final report
```

### 5. Deep Interaction (Stage 5)

**Purpose:** Enable querying individual agents post-simulation.

```python
# agents/interaction.py
class AgentInteraction:
    """Post-simulation agent communication"""

    async def interview_agent(
        self,
        agent_id: str,
        question: str
    ) -> AgentResponse:
        """Query specific agent about their reasoning"""
        pass

    async def get_agent_memory(
        self,
        agent_id: str,
        timeframe: TimeRange
    ) -> List[Memory]:
        """Retrieve agent's memory from simulation"""
        pass
```

---

## Data Flow & Integration

### External Data Sources

```
┌──────────────────┐
│  Sentiment Agent  │───► Real-time sentiment data
│     (8004)        │
└──────────────────┘

┌──────────────────┐
│   Visual Core    │───► Video transcripts, visual context
│     (8014)        │
└──────────────────┘

┌──────────────────┐
│  BettaFish API   │───► Structured sentiment reports (optional)
│   (external)     │
└──────────────────┘

         │
         ▼
┌──────────────────────────────┐
│   Simulation Engine (8016)   │
│   Knowledge Graph Builder    │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  OpenClaw Orchestrator (8000) │
│  Task routing & coordination  │
└──────────────────────────────┘
```

### Integration with OpenClaw

```python
# skills/simulation.SKILL.md
## Simulation Skill

**Purpose:** Run agent swarm simulations for "what-if" scenario testing

**Endpoint:** `http://simulation-engine:8016/api/v1/simulate`

**Parameters:**
- `seed_documents`: List of document IDs or URLs
- `agent_count`: Number of agents (default: 100)
- `simulation_rounds`: Number of rounds (default: 10)
- `scenario_type`: Type of simulation to run

**Output:** Simulation report with confidence intervals

**Cost Estimate:** ~50K tokens per 100-agent, 10-round simulation
```

---

## Technology Stack

### Core Dependencies

```python
# requirements.txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Graph Database
neo4j==5.14.0
pgvector==0.2.5
asyncpg==0.29.0

# LLM Clients
openai==1.12.0
anthropic==0.18.0
vllm==0.6.0  # For local LLM serving

# Simulation
camel-oasis==0.2.5
camel-ai==0.2.78

# Observability
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
prometheus-client==0.19.0

# Data Processing
numpy==1.26.2
pandas==2.2.0
```

### Storage Architecture

| Component | Technology | Purpose |
|-----------|-------------|---------|
| Graph Storage | Neo4j 5.x | Entity/relationship graph |
| Vector Storage | pgvector | Embedding similarity search |
| Trace Storage | SQLite | Simulation action logs |
| State Storage | Redis | Caching and coordination |

---

## API Specification

### Core Endpoints

```yaml
# Knowledge Graph
POST /api/v1/graph/build
  Body: { "documents": ["string"] }
  Response: { "graph_id": "string", "entities": int, "relationships": int }

GET /api/v1/graph/{graph_id}
  Response: GraphDetails

# Simulation
POST /api/v1/simulate
  Body: SimulationConfig
  Response: { "simulation_id": "string", "status": "running" }

GET /api/v1/simulation/{simulation_id}/status
  Response: SimulationStatus

GET /api/v1/simulation/{simulation_id}/result
  Response: SimulationResult

# Agent Interaction
POST /api/v1/agent/{agent_id}/interview
  Body: { "question": "string" }
  Response: AgentResponse

# Reporting
POST /api/v1/report/generate
  Body: { "simulation_id": "string", "format": "markdown|pdf|json" }
  Response: Report
```

---

## Deployment Architecture

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: simulation-engine-config
data:
  GRAPH_DB_URL: "bolt://neo4j:7687"
  VECTOR_DB_URL: "postgresql+asyncpg://user:pass@pgvector:5432/chimera"
  LOCAL_LLM_URL: "http://vllm:8000"
  SIMULATION_MAX_AGENTS: "1000"
  ENABLE_FORUM_DEBATE: "true"
---
apiVersion: v1
kind: Secret
metadata:
  name: simulation-engine-secrets
type: Opaque
stringData:
  ANTHROPIC_API_KEY: <base64>
  OPENAI_API_KEY: <base64>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simulation-engine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: simulation-engine
  template:
    metadata:
      labels:
        app: simulation-engine
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: simulation-engine
        image: simulation-engine:latest
        ports:
        - containerPort: 8016
        env:
        - name: GRAPH_DB_URL
          valueFrom:
            configMapKeyRef:
              name: simulation-engine-config
              key: GRAPH_DB_URL
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8016
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8016
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: simulation-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: simulation-engine
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Local Development

```bash
# docker-compose.yml
version: '3.8'

services:
  simulation-engine:
    build: .
    ports:
      - "8016:8016"
    environment:
      - GRAPH_DB_URL=bolt://neo4j:7687
      - VECTOR_DB_URL=postgresql+asyncpg://postgres:password@pgvector:5432/chimera
      - LOCAL_LLM_URL=http://vllm:8000
    depends_on:
      - neo4j
      - pgvector
      - vllm

  neo4j:
    image: neo4j:5.14.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password

  pgvector:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=chimera

  vllm:
    image: vllm/vllm-openai:v0.6.0
    ports:
      - "8000:8000"
    command: >
      --model meta-llama/Meta-Llama-3-8B-Instruct
      --quantization awq
```

---

## Implementation Roadmap

### Phase 0: Validation (Weeks 1-2)

**Objective:** Prove the architecture works

- [ ] Set up local Neo4j + pgvector
- [ ] Implement basic GraphBuilder
- [ ] Create 5-agent test simulation
- [ ] Validate cost model (track token usage)
- [ ] **Success:** 10-agent simulation completes in <5 minutes

### Phase 1: Foundation (Weeks 3-6)

**Objective:** Build production-grade components

- [ ] Complete GraphBuilder with temporal facts
- [ ] Implement PersonaGenerator with MBTI profiles
- [ ] Build ForumEngine debate system
- [ ] Create ReACT ReportAgent
- [ ] Add OpenTelemetry tracing
- [ ] **Success:** 100-agent simulation with debate validation

### Phase 2: Integration (Weeks 7-10)

**Objective:** Integrate with Chimera ecosystem

- [ ] Connect to Sentiment Agent for real-time data
- [ ] Create OpenClaw skill for simulation
- [ ] Implement IPC agent interaction
- [ ] Add PDF report generation
- [ ] **Success:** End-to-end pipeline from sentiment to simulation

### Phase 3: Production (Weeks 11+)

**Objective:** Production hardening

- [ ] Kubernetes deployment with security policies
- [ ] Tiered LLM routing with vLLM
- [ ] Cost monitoring and alerts
- [ ] Runbook documentation
- [ ] **Success:** 1,000-agent simulation with <10M tokens used

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|-------|------------|
| **Cost Overrun** | High | High | Tiered routing, local LLMs, strict budgets |
| **Licensing** | Low | High | Clean-room implementation, permissive licenses |
| **Data Sovereignty** | Low | High | Local Neo4j/pgvector, no cloud dependencies |
| **Herd Behavior** | Medium | Medium | Calibrate against historical data, disclose uncertainty |
| **Scalability** | Medium | Medium | Horizontal pod autoscaling, queue-based architecture |
| **Simulation Accuracy** | High | Medium | Validation framework, backtesting against known outcomes |

---

## Acceptance Criteria

### Phase 0 (Validation)

- [ ] Can build knowledge graph from sample document
- [ ] Can generate 10 diverse agent profiles
- [ ] Can run 5-round simulation with those agents
- [ ] Can generate basic report
- [ ] Token usage tracked and within budget

### Phase 1 (Foundation)

- [ ] All 5 stages implemented and tested
- [ ] Unit tests for each component (80%+ coverage)
- [ ] Integration tests for data flow
- [ ] ForumEngine produces consensus in 3 rounds
- [ ] Reports include confidence intervals

### Phase 2 (Integration)

- [ ] OpenClaw skill works end-to-end
- [ ] Can query agents post-simulation
- [ ] PDF reports generated correctly
- [ ] E2E tests pass (5 scenarios)

---

## Conclusion

This design provides a **clean-room implementation** of BaiFu-inspired patterns while avoiding the critical blockers:

1. ✅ **No licensing risk** - MIT/Apache-2.0 licenses
2. ✅ **Data sovereignty** - Local graph storage
3. ✅ **Cost control** - Tiered LLM routing
4. ✅ **Production ready** - Security, monitoring, scalability

### Next Steps

1. **Review and approve this design** with stakeholders
2. **Create implementation plan** with detailed tasks
3. **Begin Phase 0 validation** immediately

---

**Document Status:** Ready for Review
**Next Review:** After Phase 0 completion
**Owner:** Project Chimera Team
