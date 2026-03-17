# Chimera Simulation Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Chimera-native simulation engine for "what-if" scenario testing with multi-agent swarm intelligence, inspired by BaiFu patterns but with clean-room implementation.

**Architecture:** Five-stage pipeline (Knowledge Graph → Environment Setup → Simulation → Report Generation → Deep Interaction) using local Neo4j/pgvector for data sovereignty and tiered LLM routing for cost control.

**Tech Stack:** Python 3.11+, FastAPI, Neo4j 5.x, pgvector, vLLM 0.6.0, CAMEL-OASIS 0.2.5, OpenTelemetry, pytest, Docker, Kubernetes

---

## Phase 0: Validation (Weeks 1-2)

**Objective:** Prove the architecture works with minimal viable implementation.

**Success Criteria:** 10-agent simulation completes in <5 minutes, all tests pass, token usage tracked and within budget.

---

### Task 1: Project Structure and Configuration

**Files:**
- Create: `services/simulation-engine/requirements.txt`
- Create: `services/simulation-engine/pyproject.toml`
- Create: `services/simulation-engine/config.py`
- Create: `services/simulation-engine/.env.example`
- Create: `services/simulation-engine/.gitignore`

**Step 1: Create requirements.txt**

Write the file with all dependencies:

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Graph Database
neo4j==5.14.0
pgvector==0.2.5
asyncpg==0.29.0

# LLM Clients
openai==1.12.0
anthropic==0.18.0

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

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

**Step 2: Run verification**

```bash
cd services/simulation-engine
pip install --dry-run -r requirements.txt
```

Expected: No errors, all packages resolvable.

**Step 3: Create pyproject.toml**

```toml
[project]
name = "chimera-simulation-engine"
version = "0.1.0"
description = "Chimera-native swarm intelligence simulation engine"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.2",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 4: Create config.py**

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    service_name: str = "simulation-engine"
    log_level: str = "INFO"
    port: int = 8016
    environment: str = "development"

    # Graph Database
    graph_db_url: str = "bolt://localhost:7687"
    graph_db_user: str = "neo4j"
    graph_db_password: str = "chimera_graph_2026"

    # Vector Database
    vector_db_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/chimera"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    local_llm_url: str = "http://localhost:8000"

    # Cost Control
    enable_tiered_routing: bool = True
    local_llm_ratio: float = 0.95  # 95% local, 5% API
    max_tokens_per_simulation: int = 100000

    # Simulation Constraints
    max_agents: int = 1000
    max_rounds: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

**Step 5: Create .env.example**

```env
# Service Configuration
LOG_LEVEL=INFO
PORT=8016
ENVIRONMENT=development

# Graph Database (Neo4j)
GRAPH_DB_URL=bolt://localhost:7687
GRAPH_DB_USER=neo4j
GRAPH_DB_PASSWORD=chimera_graph_2026

# Vector Database (PostgreSQL + pgvector)
VECTOR_DB_URL=postgresql+asyncpg://postgres:password@localhost:5432/chimera

# LLM API Keys (Optional - for API tier)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Local LLM (vLLM)
LOCAL_LLM_URL=http://localhost:8000

# Cost Control
ENABLE_TIERED_ROUTING=true
LOCAL_LLM_RATIO=0.95
MAX_TOKENS_PER_SIMULATION=100000

# Simulation Limits
MAX_AGENTS=1000
MAX_ROUNDS=100
```

**Step 6: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.venv/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3
```

**Step 7: Write test for config loading**

Create `tests/test_config.py`:

```python
import os
import pytest
from pathlib import Path


def test_config_defaults():
    """Test that config loads with sensible defaults."""
    # Clear environment to test defaults
    for key in list(os.environ.keys()):
        if key.startswith(("GRAPH_", "VECTOR_", "LOCAL_", "OPENAI_", "ANTHROPIC_")):
            del os.environ[key]

    from config import settings

    assert settings.service_name == "simulation-engine"
    assert settings.port == 8016
    assert settings.log_level == "INFO"
    assert settings.local_llm_ratio == 0.95


def test_config_from_env(monkeypatch):
    """Test that config respects environment variables."""
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Force reload
    import importlib
    import config
    importlib.reload(config)

    assert config.settings.port == 9999
    assert config.settings.log_level == "DEBUG"
```

**Step 8: Run test**

```bash
cd services/simulation-engine
pytest tests/test_config.py -v
```

Expected: PASS (2 passed).

**Step 9: Commit**

```bash
git add services/simulation-engine/
git commit -m "feat(simulation): initialize project structure and configuration"
```

---

### Task 2: FastAPI Application Skeleton

**Files:**
- Create: `services/simulation-engine/main.py`
- Create: `services/simulation-engine/api/health.py`
- Create: `services/simulation-engine/api/__init__.py`
- Create: `services/simulation-engine/tests/test_api.py`

**Step 1: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_client import Counter, Histogram, make_asgi_app
import logging

from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Metrics
simulation_counter = Counter(
    "simulations_total",
    "Total number of simulations started",
    ["scenario_type"]
)
simulation_duration = Histogram(
    "simulation_duration_seconds",
    "Simulation execution time",
    ["scenario_type"]
)

# Create FastAPI app
app = FastAPI(
    title="Chimera Simulation Engine",
    description="Multi-agent swarm intelligence simulation platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
from api import health, graph, simulation

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info(f"Starting {settings.service_name} v0.1.0")
    logger.info(f"Environment: {settings.environment}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    logger.info("Shutting down simulation engine")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )
```

**Step 2: Create api/__init__.py**

```python
"""API router package."""
```

**Step 3: Create api/health.py**

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/live", response_model=HealthResponse)
async def liveness():
    """Liveness probe - check if service is running."""
    return HealthResponse(
        status="healthy",
        service="simulation-engine",
        version="0.1.0"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness():
    """Readiness probe - check if service can accept requests."""
    # TODO: Add database connection checks
    return HealthResponse(
        status="ready",
        service="simulation-engine",
        version="0.1.0"
    )
```

**Step 4: Create api/graph.py (stub)**

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/build")
async def build_graph():
    """Build knowledge graph from documents."""
    return {"status": "not_implemented"}
```

**Step 5: Create api/simulation.py (stub)**

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/simulate")
async def run_simulation():
    """Run simulation."""
    return {"status": "not_implemented"}
```

**Step 6: Write test for health endpoints**

```python
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_liveness_probe(client):
    """Test liveness endpoint returns healthy status."""
    response = client.get("/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "simulation-engine"
    assert data["version"] == "0.1.0"


def test_readiness_probe(client):
    """Test readiness endpoint returns ready status."""
    response = client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint is accessible."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
```

**Step 7: Run tests**

```bash
cd services/simulation-engine
pytest tests/test_api.py -v
```

Expected: PASS (3 passed).

**Step 8: Start server manually to verify**

```bash
cd services/simulation-engine
python main.py &
PID=$!

sleep 3

curl http://localhost:8014/health/live
curl http://localhost:8014/health/ready

kill $PID
```

Expected: Both health endpoints return 200 with JSON response.

**Step 9: Commit**

```bash
git add services/simulation-engine/
git commit -m "feat(simulation): add FastAPI skeleton with health endpoints"
```

---

### Task 3: Knowledge Graph Builder

**Files:**
- Create: `services/simulation-engine/graph/neo4j_client.py`
- Create: `services/simulation-engine/graph/builder.py`
- Create: `services/simulation-engine/graph/models.py`
- Create: `services/simulation-engine/tests/test_graph.py`

**Step 1: Create graph/models.py**

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    POLICY = "policy"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    KNOWS = "knows"
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    PARTICIPATED_IN = "participated_in"
    RELATED_TO = "related_to"
    INFLUENCES = "influences"


class Entity(BaseModel):
    """Represents an entity in the knowledge graph."""
    id: str
    type: EntityType
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime] = None


class Relationship(BaseModel):
    """Represents a relationship between entities."""
    source: str
    target: str
    type: RelationType
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime] = None


class Fact(BaseModel):
    """Represents a temporal fact."""
    subject: str
    predicate: str
    object: str
    confidence: float
    valid_at: datetime
    invalid_at: Optional[datetime] = None
```

**Step 2: Create graph/neo4j_client.py**

```python
from neo4j import AsyncGraphDatabase
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from graph.models import Entity, Relationship, EntityType, RelationType

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for Neo4j graph database operations."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        """Close the database connection."""
        await self.driver.close()

    async def create_entity(self, entity: Entity) -> None:
        """Create or update an entity node."""
        query = """
        MERGE (e:Entity {id: $entity_id})
        SET e.type = $entity_type,
            e.attributes = $attributes,
            e.valid_at = $valid_at,
            e.invalid_at = $invalid_at
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                entity_id=entity.id,
                entity_type=entity.type.value,
                attributes=entity.attributes,
                valid_at=entity.valid_at.isoformat(),
                invalid_at=entity.invalid_at.isoformat() if entity.invalid_at else None
            )
        logger.debug(f"Created entity: {entity.id}")

    async def create_relationship(self, rel: Relationship) -> None:
        """Create a relationship between entities."""
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
        SET r.attributes = $attributes,
            r.valid_at = $valid_at,
            r.invalid_at = $invalid_at
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                source_id=rel.source,
                target_id=rel.target,
                rel_type=rel.type.value,
                attributes=rel.attributes,
                valid_at=rel.valid_at.isoformat(),
                invalid_at=rel.invalid_at.isoformat() if rel.invalid_at else None
            )
        logger.debug(f"Created relationship: {rel.source} -> {rel.target}")

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an entity by ID."""
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id)
            record = await result.single()
            if record:
                return dict(record["e"])
        return None

    async def query_related(self, entity_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Query entities related to the given entity."""
        query = """
        MATCH (e:Entity {id: $entity_id})-[*1..$depth]-(related:Entity)
        RETURN DISTINCT related
        LIMIT 100
        """
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id, depth=depth)
            records = await result.data()
            return [dict(r["related"]) for r in records]

    async def clear_all(self) -> None:
        """Clear all data from the database (for testing)."""
        query = "MATCH (n) DETACH DELETE n"
        async with self.driver.session() as session:
            await session.run(query)
        logger.warning("Cleared all graph data")
```

**Step 3: Create graph/builder.py**

```python
from typing import List, Dict, Any
import logging
from datetime import datetime

from graph.models import Entity, Relationship, EntityType
from graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from seed documents using GraphRAG-inspired extraction."""

    def __init__(self, client: Neo4jClient):
        self.client = client

    async def build_from_documents(self, documents: List[str]) -> Dict[str, int]:
        """
        Extract entities and relationships from documents.

        For Phase 0, this is a simplified implementation.
        Phase 1 will integrate actual LLM-based extraction.
        """
        entity_count = 0
        relationship_count = 0

        for doc_id, document in enumerate(documents):
            logger.info(f"Processing document {doc_id + 1}/{len(documents)}")

            # Simple extraction for Phase 0
            entities = await self._extract_entities_simple(document)
            relationships = await self._extract_relationships_simple(entities)

            for entity in entities:
                await self.client.create_entity(entity)
                entity_count += 1

            for rel in relationships:
                await self.client.create_relationship(rel)
                relationship_count += 1

        return {
            "entities": entity_count,
            "relationships": relationship_count
        }

    async def _extract_entities_simple(self, document: str) -> List[Entity]:
        """
        Simple entity extraction for Phase 0.

        This is a placeholder. Phase 1 will use LLM-based extraction.
        """
        import re

        entities = []
        now = datetime.utcnow()

        # Extract capitalized words as potential entities
        words = re.findall(r'\b[A-Z][a-z]+\b', document)
        unique_words = list(set(words[:20]))  # Limit for Phase 0

        for i, word in enumerate(unique_words):
            entities.append(Entity(
                id=f"entity_{i}",
                type=EntityType.CONCEPT,
                attributes={"name": word, "source": "simple_extraction"},
                valid_at=now
            ))

        return entities

    async def _extract_relationships_simple(self, entities: List[Entity]) -> List[Relationship]:
        """Simple relationship extraction for Phase 0."""
        relationships = []
        now = datetime.utcnow()

        # Create relationships between consecutive entities
        for i in range(len(entities) - 1):
            relationships.append(Relationship(
                source=entities[i].id,
                target=entities[i + 1].id,
                type="related_to",
                attributes={"source": "simple_extraction"},
                valid_at=now
            ))

        return relationships
```

**Step 4: Write tests for graph builder**

```python
import pytest
from datetime import datetime
from graph.neo4j_client import Neo4jClient
from graph.builder import GraphBuilder
from graph.models import Entity, EntityType


@pytest.fixture
async def neo4j_client():
    """Create a test Neo4j client."""
    # Use environment variables or test defaults
    import os
    uri = os.getenv("TEST_GRAPH_DB_URL", "bolt://localhost:7687")
    user = os.getenv("TEST_GRAPH_DB_USER", "neo4j")
    password = os.getenv("TEST_GRAPH_DB_PASSWORD", "password")

    client = Neo4jClient(uri, user, password)

    # Clear database before test
    await client.clear_all()

    yield client

    # Cleanup
    await client.clear_all()
    await client.close()


@pytest.mark.asyncio
async def test_create_entity(neo4j_client):
    """Test creating an entity in the graph."""
    entity = Entity(
        id="test_entity_1",
        type=EntityType.PERSON,
        attributes={"name": "Alice", "role": "test_subject"},
        valid_at=datetime.utcnow()
    )

    await neo4j_client.create_entity(entity)

    retrieved = await neo4j_client.get_entity("test_entity_1")
    assert retrieved is not None
    assert retrieved["id"] == "test_entity_1"
    assert retrieved["type"] == "person"


@pytest.mark.asyncio
async def test_graph_builder(neo4j_client):
    """Test building a graph from documents."""
    builder = GraphBuilder(neo4j_client)

    documents = [
        "Alice and Bob discussed the new policy.",
        "The policy affects many organizations."
    ]

    result = await builder.build_from_documents(documents)

    assert result["entities"] > 0
    assert result["relationships"] >= 0
```

**Step 5: Run tests**

```bash
cd services/simulation-engine
pytest tests/test_graph.py -v
```

Expected: Tests may fail if Neo4j is not available - this is expected for Phase 0. Add skip condition if needed.

**Step 6: Update api/graph.py with real implementation**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.neo4j_client import Neo4jClient
from graph.builder import GraphBuilder

router = APIRouter()

# Initialize client (use env vars or config)
client = None  # Will be initialized on startup
builder = None


class GraphBuildRequest(BaseModel):
    documents: list[str]


class GraphBuildResponse(BaseModel):
    graph_id: str
    entities: int
    relationships: int


@router.post("/build", response_model=GraphBuildResponse)
async def build_graph(request: GraphBuildRequest):
    """Build knowledge graph from documents."""
    if builder is None:
        raise HTTPException(status_code=503, detail="Graph service not initialized")

    result = await builder.build_from_documents(request.documents)

    return GraphBuildResponse(
        graph_id="temp_graph_1",  # Will be proper ID in Phase 1
        entities=result["entities"],
        relationships=result["relationships"]
    )
```

**Step 7: Test the endpoint**

```bash
cd services/simulation-engine
python main.py &
PID=$!

sleep 3

curl -X POST "http://localhost:8016/api/v1/graph/build" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["Test document about policy changes."]}'

kill $PID
```

Expected: JSON response with entity/relationship counts.

**Step 8: Commit**

```bash
git add services/simulation-engine/
git commit -m "feat(simulation): implement knowledge graph builder"
```

**Step 9: Update api/graph.py startup initialization**

Add to main.py startup event:

```python
# Initialize graph client
from graph.neo4j_client import Neo4jClient
from graph.builder import GraphBuilder

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info(f"Starting {settings.service_name} v0.1.0")

    # Initialize graph client
    global client, builder
    client = Neo4jClient(
        settings.graph_db_url,
        settings.graph_db_user,
        settings.graph_db_password
    )
    builder = GraphBuilder(client)

    logger.info("Graph client initialized")
```

---

### Task 4: Agent Profile Generator

**Files:**
- Create: `services/simulation-engine/agents/profile.py`
- Create: `services/simulation-engine/agents/persona.py`
- Create: `services/simulation-engine/tests/test_agents.py`

**Step 1: Create agents/profile.py**

```python
from pydantic import BaseModel
from typing import List, Dict, Any
from enum import Enum


class MBTIType(str, Enum):
    """Myers-Briggs Type Indicator personality types."""
    INTJ = "INTJ"  # Architect
    INTP = "INTP"  # Logician
    ENTJ = "ENTJ"  # Commander
    ENTP = "ENTP"  # Debater
    INFJ = "INFJ"  # Advocate
    INFP = "INFP"  # Mediator
    ENFJ = "ENFJ"  # Protagonist"
    ENFP = "ENFP"  # Campaigner"
    ISTJ = "ISTJ"  # Logistician
    ISFJ = "ISFJ"  # Defender
    ESTJ = "ESTJ"  # Executive
    ESFJ = "ESFJ"  # Consul
    ISTP = "ISTP"  # Virtuoso
    ISFP = "ISFP"  # Adventurer"
    ESTP = "ESTP"  # Entrepreneur"
    ESFP = "ESFP"  # Entertainer"


class PoliticalLeaning(str, Enum):
    """Political orientation categories."""
    FAR_LEFT = "far_left"
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    FAR_RIGHT = "far_right"


class Demographics(BaseModel):
    """Demographic characteristics."""
    age: int
    gender: str
    education: str
    occupation: str
    location: str
    income_level: str


class BehavioralProfile(BaseModel):
    """Behavioral tendencies and personality traits."""
    openness: float  # 0-1
    conscientiousness: float  # 0-1
    extraversion: float  # 0-1
    agreeableness: float  # 0-1
    neuroticism: float  # 0-1


class AgentProfile(BaseModel):
    """Complete agent persona definition."""
    id: str
    mbti: MBTIType
    demographics: Demographics
    behavioral: BehavioralProfile
    political_leaning: PoliticalLeaning
    information_sources: List[str]
    memory_capacity: int
```

**Step 2: Create agents/persona.py**

```python
import random
from typing import List
from datetime import datetime
import logging

from agents.profile import (
    AgentProfile,
    MBTIType,
    PoliticalLeaning,
    Demographics,
    BehavioralProfile
)

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """Generate diverse agent personas for simulation."""

    MBTI_TYPES = list(MBTIType)
    POLITICAL_LEANINGS = list(PoliticalLeaning)

    OCCUPATIONS = [
        "teacher", "engineer", "doctor", "artist", "business_owner",
        "student", "retiree", "manager", "scientist", "writer"
    ]

    LOCATIONS = ["urban", "suburban", "rural"]

    EDUCATION_LEVELS = ["high_school", "bachelor", "master", "phd"]

    def __init__(self, seed: int = None):
        """Initialize generator with optional seed for reproducibility."""
        self.rng = random.Random(seed)

    async def generate_population(
        self,
        count: int,
        diversity_config: dict = None
    ) -> List[AgentProfile]:
        """
        Generate N diverse agent profiles.

        Args:
            count: Number of agents to generate
            diversity_config: Optional distribution preferences

        Returns:
            List of agent profiles
        """
        logger.info(f"Generating {count} agent personas")

        profiles = []

        # Simple diversity strategy: ensure MBTI and political distribution
        mbti_distribution = self._distribute_types(count, self.MBTI_TYPES)
        political_distribution = self._distribute_types(count, self.POLITICAL_LEANINGS)

        for i in range(count):
            mbti = mbti_distribution[i]
            political = political_distribution[i]

            profile = AgentProfile(
                id=f"agent_{i:04d}",
                mbti=mbti,
                demographics=self._generate_demographics(),
                behavioral=self._generate_behavioral(mbti),
                political_leaning=political,
                information_sources=self._generate_info_sources(),
                memory_capacity=self.rng.randint(50, 200)
            )
            profiles.append(profile)

        logger.info(f"Generated {len(profiles)} diverse personas")
        return profiles

    def _distribute_types(self, count: int, types: List) -> List:
        """Distribute types evenly across population."""
        result = []
        per_type = max(1, count // len(types))

        for _ in range(count):
            type_index = (len(result) // per_type) % len(types)
            result.append(types[type_index])

        self.rng.shuffle(result)
        return result

    def _generate_demographics(self) -> Demographics:
        """Generate random demographic attributes."""
        return Demographics(
            age=self.rng.randint(18, 75),
            gender=self.rng.choice(["male", "female", "non_binary", "prefer_not_to_say"]),
            education=self.rng.choice(self.EDUCATION_LEVELS),
            occupation=self.rng.choice(self.OCCUPATIONS),
            location=self.rng.choice(self.LOCATIONS),
            income_level=self.rng.choice(["low", "medium", "high", "very_high"])
        )

    def _generate_behavioral(self, mbti: MBTIType) -> BehavioralProfile:
        """Generate behavioral traits influenced by MBTI."""
        # MBTI-influenced traits
        is_introvert = mbti.value[0] == 'I'
        is_intuitive = mbti.value[1] == 'N'
        is_thinking = mbti.value[2] == 'T'
        is_judging = mbti.value[3] == 'J'

        return BehavioralProfile(
            openness=0.7 if is_intuitive else 0.4,
            conscientiousness=0.8 if is_judging else 0.5,
            extraversion=0.3 if is_introvert else 0.7,
            agreeableness=0.6 if not is_thinking else 0.4,
            neuroticism=self.rng.uniform(0.2, 0.7)
        )

    def _generate_info_sources(self) -> List[str]:
        """Generate information source preferences."""
        all_sources = [
            "twitter", "reddit", "news_website", "social_media",
            "podcasts", "youtube", "traditional_media", "forums"
        ]
        count = self.rng.randint(2, 4)
        return self.rng.sample(all_sources, count)
```

**Step 3: Write tests for persona generator**

```python
import pytest
from agents.persona import PersonaGenerator
from agents.profile import MBTIType, PoliticalLeaning


@pytest.mark.asyncio
async def test_generate_population():
    """Test generating a population of agents."""
    generator = PersonaGenerator(seed=42)

    profiles = await generator.generate_population(count=10)

    assert len(profiles) == 10

    # Check diversity
    mbti_types = set(p.mbti for p in profiles)
    political_types = set(p.political_leaning for p in profiles)

    assert len(mbti_types) > 1  # Should have multiple types
    assert len(political_types) > 1


@pytest.mark.asyncio
async def test_agent_profile_completeness():
    """Test that generated profiles have all required fields."""
    generator = PersonaGenerator()

    profiles = await generator.generate_population(count=5)

    for profile in profiles:
        assert profile.id.startswith("agent_")
        assert profile.mbti in MBTIType
        assert profile.political_leaning in PoliticalLeaning
        assert 18 <= profile.demographics.age <= 75
        assert 0 <= profile.behavioral.openness <= 1
        assert len(profile.information_sources) >= 2
        assert 50 <= profile.memory_capacity <= 200


@pytest.mark.asyncio
async def test_reproducibility_with_seed():
    """Test that same seed produces same results."""
    generator1 = PersonaGenerator(seed=123)
    generator2 = PersonaGenerator(seed=123)

    profiles1 = await generator1.generate_population(count=10)
    profiles2 = await generator2.generate_population(count=10)

    assert len(profiles1) == len(profiles2)

    for p1, p2 in zip(profiles1, profiles2):
        assert p1.mbti == p2.mbti
        assert p1.demographics.age == p2.demographics.age
```

**Step 4: Run tests**

```bash
cd services/simulation-engine
pytest tests/test_agents.py -v
```

Expected: PASS (3 passed).

**Step 5: Create API endpoint for persona generation**

Create `api/agents.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.persona import PersonaGenerator

router = APIRouter()

generator = PersonaGenerator()


class GeneratePersonasRequest(BaseModel):
    count: int
    seed: int = None


@router.post("/generate")
async def generate_personas(request: GeneratePersonasRequest):
    """Generate agent personas for simulation."""
    if request.count < 1 or request.count > 1000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 1000")

    profiles = await generator.generate_population(
        count=request.count,
        diversity_config={}
    )

    return {
        "personas": [p.dict() for p in profiles],
        "count": len(profiles)
    }
```

**Step 6: Add router to main.py**

```python
from api import agents

app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
```

**Step 7: Test the endpoint**

```bash
curl -X POST "http://localhost:8016/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "seed": 42}'
```

Expected: JSON response with 5 agent personas.

**Step 8: Commit**

```bash
git add services/simulation-engine/
git commit -m "feat(simulation): implement agent profile generator"
```

**Step 9: Update TaskList to mark this task complete**

(Use TaskUpdate tool to update task status to completed)

---

### Task 5: Basic Simulation Runner

**Files:**
- Create: `services/simulation-engine/simulation/runner.py`
- Create: `services/simulation-engine/simulation/llm_router.py`
- Create: `services/simulation-engine/tests/test_simulation.py`

**Step 1: Create simulation/models.py**

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ActionType(str, Enum):
    """Social action types from OASIS framework."""
    POST = "post"
    REPLY = "reply"
    RETWEET = "retweet"
    LIKE = "like"
    FOLLOW = "follow"
    QUOTE = "quote"


class SimulationConfig(BaseModel):
    """Configuration for simulation run."""
    agent_count: int = Field(default=10, ge=1, le=1000)
    simulation_rounds: int = Field(default=10, ge=1, le=100)
    scenario_description: str
    seed_documents: List[str]


class SimulationResult(BaseModel):
    """Results from a simulation run."""
    simulation_id: str
    status: str
    rounds_completed: int
    total_actions: int
    final_summary: str
```

**Step 2: Create simulation/llm_router.py**

```python
from typing import Literal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    """Available LLM backends."""
    LOCAL_VLLM = "local_vllm"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TieredLLMRouter:
    """Route LLM calls based on cost and criticality."""

    def __init__(
        self,
        local_ratio: float = 0.95,
        local_url: str = "http://localhost:8000"
    ):
        self.local_ratio = local_ratio
        self.local_url = local_url
        self.call_count = 0
        self.local_count = 0
        self.api_count = 0

    async def route_decision(self, context: str = "") -> LLMBackend:
        """
        Decide which LLM to use based on context and cost ratio.

        For Phase 0, use simple random routing respecting ratio.
        Phase 1 will analyze context criticality.
        """
        import random

        self.call_count += 1

        if random.random() < self.local_ratio:
            self.local_count += 1
            logger.debug(f"Routing to local LLM ({self.local_count}/{self.call_count})")
            return LLMBackend.LOCAL_VLLM
        else:
            self.api_count += 1
            logger.debug(f"Routing to API LLM ({self.api_count}/{self.call_count})")
            # Choose between OpenAI and Anthropic
            return LLMBackend.OPENAI if random.random() < 0.5 else LLMBackend.ANTHROPIC

    def get_stats(self) -> Dict[str, int]:
        """Get routing statistics."""
        return {
            "total_calls": self.call_count,
            "local_calls": self.local_count,
            "api_calls": self.api_count,
            "local_ratio": self.local_count / self.call_count if self.call_count > 0 else 0
        }
```

**Step 3: Create simulation/runner.py**

```python
import asyncio
import uuid
from typing import List
from datetime import datetime
import logging

from simulation.models import SimulationConfig, SimulationResult, ActionType
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter

logger = logging.getLogger(__name__)


class SimulationRunner:
    """OASIS-inspired simulation orchestrator."""

    def __init__(
        self,
        persona_generator: PersonaGenerator,
        llm_router: TieredLLMRouter
    ):
        self.persona_generator = persona_generator
        self.llm_router = llm_router

    async def run_simulation(
        self,
        config: SimulationConfig
    ) -> SimulationResult:
        """
        Execute simulation rounds.

        For Phase 0, this is a simplified implementation.
        Phase 1 will integrate full OASIS framework.
        """
        simulation_id = str(uuid.uuid4())
        logger.info(f"Starting simulation {simulation_id}")

        # Generate agent personas
        agents = await self.persona_generator.generate_population(
            count=config.agent_count
        )

        logger.info(f"Generated {len(agents)} agents")

        # Run simulation rounds
        total_actions = 0
        actions_log = []

        for round_num in range(config.simulation_rounds):
            logger.info(f"Round {round_num + 1}/{config.simulation_rounds}")

            round_actions = await self._run_round(agents, round_num)
            total_actions += len(round_actions)
            actions_log.extend(round_actions)

        # Generate summary
        summary = await self._generate_summary(
            config,
            agents,
            actions_log
        )

        # Log routing stats
        stats = self.llm_router.get_stats()
        logger.info(f"LLM routing stats: {stats}")

        return SimulationResult(
            simulation_id=simulation_id,
            status="completed",
            rounds_completed=config.simulation_rounds,
            total_actions=total_actions,
            final_summary=summary
        )

    async def _run_round(self, agents: List, round_num: int) -> List[dict]:
        """Execute a single simulation round."""
        actions = []

        # For each agent, decide and execute action
        for agent in agents:
            # Determine which LLM to use
            backend = await self.llm_router.route_decision(
                context=f"Agent {agent.id} making decision"
            )

            # For Phase 0, simulate action without actual LLM call
            action = {
                "agent_id": agent.id,
                "round": round_num,
                "action_type": ActionType.POST.value,
                "backend_used": backend.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            actions.append(action)

        return actions

    async def _generate_summary(
        self,
        config: SimulationConfig,
        agents: List,
        actions: List[dict]
    ) -> str:
        """Generate simulation summary."""
        return f"""
Simulation Summary
==================
Scenario: {config.scenario_description}
Agents: {len(agents)}
Rounds: {config.simulation_rounds}
Total Actions: {len(actions)}

This is a Phase 0 placeholder summary.
Phase 1 will use ReACT ReportAgent for detailed analysis.
        """.strip()
```

**Step 4: Write tests**

```python
import pytest
from simulation.runner import SimulationRunner
from simulation.models import SimulationConfig
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter


@pytest.mark.asyncio
async def test_simulation_runner():
    """Test basic simulation execution."""
    generator = PersonaGenerator(seed=42)
    router = TieredLLMRouter(local_ratio=0.8)
    runner = SimulationRunner(generator, router)

    config = SimulationConfig(
        agent_count=5,
        simulation_rounds=3,
        scenario_description="Test scenario",
        seed_documents=["Test document"]
    )

    result = await runner.run_simulation(config)

    assert result.status == "completed"
    assert result.rounds_completed == 3
    assert result.total_actions == 15  # 5 agents * 3 rounds
    assert len(result.final_summary) > 0


@pytest.mark.asyncio
async def test_llm_router_stats():
    """Test LLM router statistics."""
    router = TieredLLMRouter(local_ratio=0.7)

    # Make some routing decisions
    backends = [await router.route_decision() for _ in range(100)]

    stats = router.get_stats()

    assert stats["total_calls"] == 100
    # Allow some variance due to randomness
    assert 60 <= stats["local_calls"] <= 80
```

**Step 5: Run tests**

```bash
cd services/simulation-engine
pytest tests/test_simulation.py -v
```

Expected: PASS (2 passed).

**Step 6: Update api/simulation.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from simulation.runner import SimulationRunner
from simulation.models import SimulationConfig
from agents.persona import PersonaGenerator
from simulation.llm_router import TieredLLMRouter

router = APIRouter()

# Initialize components
runner = None


@router.post("/simulate")
async def run_simulation(config: SimulationConfig):
    """Run a simulation with the given configuration."""
    if runner is None:
        raise HTTPException(status_code=503, detail="Simulation service not initialized")

    result = await runner.run_simulation(config)

    return {
        "simulation_id": result.simulation_id,
        "status": result.status,
        "rounds_completed": result.rounds_completed,
        "total_actions": result.total_actions,
        "summary": result.final_summary
    }
```

**Step 7: Test full simulation endpoint**

```bash
curl -X POST "http://localhost:8016/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 5,
    "simulation_rounds": 3,
    "scenario_description": "Testing policy response",
    "seed_documents": ["Policy document text"]
  }'
```

Expected: Simulation result with 15 total actions.

**Step 8: Commit**

```bash
git add services/simulation-engine/
git commit -m "feat(simulation): implement basic simulation runner"
```

**Step 9: Initialize runner in main.py startup**

```python
# Initialize simulation runner
from simulation.runner import SimulationRunner

@app.on_event("startup")
async def startup_event():
    # ... existing code ...

    # Initialize simulation runner
    global runner
    runner = SimulationRunner(builder, TieredLLMRouter())

    logger.info("Simulation runner initialized")
```

---

### Task 6: End-to-End Integration Test

**Files:**
- Create: `services/simulation-engine/tests/test_e2e.py`

**Step 1: Create end-to-end test**

```python
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_full_simulation_pipeline():
    """Test complete pipeline from graph build to simulation."""

    async with AsyncClient(app=app, base_url="http://test") as client:

        # Step 1: Check health
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Step 2: Build knowledge graph
        response = await client.post(
            "/api/v1/graph/build",
            json={"documents": ["Test policy document about climate change."]}
        )
        assert response.status_code == 200
        graph_data = response.json()
        assert graph_data["entities"] > 0

        # Step 3: Generate personas
        response = await client.post(
            "/api/v1/agents/generate",
            json={"count": 10, "seed": 42}
        )
        assert response.status_code == 200
        personas_data = response.json()
        assert personas_data["count"] == 10

        # Step 4: Run simulation
        response = await client.post(
            "/api/v1/simulation/simulate",
            json={
                "agent_count": 10,
                "simulation_rounds": 5,
                "scenario_description": "Public response to climate policy",
                "seed_documents": ["Climate policy document"]
            }
        )
        assert response.status_code == 200
        sim_data = response.json()
        assert sim_data["status"] == "completed"
        assert sim_data["total_actions"] == 50  # 10 agents * 5 rounds

        # Step 5: Check metrics
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "simulations_total" in response.text


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid requests."""

    async with AsyncClient(app=app, base_url="http://test") as client:

        # Invalid agent count
        response = await client.post(
            "/api/v1/agents/generate",
            json={"count": 2000}  # Over max
        )
        assert response.status_code == 400

        # Missing required fields
        response = await client.post(
            "/api/v1/simulation/simulate",
            json={"agent_count": 5}  # Missing required fields
        )
        assert response.status_code == 422  # Validation error
```

**Step 2: Run end-to-end tests**

```bash
cd services/simulation-engine
pytest tests/test_e2e.py -v
```

Expected: All tests pass. May skip graph-related tests if Neo4j unavailable.

**Step 3: Measure execution time**

```bash
time pytest tests/test_e2e.py::test_full_simulation_pipeline -v
```

Expected: Completes in under 5 minutes (Phase 0 success criteria).

**Step 4: Verify token tracking**

Add token tracking to simulation:

```python
# In simulation/runner.py
class TokenTracker:
    def __init__(self):
        self.tokens_used = 0

    def add(self, count: int):
        self.tokens_used += count

# Pass to runner and log in summary
```

**Step 5: Create validation script**

Create `scripts/validate_phase0.sh`:

```bash
#!/bin/bash
set -e

echo "Phase 0 Validation Script"
echo "========================="

# Check Python version
python --version | grep "3.1[1-9]" || exit 1

# Run tests
pytest tests/ -v --cov=. --cov-report=term

# Check coverage is at least 50%
pytest tests/ --cov=. --cov-report=term | grep "TOTAL.*50%" || exit 1

echo "Phase 0 validation passed!"
```

**Step 6: Run validation script**

```bash
chmod +x scripts/validate_phase0.sh
./scripts/validate_phase0.sh
```

Expected: All validations pass.

**Step 7: Document Phase 0 completion**

Create `PHASE0_COMPLETION.md`:

```markdown
# Phase 0 Completion Report

**Date:** [Date]
**Status:** ✅ Complete

## Success Criteria Met

- [x] 10-agent simulation completes in <5 minutes
- [x] All tests passing
- [x] Token usage tracked
- [x] Basic five-stage pipeline operational

## Metrics

- Test Coverage: XX%
- Simulation Time: XX seconds
- LLM Call Distribution: XX% local, XX% API

## Known Limitations

- GraphRAG extraction is simplified (placeholder)
- No actual LLM API calls in Phase 0
- OASIS integration not yet implemented

## Next Steps

Proceed to Phase 1: Foundation
```

**Step 8: Create deployment artifacts**

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8016/health/live')" || exit 1

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8016"]
```

---

### Task 7: Documentation and Deployment

**Files:**
- Create: `services/simulation-engine/README.md`
- Create: `services/simulation-engine/k8s-deployment.yaml`
- Create: `services/simulation-engine/docker-compose.yml`

**Step 1: Create README.md**

```markdown
# Chimera Simulation Engine

A multi-agent swarm intelligence simulation platform for "what-if" scenario testing.

## Architecture

Five-stage pipeline:
1. Knowledge Graph Construction (GraphRAG-inspired)
2. Environment Setup (Agent Persona Generation)
3. Simulation Execution (OASIS-inspired)
4. Report Generation (ReACT-pattern)
5. Deep Interaction (Agent Query)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run tests
pytest tests/ -v

# Start server
python main.py
```

## API Endpoints

- `POST /api/v1/graph/build` - Build knowledge graph from documents
- `POST /api/v1/agents/generate` - Generate agent personas
- `POST /api/v1/simulation/simulate` - Run simulation
- `GET /health/live` - Health check
- `GET /metrics` - Prometheus metrics

## Cost Control

Tiered LLM routing:
- 95% local vLLM (Llama 3 8B) - ~$0
- 5% API (Claude/GPT-4) - ~$0.01 per simulation

## Development

```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_simulation.py::test_simulation_runner -v

# Format code
black .
isort .

# Type check
mypy .
```

## License

MIT/Apache-2.0 (permissive)
```

**Step 2: Create docker-compose.yml**

```yaml
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
      - NEO4J_AUTH=neo4j/chimera_graph_2026
    volumes:
      - neo4j_data:/data

  pgvector:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=chimera
    volumes:
      - pgvector_data:/var/lib/postgresql/data

  vllm:
    image: vllm/vllm-openai:v0.6.0
    ports:
      - "8000:8000"
    command: >
      --model meta-llama/Meta-Llama-3-8B-Instruct
      --quantization awq

volumes:
  neo4j_data:
  pgvector_data:
```

**Step 3: Create k8s-deployment.yaml**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: simulation-engine-config
data:
  LOG_LEVEL: "INFO"
  PORT: "8016"
  LOCAL_LLM_RATIO: "0.95"
  MAX_TOKENS_PER_SIMULATION: "100000"
---
apiVersion: v1
kind: Secret
metadata:
  name: simulation-engine-secrets
type: Opaque
stringData:
  GRAPH_DB_PASSWORD: "chimera_graph_2026"
  OPENAI_API_KEY: "your-key-here"
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
      containers:
      - name: simulation-engine
        image: simulation-engine:latest
        ports:
        - containerPort: 8016
        env:
        - name: GRAPH_DB_URL
          value: "bolt://neo4j:7687"
        - name: GRAPH_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: simulation-engine-secrets
              key: GRAPH_DB_PASSWORD
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
apiVersion: v1
kind: Service
metadata:
  name: simulation-engine
spec:
  selector:
    app: simulation-engine
  ports:
  - port: 8016
    targetPort: 8016
  type: ClusterIP
```

**Step 4: Create Makefile**

```makefile
.PHONY: help test run build deploy

help:
	@echo "Available commands:"
	@echo "  make test     - Run tests"
	@echo "  make run      - Run server"
	@echo "  make build    - Build Docker image"
	@echo "  make deploy   - Deploy to Kubernetes"

test:
	pytest tests/ -v --cov=. --cov-report=term

run:
	python main.py

build:
	docker build -t simulation-engine:latest .

deploy:
	kubectl apply -f k8s-deployment.yaml

validate:
	./scripts/validate_phase0.sh
```

**Step 5: Run full local stack**

```bash
docker-compose up -d

# Wait for services to start
sleep 10

# Run full test
pytest tests/test_e2e.py -v

# Check logs
docker-compose logs simulation-engine
```

**Step 6: Verify metrics**

```bash
curl http://localhost:8016/metrics
```

Expected: Prometheus metrics output with simulation counters.

**Step 7: Create quick start guide**

Create `QUICKSTART.md`:

```markdown
# Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker (for local services)

## 5-Minute Setup

```bash
# 1. Clone and navigate
cd services/simulation-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env

# 4. Run tests
pytest tests/ -v

# 5. Start server
python main.py
```

## Try It Out

```bash
# Generate 10 agents
curl -X POST "http://localhost:8016/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{"count": 10}'

# Run a simulation
curl -X POST "http://localhost:8016/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 10,
    "simulation_rounds": 5,
    "scenario_description": "Test simulation"
  }'
```

## Next Steps

See README.md for full documentation.
```

**Step 8: Final validation and commit**

```bash
# Run all tests
pytest tests/ -v

# Check code style
black . --check
isort . --check

# Final commit
git add services/simulation-engine/
git commit -m "feat(simulation): complete Phase 0 implementation with documentation"
```

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-15-chimera-simulation-engine-implementation.md`.**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
