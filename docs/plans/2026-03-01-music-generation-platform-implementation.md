# Music Generation Platform - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a dual-service AI music generation platform for Project Chimera that supports social media content and live show underscore with adaptive real-time modulation.

**Architecture:** Multi-tier orchestration pattern with Music Generation Service (port 8011) handling model inference and Music Orchestration Service (port 8012) handling caching, approval workflow, and show integration.

**Tech Stack:** FastAPI, SQLAlchemy, Redis, PostgreSQL, MinIO, Meta MusicGen-Small, ACE-Step, Kubernetes (k3s), Pytest

---

## Task 1: Project Scaffolding

**Files:**
- Create: `services/music-generation/pyproject.toml`
- Create: `services/music-generation/README.md`
- Create: `services/music-orchestration/pyproject.toml`
- Create: `services/music-orchestration/README.md`

**Step 1: Create music-generation pyproject.toml**

Create `services/music-generation/pyproject.toml`:
```toml
[project]
name = "chimera-music-generation"
version = "0.1.0"
description = "AI music generation service for Project Chimera"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "minio>=7.2.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "prometheus-client>=0.19.0",
    "structlog>=24.1.0",
    "transformers>=4.37.0",
    "torch>=2.1.0",
    "audiocraft>=1.0.0",  # Meta MusicGen
    "numpy>=1.26.0",
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Step 2: Create music-generation README.md**

Create `services/music-generation/README.md`:
```markdown
# Music Generation Service

Port 8011 - Model inference service for AI music generation.

## Models
- Meta MusicGen-Small (~2GB VRAM)
- ACE-Step (<4GB VRAM)

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Running

```bash
uvicorn music_generation.main:app --host 0.0.0.0 --port 8011
```
```

**Step 3: Create music-orchestration pyproject.toml**

Create `services/music-orchestration/pyproject.toml`:
```toml
[project]
name = "chimera-music-orchestration"
version = "0.1.0"
description = "Music orchestration service for Project Chimera"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "minio>=7.2.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "prometheus-client>=0.19.0",
    "structlog>=24.1.0",
    "httpx>=0.26.0",
    "websockets>=12.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Step 4: Create music-orchestration README.md**

Create `services/music-orchestration/README.md`:
```markdown
# Music Orchestration Service

Port 8012 - Caching, approval workflow, and show integration for music generation.

## Responsibilities
- Request routing and validation
- Exact-match caching (Redis)
- Staged approval pipeline
- Role-based access control
- Sentiment-based adaptive modulation
- WebSocket progress streaming

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Running

```bash
uvicorn music_orchestration.main:app --host 0.0.0.0 --port 8012
```
```

**Step 5: Commit**

```bash
git add services/music-generation/ services/music-orchestration/
git commit -m "feat: scaffold music generation and orchestration services"
```

---

## Task 2: Database Schema Setup

**Files:**
- Create: `services/music-orchestration/music_orchestration/database.py`
- Create: `services/music-orchestration/music_orchestration/models.py`
- Create: `services/music-orchestration/migrations/001_create_music_tables.sql`

**Step 1: Write database connection test**

Create `services/music-orchestration/tests/unit/test_database.py`:
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from music_orchestration.database import get_engine, Base


@pytest.mark.asyncio
async def test_database_connection():
    """Test that database connection can be established"""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        assert result.scalar() == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_tables_can_be_created():
    """Test that all tables can be created without errors"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
```

**Step 2: Run test to verify it fails**

Run: `cd services/music-orchestration && pytest tests/unit/test_database.py -v`
Expected: FAIL with "module 'music_orchestration.database' not found"

**Step 3: Implement database connection**

Create `services/music-orchestration/music_orchestration/database.py`:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://chimera:chimera@localhost/chimera_music"

    class Config:
        env_file = ".env"


class Base(DeclarativeBase):
    pass


def get_engine() -> AsyncSession:
    settings = Settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    return engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd services/music-orchestration && pytest tests/unit/test_database.py -v`
Expected: PASS (assuming database is running, otherwise connection refused is OK for now)

**Step 5: Implement models**

Create `services/music-orchestration/music_orchestration/models.py`:
```python
from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from music_orchestration.database import Base


class UseCase(str, Enum):
    MARKETING = "marketing"
    SHOW = "show"


class MusicStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MusicGeneration(Base):
    __tablename__ = "music_generations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    use_case: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Structured parameters
    genre: Mapped[str | None] = mapped_column(String(100))
    mood: Mapped[str | None] = mapped_column(String(100))
    tempo: Mapped[int | None] = mapped_column(Integer)
    key_signature: Mapped[str | None] = mapped_column(String(10))
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    # Output
    minio_key: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="mp3")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    approval_status: Mapped[str | None] = mapped_column(String(20))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    # Audit
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Cache stats
    cache_hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("use_case IN ('marketing', 'show')", name="check_use_case"),
        Index("idx_music_prompt_hash", "prompt_hash"),
        Index("idx_music_status", "status"),
        Index("idx_music_approval", "approval_status"),
        Index("idx_music_created_at", "created_at"),
    )


class MusicApproval(Base):
    __tablename__ = "music_approvals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    music_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("music_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_audit_timestamp", "created_at"),
    )


class MusicUsageLog(Base):
    __tablename__ = "music_usage_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    music_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("music_generations.id"))
    was_cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    generation_duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_usage_timestamp", "created_at"),
    )
```

**Step 6: Create migration SQL**

Create `services/music-orchestration/migrations/001_create_music_tables.sql`:
```sql
-- Music generations metadata
CREATE TABLE IF NOT EXISTS music_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    use_case VARCHAR(20) NOT NULL CHECK (use_case IN ('marketing', 'show')),
    model_name VARCHAR(50) NOT NULL,
    genre VARCHAR(100),
    mood VARCHAR(100),
    tempo INTEGER,
    key_signature VARCHAR(10),
    duration_seconds INTEGER NOT NULL,
    minio_key TEXT NOT NULL,
    format VARCHAR(10) NOT NULL DEFAULT 'mp3',
    file_size_bytes INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_status VARCHAR(20),
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_at TIMESTAMPTZ,
    cache_hit_count INTEGER DEFAULT 0,
    last_cached_at TIMESTAMPTZ
);

CREATE INDEX idx_music_prompt_hash ON music_generations(prompt_hash);
CREATE INDEX idx_music_status ON music_generations(status);
CREATE INDEX idx_music_approval ON music_generations(approval_status) WHERE approval_status IS NOT NULL;
CREATE INDEX idx_music_created_at ON music_generations(created_at DESC);

-- Approval audit trail
CREATE TABLE IF NOT EXISTS music_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    music_id UUID NOT NULL REFERENCES music_generations(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    user_id UUID NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON music_approvals(created_at DESC);

-- Usage tracking
CREATE TABLE IF NOT EXISTS music_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    music_id UUID,
    was_cache_hit BOOLEAN NOT NULL,
    generation_duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_timestamp ON music_usage_log(created_at DESC);
```

**Step 7: Commit**

```bash
git add services/music-orchestration/music_orchestration/database.py services/music-orchestration/music_orchestration/models.py services/music-orchestration/migrations/001_create_music_tables.sql
git commit -m "feat: add database schema for music platform"
```

---

## Task 3: Shared Data Models and Schemas

**Files:**
- Create: `services/music-orchestration/music_orchestration/schemas.py`
- Test: `services/music-orchestration/tests/unit/test_schemas.py`

**Step 1: Write schema validation tests**

Create `services/music-orchestration/tests/unit/test_schemas.py`:
```python
import pytest
from pydantic import ValidationError

from music_orchestration.schemas import (
    MusicRequest,
    MusicResponse,
    GenerationProgress,
    UseCase,
)


def test_music_request_with_valid_data():
    request = MusicRequest(
        prompt="upbeat electronic background",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    assert request.prompt == "upbeat electronic background"
    assert request.use_case == UseCase.MARKETING
    assert request.duration_seconds == 30


def test_music_request_rejects_invalid_duration():
    with pytest.raises(ValidationError):
        MusicRequest(
            prompt="test",
            use_case=UseCase.MARKETING,
            duration_seconds=500  # Too long
        )


def test_music_request_accepts_optional_params():
    request = MusicRequest(
        prompt="dramatic orchestral",
        use_case=UseCase.SHOW,
        duration_seconds=180,
        genre="orchestral",
        mood="dramatic",
        tempo=120,
        key_signature="C minor"
    )
    assert request.genre == "orchestral"
    assert request.mood == "dramatic"
    assert request.tempo == 120


def test_music_response_serialization():
    response = MusicResponse(
        request_id="abc-123",
        music_id="def-456",
        status="completed",
        audio_url="https://minio/audio.mp3",
        duration_seconds=30,
        format="mp3",
        was_cache_hit=True
    )
    data = response.model_dump()
    assert data["request_id"] == "abc-123"
    assert data["was_cache_hit"] is True
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_schemas.py -v`
Expected: FAIL with "module 'music_orchestration.schemas' not found"

**Step 3: Implement schemas**

Create `services/music-orchestration/music_orchestration/schemas.py`:
```python
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class UseCase(str, Enum):
    MARKETING = "marketing"
    SHOW = "show"


class Role(str, Enum):
    SOCIAL_MEDIA_USER = "social_media_user"
    SHOW_OPERATOR = "show_operator"
    DEVELOPER = "developer"
    ADMIN = "admin"


class MusicRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=1000)
    use_case: UseCase
    duration_seconds: int = Field(..., ge=15, le=300)
    format: str = Field(default="mp3")

    # Optional structured overrides
    genre: str | None = Field(None, max_length=100)
    mood: str | None = Field(None, max_length=100)
    tempo: int | None = Field(None, ge=40, le=240)
    key_signature: str | None = Field(None, max_length=20)

    @property
    def cache_key(self) -> str:
        """Generate cache key from prompt and parameters"""
        import hashlib
        key_data = f"{self.prompt}:{self.use_case}:{self.duration_seconds}"
        if self.genre:
            key_data += f":genre={self.genre}"
        if self.mood:
            key_data += f":mood={self.mood}"
        if self.tempo:
            key_data += f":tempo={self.tempo}"
        return hashlib.sha256(key_data.encode()).hexdigest()


class MusicResponse(BaseModel):
    request_id: str
    music_id: str | None = None
    status: Literal["cached", "generating", "completed", "failed"]
    audio_url: str | None = None
    duration_seconds: int
    format: str
    was_cache_hit: bool
    estimated_completion: str | None = None


class GenerationProgress(BaseModel):
    request_id: str
    type: Literal["started", "progress", "completed", "failed"]
    progress: int | None = None  # 0-100
    stage: str | None = None
    eta_seconds: int | None = None
    error: str | None = None


class UserContext(BaseModel):
    service_name: str
    role: Role
    permissions: list[str]


class ModulationParams(BaseModel):
    tempo_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    brightness_delta: float = Field(default=0.0, ge=-0.5, le=0.5)
    volume_adjust_db: float = Field(default=0.0, ge=-10.0, le=10.0)


class SentimentScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    trend: Literal["rising", "falling", "stable"]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_schemas.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/schemas.py services/music-orchestration/tests/unit/test_schemas.py
git commit -m "feat: add shared data models and schemas"
```

---

## Task 4: Error Handling Classes

**Files:**
- Create: `services/music-orchestration/music_orchestration/errors.py`
- Test: `services/music-orchestration/tests/unit/test_errors.py`

**Step 1: Write error class tests**

Create `services/music-orchestration/tests/unit/test_errors.py`:
```python
import pytest

from music_orchestration.errors import (
    MusicServiceError,
    ModelNotFoundError,
    InsufficientVRAMError,
    GenerationTimeoutError,
    InvalidPromptError,
    ApprovalRequiredError,
)


def test_model_not_found_error():
    error = ModelNotFoundError("musicgen")
    assert "musicgen" in str(error)
    assert error.model_name == "musicgen"


def test_insufficient_vram_error():
    error = InsufficientVRAMError(required_mb=4096, available_mb=2048)
    assert "4096" in str(error)
    assert "2048" in str(error)
    assert error.required_mb == 4096


def test_invalid_prompt_error():
    error = InvalidPromptError("blocked content")
    assert "blocked content" in str(error)


def test_approval_required_error():
    error = ApprovalRequiredError("abc-123")
    assert "abc-123" in str(error)
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_errors.py -v`
Expected: FAIL with "module 'music_orchestration.errors' not found"

**Step 3: Implement error classes**

Create `services/music-orchestration/music_orchestration/errors.py`:
```python
class MusicServiceError(Exception):
    """Base exception for music service errors"""
    pass


class ModelNotFoundError(MusicServiceError):
    """Requested model not available"""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Model '{model_name}' not found in pool")


class InsufficientVRAMError(MusicServiceError):
    """Not enough GPU memory to load/generate"""
    def __init__(self, required_mb: int, available_mb: int):
        self.required_mb = required_mb
        self.available_mb = available_mb
        super().__init__(
            f"Insufficient VRAM: need {required_mb}MB, have {available_mb}MB"
        )


class GenerationTimeoutError(MusicServiceError):
    """Generation exceeded maximum duration"""
    def __init__(self, duration_seconds: int, max_seconds: int):
        self.duration_seconds = duration_seconds
        self.max_seconds = max_seconds
        super().__init__(
            f"Generation timeout: {duration_seconds}s > {max_seconds}s limit"
        )


class InvalidPromptError(MusicServiceError):
    """Prompt contains blocked content or exceeds length"""
    def __init__(self, reason: str):
        super().__init__(f"Invalid prompt: {reason}")


class ApprovalRequiredError(MusicServiceError):
    """Show music requires manual approval before use"""
    def __init__(self, music_id: str):
        self.music_id = music_id
        super().__init__(f"Music {music_id} requires approval before show use")


class UnauthorizedError(MusicServiceError):
    """User lacks required permission"""
    def __init__(self, required_permission: str):
        super().__init__(f"Unauthorized: requires '{required_permission}' permission")
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_errors.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/errors.py services/music-orchestration/tests/unit/test_errors.py
git commit -m "feat: add error handling classes"
```

---

## Task 5: Cache Manager

**Files:**
- Create: `services/music-orchestration/music_orchestration/cache.py`
- Test: `services/music-orchestration/tests/unit/test_cache.py`

**Step 1: Write cache manager tests**

Create `services/music-orchestration/tests/unit/test_cache.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.cache import CacheManager
from music_orchestration.schemas import MusicRequest, UseCase


@pytest.mark.asyncio
async def test_cache_set_and_get():
    redis_mock = Mock()
    redis_mock.set = AsyncMock()
    redis_mock.get = AsyncMock(return_value=b'{"music_id": "abc-123"}')
    redis_mock.expire = AsyncMock()

    cache = CacheManager(redis_mock)

    await cache.set("test-key", {"music_id": "abc-123"}, ttl=604800)
    result = await cache.get("test-key")

    assert result["music_id"] == "abc-123"
    redis_mock.set.assert_called_once()
    redis_mock.get.assert_called_once()


@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)

    cache = CacheManager(redis_mock)
    result = await cache.get("nonexistent-key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cache_key_from_request():
    redis_mock = Mock()
    cache = CacheManager(redis_mock)

    request = MusicRequest(
        prompt="upbeat electronic",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )

    key = cache.get_cache_key(request)
    assert key == request.cache_key
    assert len(key) == 64  # SHA256 hex length
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_cache.py -v`
Expected: FAIL with "module 'music_orchestration.cache' not found"

**Step 3: Implement cache manager**

Create `services/music-orchestration/music_orchestration/cache.py`:
```python
import json
from typing import Any
from redis.asyncio import Redis
from music_orchestration.schemas import MusicRequest


class CachedAudio(dict):
    """Cached audio metadata"""
    pass


class CacheManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.key_prefix = "music:cache:"
        self.default_ttl = 604800  # 7 days

    def get_cache_key(self, request: MusicRequest) -> str:
        """Get cache key from request"""
        return f"{self.key_prefix}{request.cache_key}"

    async def get(self, cache_key: str) -> CachedAudio | None:
        """Get cached audio if exists"""
        data = await self.redis.get(cache_key)
        if data:
            return CachedAudio(json.loads(data))
        return None

    async def set(
        self,
        cache_key: str,
        audio: dict[str, Any],
        ttl: int | None = None
    ) -> None:
        """Cache audio metadata"""
        ttl = ttl or self.default_ttl
        await self.redis.set(cache_key, json.dumps(audio), ex=ttl)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching pattern"""
        keys = await self.redis.keys(f"{self.key_prefix}{pattern}")
        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def get_stats(self) -> dict[str, int]:
        """Get cache statistics"""
        info = await self.redis.info("stats")
        return {
            "keys_count": info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
        }
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_cache.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/cache.py services/music-orchestration/tests/unit/test_cache.py
git commit -m "feat: add Redis cache manager"
```

---

## Task 6: Authentication and Authorization

**Files:**
- Create: `services/music-orchestration/music_orchestration/auth.py`
- Test: `services/music-orchestration/tests/unit/test_auth.py`

**Step 1: Write auth tests**

Create `services/music-orchestration/tests/unit/test_auth.py`:
```python
import pytest
from unittest.mock import Mock

from music_orchestration.auth import PermissionChecker, ServiceAuthenticator
from music_orchestration.schemas import Role, UserContext


def test_permission_checker_social_media_user():
    user = UserContext(
        service_name="social_media",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate", "music:use_marketing"]
    )

    assert PermissionChecker.check_permission(user, "music:generate") is True
    assert PermissionChecker.check_permission(user, "music:approve_show") is False


def test_permission_checker_show_operator():
    user = UserContext(
        service_name="operator_console",
        role=Role.SHOW_OPERATOR,
        permissions=["music:generate", "music:approve_show"]
    )

    assert PermissionChecker.check_permission(user, "music:approve_show") is True
    assert PermissionChecker.check_permission(user, "music:manage_models") is False


def test_permission_checker_admin():
    user = UserContext(
        service_name="admin",
        role=Role.ADMIN,
        permissions=["*"]
    )

    assert PermissionChecker.check_permission(user, "music:anything") is True
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_auth.py -v`
Expected: FAIL with "module 'music_orchestration.auth' not found"

**Step 3: Implement auth module**

Create `services/music-orchestration/music_orchestration/auth.py`:
```python
import os
from typing import Callable
from jwt import decode, InvalidTokenError
from fastapi import HTTPException, status
from music_orchestration.schemas import Role, UserContext


class PermissionChecker:
    """Role-based permission checking"""

    PERMISSIONS = {
        Role.SOCIAL_MEDIA_USER: [
            "music:generate",
            "music:use_marketing",
            "music:view_own"
        ],
        Role.SHOW_OPERATOR: [
            "music:generate",
            "music:approve_show",
            "music:use_show",
            "music:view_all"
        ],
        Role.DEVELOPER: [
            "music:generate",
            "music:manage_models",
            "music:view_all",
            "music:clear_cache"
        ],
        Role.ADMIN: ["*"]
    }

    @classmethod
    def check_permission(cls, user: UserContext, permission: str) -> bool:
        """Check if user has permission"""
        user_permissions = cls.PERMISSIONS.get(user.role, [])

        # Admin has all permissions
        if "*" in user_permissions:
            return True

        return permission in user_permissions

    @classmethod
    def require_permission(cls, permission: str) -> Callable[[UserContext], None]:
        """Return a function that checks permission and raises if missing"""
        def check(user: UserContext) -> None:
            if not cls.check_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        return check


class ServiceAuthenticator:
    """JWT-based service authentication"""

    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET", "dev-secret")
        self.algorithm = "HS256"

    def validate_token(self, token: str) -> UserContext:
        """Validate JWT token and return user context"""
        try:
            payload = decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return UserContext(
                service_name=payload["sub"],
                role=Role(payload["role"]),
                permissions=payload.get("permissions", [])
            )
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token payload: missing {e}"
            )
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_auth.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/auth.py services/music-orchestration/tests/unit/test_auth.py
git commit -m "feat: add authentication and authorization"
```

---

## Task 7: Model Pool Manager (Generation Service)

**Files:**
- Create: `services/music-generation/music_generation/models.py`
- Test: `services/music-generation/tests/unit/test_models.py`

**Step 1: Write model pool tests**

Create `services/music-generation/tests/unit/test_models.py`:
```python
import pytest
from unittest.mock import Mock, patch

from music_generation.models import ModelPoolManager, ModelInfo


@pytest.mark.asyncio
async def test_load_model():
    manager = ModelPoolManager(vram_limit_mb=8192)

    with patch.object(manager, "_load_model_from_disk", return_value=Mock()):
        await manager.load_model("musicgen")

    assert "musicgen" in manager.loaded_models
    assert manager.get_model_info("musicgen") is not None


@pytest.mark.asyncio
async def test_load_model_insufficient_vram():
    manager = ModelPoolManager(vram_limit_mb=100)

    with patch.object(manager, "_load_model_from_disk", return_value=Mock()):
        manager.model_requirements = {"musicgen": 2048}  # 2GB required
        with pytest.raises(InsufficientVRAMError):
            await manager.load_model("musicgen")


@pytest.mark.asyncio
async def test_estimate_vram_usage():
    manager = ModelPoolManager()
    manager.model_requirements = {"musicgen": 2048, "acestep": 4096}

    await manager.load_model("musicgen")
    usage = manager.estimate_vram_usage()

    assert usage["musicgen"] == 2048
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-generation && pytest tests/unit/test_models.py -v`
Expected: FAIL with "module 'music_generation.models' not found"

**Step 3: Implement model pool manager**

Create `services/music-generation/music_generation/models.py`:
```python
import asyncio
from typing import Dict
from music_generation.errors import InsufficientVRAMError, ModelNotFoundError


class ModelInfo:
    """Metadata about a loaded model"""
    def __init__(
        self,
        name: str,
        vram_usage_mb: int,
        sample_rate: int = 44100,
        max_duration_seconds: int = 300
    ):
        self.name = name
        self.vram_usage_mb = vram_usage_mb
        self.sample_rate = sample_rate
        self.max_duration_seconds = max_duration_seconds


class ModelPoolManager:
    """Manages multiple AI music models with lazy loading"""

    def __init__(self, vram_limit_mb: int = 16384):
        self.vram_limit_mb = vram_limit_mb
        self.loaded_models: Dict[str, any] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self._load_lock = asyncio.Lock()

    async def load_model(self, model_name: str) -> ModelInfo:
        """Load model into memory"""
        async with self._load_lock:
            if model_name in self.loaded_models:
                return self.model_info[model_name]

            # Check VRAM availability
            required_vram = self._get_model_vram_requirement(model_name)
            current_usage = sum(info.vram_usage_mb for info in self.model_info.values())

            if current_usage + required_vram > self.vram_limit_mb:
                raise InsufficientVRAMError(
                    required_mb=current_usage + required_vram,
                    available_mb=self.vram_limit_mb
                )

            # Load the model
            model = await self._load_model_from_disk(model_name)
            info = ModelInfo(
                name=model_name,
                vram_usage_mb=required_vram
            )

            self.loaded_models[model_name] = model
            self.model_info[model_name] = info

            return info

    async def unload_model(self, model_name: str) -> None:
        """Unload model from memory"""
        if model_name not in self.loaded_models:
            raise ModelNotFoundError(model_name)

        del self.loaded_models[model_name]
        del self.model_info[model_name]

    def get_model_info(self, model_name: str) -> ModelInfo | None:
        """Get model metadata"""
        return self.model_info.get(model_name)

    def estimate_vram_usage(self) -> Dict[str, int]:
        """Estimate current VRAM usage"""
        return {
            name: info.vram_usage_mb
            for name, info in self.model_info.items()
        }

    def _get_model_vram_requirement(self, model_name: str) -> int:
        """Get VRAM requirement for model"""
        requirements = {
            "musicgen": 2048,   # ~2GB
            "acestep": 4096,    # ~4GB
        }
        return requirements.get(model_name, 2048)

    async def _load_model_from_disk(self, model_name: str):
        """Load model from disk (placeholder for actual implementation)"""
        # This will be implemented with actual model loading
        await asyncio.sleep(0.1)  # Simulate loading time
        return {"name": model_name, "loaded": True}
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-generation && pytest tests/unit/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-generation/music_generation/models.py services/music-generation/tests/unit/test_models.py
git commit -m "feat: add model pool manager"
```

---

## Task 8: Inference Engine (Generation Service)

**Files:**
- Create: `services/music-generation/music_generation/inference.py`
- Test: `services/music-generation/tests/unit/test_inference.py`

**Step 1: Write inference tests**

Create `services/music-generation/tests/unit/test_inference.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

from music_generation.inference import InferenceEngine
from music_generation.schemas import GenerationParams


@pytest.mark.asyncio
async def test_generate_music():
    model_mock = Mock()
    model_mock.generate = AsyncMock(return_value=b"fake audio data")

    engine = InferenceEngine(models={"musicgen": model_mock})
    result = await engine.generate(
        model_name="musicgen",
        prompt="upbeat electronic",
        params=GenerationParams(duration_seconds=30)
    )

    assert result.audio_data == b"fake audio data"
    assert result.duration_seconds == 30


@pytest.mark.asyncio
async def test_generate_with_cancel():
    engine = InferenceEngine(models={})

    request_id = await engine.start_generation("musicgen", "test", {})
    result = await engine.cancel_generation(request_id)

    assert result is True
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-generation && pytest tests/unit/test_inference.py -v`
Expected: FAIL with "module 'music_generation.inference' not found"

**Step 3: Implement inference engine**

Create `services/music-generation/music_generation/inference.py`:
```python
import asyncio
import uuid
from typing import Dict, Optional
from dataclasses import dataclass

from music_generation.models import ModelPoolManager
from music_generation.schemas import GenerationParams


@dataclass
class AudioResult:
    """Result of music generation"""
    audio_data: bytes
    duration_seconds: float
    sample_rate: int
    format: str


class InferenceEngine:
    """Runs generation on loaded models"""

    def __init__(self, model_pool: ModelPoolManager):
        self.model_pool = model_pool
        self.active_generations: Dict[str, asyncio.Task] = {}

    async def generate(
        self,
        model_name: str,
        prompt: str,
        params: GenerationParams
    ) -> AudioResult:
        """Generate music with given model and prompt"""
        # Ensure model is loaded
        await self.model_pool.load_model(model_name)

        # Create generation task
        request_id = str(uuid.uuid4())
        task = asyncio.create_task(
            self._generate_audio(model_name, prompt, params, request_id)
        )
        self.active_generations[request_id] = task

        try:
            result = await asyncio.wait_for(
                task,
                timeout=params.duration_seconds + 60  # Generation timeout
            )
            return result
        finally:
            del self.active_generations[request_id]

    async def start_generation(
        self,
        model_name: str,
        prompt: str,
        params: dict
    ) -> str:
        """Start async generation and return request ID"""
        request_id = str(uuid.uuid4())
        task = asyncio.create_task(
            self._generate_audio(
                model_name,
                prompt,
                GenerationParams(**params),
                request_id
            )
        )
        self.active_generations[request_id] = task
        return request_id

    async def cancel_generation(self, request_id: str) -> bool:
        """Cancel active generation"""
        if request_id in self.active_generations:
            task = self.active_generations[request_id]
            task.cancel()
            del self.active_generations[request_id]
            return True
        return False

    async def _generate_audio(
        self,
        model_name: str,
        prompt: str,
        params: GenerationParams,
        request_id: str
    ) -> AudioResult:
        """Internal method to generate audio (placeholder)"""
        # This will be implemented with actual model inference
        await asyncio.sleep(0.5)  # Simulate generation time

        # Return fake audio for now
        return AudioResult(
            audio_data=b"generated_audio_placeholder",
            duration_seconds=params.duration_seconds,
            sample_rate=44100,
            format="wav"
        )
```

**Step 4: Add generation params schema**

Create `services/music-generation/music_generation/schemas.py`:
```python
from pydantic import BaseModel, Field


class GenerationParams(BaseModel):
    duration_seconds: int = Field(..., ge=15, le=300)
    format: str = Field(default="wav")
    sample_rate: int = Field(default=44100)
```

**Step 5: Run tests to verify they pass**

Run: `cd services/music-generation && pytest tests/unit/test_inference.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add services/music-generation/music_generation/inference.py services/music-generation/music_generation/schemas.py services/music-generation/tests/unit/test_inference.py
git commit -m "feat: add inference engine"
```

---

## Task 9: Audio Processor

**Files:**
- Create: `services/music-generation/music_generation/audio.py`
- Test: `services/music-generation/tests/unit/test_audio.py`

**Step 1: Write audio processor tests**

Create `services/music-generation/tests/unit/test_audio.py`:
```python
import pytest
import numpy as np

from music_generation.audio import AudioProcessor


def test_normalize_audio():
    processor = AudioProcessor()

    # Create fake audio (stereo, 44100 Hz, 1 second)
    audio = np.random.randn(2, 44100).astype(np.float32) * 0.5
    normalized = processor.normalize(audio)

    # Check peak is within range
    assert np.max(np.abs(normalized)) <= 1.0


def test_trim_silence():
    processor = AudioProcessor()

    # Create audio with silence at start/end
    audio = np.zeros((2, 44100), dtype=np.float32)
    audio[:, 1000:-1000] = 0.5  # Add signal in middle

    trimmed = processor.trim_silence(audio, threshold_db=-40)

    # Should be shorter
    assert trimmed.shape[1] < audio.shape[1]
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-generation && pytest tests/unit/test_audio.py -v`
Expected: FAIL with "module 'music_generation.audio' not found"

**Step 3: Implement audio processor**

Create `services/music-generation/music_generation/audio.py`:
```python
import numpy as np
import soundfile as sf
from io import BytesIO


class AudioProcessor:
    """Post-processing: format conversion, normalization, trimming"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to -1.0 to 1.0 range"""
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio / peak
        return audio

    def trim_silence(
        self,
        audio: np.ndarray,
        threshold_db: float = -40.0
    ) -> np.ndarray:
        """Trim silence from start and end of audio"""
        # Calculate RMS in dB
        rms = np.sqrt(np.mean(audio ** 2, axis=0))
        threshold = 10 ** (threshold_db / 20)

        # Find non-silent regions
        non_silent = rms > threshold

        if not np.any(non_silent):
            return audio

        # Find first and last non-silent sample
        first = np.argmax(non_silent)
        last = len(non_silent) - np.argmax(non_silent[::-1])

        return audio[:, first:last]

    def convert_format(
        self,
        audio: np.ndarray,
        output_format: str = "mp3",
        bitrate: int = 192
    ) -> bytes:
        """Convert audio to specified format and return bytes"""
        buffer = BytesIO()

        if output_format == "mp3":
            # Use soundfile to write WAV, then convert to MP3
            # (For now, just return WAV bytes)
            sf.write(buffer, audio.T, self.sample_rate, format="WAV")
        else:
            sf.write(buffer, audio.T, self.sample_rate, format=output_format.upper())

        return buffer.getvalue()

    def extract_preview(
        self,
        audio: np.ndarray,
        start_sec: float = 0.0,
        duration: float = 10.0
    ) -> np.ndarray:
        """Extract a preview clip from audio"""
        start_sample = int(start_sec * self.sample_rate)
        end_sample = int((start_sec + duration) * self.sample_rate)

        return audio[:, start_sample:end_sample]
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-generation && pytest tests/unit/test_audio.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-generation/music_generation/audio.py services/music-generation/tests/unit/test_audio.py
git commit -m "feat: add audio processor"
```

---

## Task 10: Music Generation Service API

**Files:**
- Create: `services/music-generation/music_generation/main.py`
- Test: `services/music-generation/tests/integration/test_api.py`

**Step 1: Write API integration tests**

Create `services/music-generation/tests/integration/test_api.py`:
```python
import pytest
from httpx import AsyncClient

from music_generation.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_generate_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/generate", json={
            "model_name": "musicgen",
            "prompt": "upbeat electronic",
            "duration_seconds": 30
        })

    assert response.status_code == 200
    assert "request_id" in response.json()
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-generation && pytest tests/integration/test_api.py -v`
Expected: FAIL with "module 'music_generation.main' not found"

**Step 3: Implement FastAPI application**

Create `services/music-generation/music_generation/main.py`:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog

from music_generation.models import ModelPoolManager
from music_generation.inference import InferenceEngine
from music_generation.audio import AudioProcessor


logger = structlog.get_logger()


class GenerateRequest(BaseModel):
    model_name: str
    prompt: str
    duration_seconds: int = 30
    format: str = "wav"


class GenerateResponse(BaseModel):
    request_id: str
    status: str
    audio_url: str | None = None
    duration_seconds: int


# Global instances
model_pool: ModelPoolManager | None = None
inference_engine: InferenceEngine | None = None
audio_processor: AudioProcessor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global model_pool, inference_engine, audio_processor

    # Initialize
    model_pool = ModelPoolManager()
    inference_engine = InferenceEngine(model_pool)
    audio_processor = AudioProcessor()

    logger.info("music_generation_service_started")

    yield

    # Cleanup
    logger.info("music_generation_service_stopped")


app = FastAPI(
    title="Music Generation Service",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "music-generation",
        "models_loaded": len(model_pool.loaded_models) if model_pool else 0
    }


@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_music(request: GenerateRequest):
    """Generate music with specified model"""
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        result = await inference_engine.generate(
            model_name=request.model_name,
            prompt=request.prompt,
            params=request
        )

        return GenerateResponse(
            request_id="placeholder",
            status="completed",
            audio_url=None,  # Will be implemented with MinIO
            duration_seconds=int(result.duration_seconds)
        )
    except Exception as e:
        logger.error("generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-generation && pytest tests/integration/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-generation/music_generation/main.py services/music-generation/tests/integration/test_api.py
git commit -m "feat: add music generation service API"
```

---

## Task 11: Request Router (Orchestration Service)

**Files:**
- Create: `services/music-orchestration/music_orchestration/router.py`
- Test: `services/music-orchestration/tests/unit/test_router.py`

**Step 1: Write router tests**

Create `services/music-orchestration/tests/unit/test_router.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.router import RequestRouter
from music_orchestration.schemas import MusicRequest, UseCase, UserContext, Role


@pytest.mark.asyncio
async def test_route_to_cache_hit():
    cache_mock = Mock()
    cache_mock.get = AsyncMock(return_value={"music_id": "cached-123"})

    router = RequestRouter(cache=cache_mock)
    request = MusicRequest(
        prompt="upbeat electronic",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    user = UserContext(
        service_name="test",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate"]
    )

    response = await router.route(request, user)

    assert response["was_cache_hit"] is True
    assert response["music_id"] == "cached-123"


@pytest.mark.asyncio
async def test_route_to_generation_on_cache_miss():
    cache_mock = Mock()
    cache_mock.get = AsyncMock(return_value=None)
    generation_mock = Mock()
    generation_mock.generate = AsyncMock(return_value={"music_id": "new-123"})

    router = RequestRouter(cache=cache_mock, generation_client=generation_mock)
    request = MusicRequest(
        prompt="new prompt",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    user = UserContext(
        service_name="test",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate"]
    )

    response = await router.route(request, user)

    assert response["was_cache_hit"] is False
    assert response["music_id"] == "new-123"
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_router.py -v`
Expected: FAIL with "module 'music_orchestration.router' not found"

**Step 3: Implement request router**

Create `services/music-orchestration/music_orchestration/router.py`:
```python
from typing import Any
from music_orchestration.cache import CacheManager
from music_orchestration.schemas import MusicRequest, UserContext, UseCase
from music_orchestration.auth import PermissionChecker


class RequestRouter:
    """Routes requests to cache or generation service"""

    def __init__(
        self,
        cache: CacheManager,
        generation_client: Any | None = None
    ):
        self.cache = cache
        self.generation_client = generation_client

    async def route(
        self,
        request: MusicRequest,
        user: UserContext
    ) -> dict[str, Any]:
        """Route request to cache or generation"""
        # Check permissions
        PermissionChecker.require_permission("music:generate")(user)

        # Check cache first
        cache_key = self.cache.get_cache_key(request)
        cached = await self.cache.get(cache_key)

        if cached:
            return {
                "music_id": cached.get("music_id"),
                "status": "cached",
                "was_cache_hit": True
            }

        # Route to generation
        if not self.generation_client:
            return {
                "music_id": None,
                "status": "error",
                "error": "Generation service not available"
            }

        # Select model based on use case
        model_name = self._select_model(request.use_case)

        # Call generation service
        result = await self.generation_client.generate(
            model_name=model_name,
            prompt=request.prompt,
            duration_seconds=request.duration_seconds
        )

        return {
            "music_id": result.get("music_id"),
            "status": "generating",
            "was_cache_hit": False
        }

    def _select_model(self, use_case: UseCase) -> str:
        """Select model based on use case"""
        if use_case == UseCase.MARKETING:
            return "musicgen"
        return "acestep"
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_router.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/router.py services/music-orchestration/tests/unit/test_router.py
git commit -m "feat: add request router"
```

---

## Task 12: Approval Pipeline

**Files:**
- Create: `services/music-orchestration/music_orchestration/approval.py`
- Test: `services/music-orchestration/tests/unit/test_approval.py`

**Step 1: Write approval tests**

Create `services/music-orchestration/tests/unit/test_approval.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from music_orchestration.approval import ApprovalPipeline
from music_orchestration.schemas import UseCase


@pytest.mark.asyncio
async def test_marketing_auto_approves():
    db_mock = Mock()
    db_mock.execute = AsyncMock()

    pipeline = ApprovalPipeline(database=db_mock)

    result = await pipeline.submit_for_approval(
        music_id=str(uuid4()),
        use_case=UseCase.MARKETING
    )

    assert result["status"] == "approved"
    assert result["auto_approved"] is True


@pytest.mark.asyncio
async def test_show_requires_manual_approval():
    db_mock = Mock()
    db_mock.execute = AsyncMock()

    pipeline = ApprovalPipeline(database=db_mock)

    result = await pipeline.submit_for_approval(
        music_id=str(uuid4()),
        use_case=UseCase.SHOW
    )

    assert result["status"] == "pending_approval"
    assert result["auto_approved"] is False
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_approval.py -v`
Expected: FAIL with "module 'music_orchestration.approval' not found"

**Step 3: Implement approval pipeline**

Create `services/music-orchestration/music_orchestration/approval.py`:
```python
from uuid import UUID
from music_orchestration.schemas import UseCase
from music_orchestration.database import get_session_maker


class ApprovalPipeline:
    """Staged approval: marketing auto-approves, show requires manual"""

    def __init__(self, database=None):
        self.session_maker = database or get_session_maker()

    async def submit_for_approval(
        self,
        music_id: str,
        use_case: UseCase,
        user_id: UUID | None = None
    ) -> dict:
        """Submit music for approval based on use case"""
        if use_case == UseCase.MARKETING:
            # Auto-approve marketing content
            return {
                "music_id": music_id,
                "status": "approved",
                "auto_approved": True
            }

        # Show content requires manual approval
        return {
            "music_id": music_id,
            "status": "pending_approval",
            "auto_approved": False
        }

    async def approve(
        self,
        music_id: str,
        user_id: UUID,
        reason: str | None = None
    ) -> dict:
        """Manually approve show music"""
        async with self.session_maker() as session:
            # Update music_generations table
            # Log to music_approvals table
            pass

        return {
            "music_id": music_id,
            "status": "approved",
            "approved_by": str(user_id)
        }

    async def reject(
        self,
        music_id: str,
        user_id: UUID,
        reason: str
    ) -> dict:
        """Reject show music"""
        async with self.session_maker() as session:
            # Update music_generations table
            # Log to music_approvals table
            pass

        return {
            "music_id": music_id,
            "status": "rejected",
            "rejected_by": str(user_id),
            "reason": reason
        }

    async def get_pending_approvals(self, user_role: str) -> list[dict]:
        """Get list of pending approvals"""
        async with self.session_maker() as session:
            # Query music_generations where approval_status = 'pending_approval'
            pass

        return []
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_approval.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/approval.py services/music-orchestration/tests/unit/test_approval.py
git commit -m "feat: add approval pipeline"
```

---

## Task 13: Music Orchestration Service API

**Files:**
- Create: `services/music-orchestration/music_orchestration/main.py`
- Test: `services/music-orchestration/tests/integration/test_api.py`

**Step 1: Write API integration tests**

Create `services/music-orchestration/tests/integration/test_api.py`:
```python
import pytest
from httpx import AsyncClient

from music_orchestration.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_generate_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/music/generate",
            json={
                "prompt": "upbeat electronic",
                "use_case": "marketing",
                "duration_seconds": 30
            },
            headers={"Authorization": "Bearer test-token"}
        )

    assert response.status_code in [200, 202]
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/integration/test_api.py -v`
Expected: FAIL with "module 'music_orchestration.main' not found"

**Step 3: Implement FastAPI application**

Create `services/music-orchestration/music_orchestration/main.py`:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import structlog

from music_orchestration.router import RequestRouter
from music_orchestration.cache import CacheManager
from music_orchestration.auth import ServiceAuthenticator, PermissionChecker
from music_orchestration.approval import ApprovalPipeline
from music_orchestration.schemas import (
    MusicRequest,
    MusicResponse,
    UserContext,
    Role
)


logger = structlog.get_logger()


# Global instances
cache_manager: CacheManager | None = None
request_router: RequestRouter | None = None
authenticator: ServiceAuthenticator | None = None
approval_pipeline: ApprovalPipeline | None = None


async def get_authorization(
    authorization: str = Header(...)
) -> UserContext:
    """Extract and validate authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    if not authenticator:
        # For testing, return fake context
        return UserContext(
            service_name="test",
            role=Role.ADMIN,
            permissions=["*"]
        )

    return authenticator.validate_token(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global cache_manager, request_router, authenticator, approval_pipeline

    # Initialize (placeholder - will connect to actual Redis/DB)
    # cache_manager = CacheManager(redis_client)
    # request_router = RequestRouter(cache=cache_manager)
    # authenticator = ServiceAuthenticator()
    # approval_pipeline = ApprovalPipeline()

    logger.info("music_orchestration_service_started")

    yield

    logger.info("music_orchestration_service_stopped")


app = FastAPI(
    title="Music Orchestration Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "music-orchestration"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "checks": {
            "cache": cache_manager is not None,
            "router": request_router is not None,
            "auth": authenticator is not None
        }
    }


@app.post("/api/v1/music/generate", response_model=MusicResponse)
async def generate_music(
    request: MusicRequest,
    user: UserContext = Depends(get_authorization)
):
    """Generate music with caching and approval"""
    PermissionChecker.require_permission("music:generate")(user)

    if not request_router:
        raise HTTPException(status_code=503, detail="Service not ready")

    result = await request_router.route(request, user)

    return MusicResponse(
        request_id=result.get("request_id", "placeholder"),
        music_id=result.get("music_id"),
        status=result.get("status", "generating"),
        audio_url=result.get("audio_url"),
        duration_seconds=request.duration_seconds,
        format=request.format,
        was_cache_hit=result.get("was_cache_hit", False)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/integration/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/main.py services/music-orchestration/tests/integration/test_api.py
git commit -m "feat: add music orchestration service API"
```

---

## Task 14: MinIO Storage Integration

**Files:**
- Create: `services/music-orchestration/music_orchestration/storage.py`
- Test: `services/music-orchestration/tests/unit/test_storage.py`

**Step 1: Write storage tests**

Create `services/music-orchestration/tests/unit/test_storage.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

from music_orchestration.storage import MinIOStorage


@pytest.mark.asyncio
async def test_upload_audio():
    minio_mock = Mock()
    minio_mock.put_object = AsyncMock()

    storage = MinIOStorage(client=minio_mock)

    await storage.upload_audio(
        key="test/audio.mp3",
        audio_data=b"fake audio",
        metadata={"duration": "30"}
    )

    minio_mock.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_generate_presigned_url():
    minio_mock = Mock()
    minio_mock.presigned_get_object = Mock(return_value="https://minio/audio.mp3")

    storage = MinIOStorage(client=minio_mock)

    url = await storage.get_presigned_url("test/audio.mp3")

    assert url == "https://minio/audio.mp3"
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_storage.py -v`
Expected: FAIL with "module 'music_orchestration.storage' not found"

**Step 3: Implement MinIO storage**

Create `services/music-orchestration/music_orchestration/storage.py`:
```python
from datetime import timedelta
from typing import Any
from minio import Minio
from minio.helpers import ObjectWriteResult


class MinIOStorage:
    """MinIO/S3 storage for audio files"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "chimeramusic"
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket = bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            # Create folder structure
            self._create_folders()

    def _create_folders(self):
        """Create initial folder structure"""
        folders = ["marketing/social", "marketing/promotional",
                   "show/underscore", "show/transitions", "show/approved",
                   "previews"]
        for folder in folders:
            self.client.put_object(
                self.bucket,
                f"{folder}/.keep",
                data=b"",
                length=0
            )

    async def upload_audio(
        self,
        key: str,
        audio_data: bytes,
        metadata: dict[str, str] | None = None
    ) -> str:
        """Upload audio file and return path"""
        from io import BytesIO

        data = BytesIO(audio_data)
        length = len(audio_data)

        result: ObjectWriteResult = self.client.put_object(
            self.bucket,
            key,
            data=data,
            length=length,
            metadata=metadata or {}
        )

        return result.object_name

    async def get_presigned_url(
        self,
        key: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate presigned URL for download"""
        return self.client.presigned_get_object(
            self.bucket,
            key,
            expires=expires
        )

    async def delete_audio(self, key: str) -> None:
        """Delete audio file"""
        self.client.remove_object(self.bucket, key)

    def get_key_for_use_case(
        self,
        use_case: str,
        music_id: str,
        format: str = "mp3"
    ) -> str:
        """Generate storage key based on use case"""
        if use_case == "marketing":
            return f"marketing/social/{music_id}.{format}"
        return f"show/underscore/{music_id}.{format}"
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_storage.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/music-orchestration/music_orchestration/storage.py services/music-orchestration/tests/unit/test_storage.py
git commit -m "feat: add MinIO storage integration"
```

---

## Task 15: WebSocket Progress Streaming

**Files:**
- Create: `services/music-orchestration/music_orchestration/websocket.py`
- Test: `services/music-orchestration/tests/unit/test_websocket.py`

**Step 1: Write WebSocket tests**

Create `services/music-orchestration/tests/unit/test_websocket.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.websocket import MusicWebSocket


@pytest.mark.asyncio
async def test_subscribe_to_progress():
    ws = MusicWebSocket()
    ws.subscribe("request-123")

    assert "request-123" in ws.active_subscriptions


@pytest.mark.asyncio
async def test_publish_progress():
    ws = MusicWebSocket()
    ws.subscribe("request-123")

    await ws.publish_progress(
        request_id="request-123",
        progress=50,
        stage="inference"
    )

    # Verify progress was stored/queued
    assert ws.get_progress("request-123")["progress"] == 50
```

**Step 2: Run tests to verify they fail**

Run: `cd services/music-orchestration && pytest tests/unit/test_websocket.py -v`
Expected: FAIL with "module 'music_orchestration.websocket' not found"

**Step 3: Implement WebSocket streaming**

Create `services/music-orchestration/music_orchestration/websocket.py`:
```python
from typing import Dict, Set
from fastapi import WebSocket
import structlog

from music_orchestration.schemas import GenerationProgress


logger = structlog.get_logger()


class MusicWebSocket:
    """WebSocket manager for real-time progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.progress_state: Dict[str, dict] = {}

    async def subscribe(self, request_id: str, websocket: WebSocket) -> None:
        """Subscribe to progress updates for a request"""
        if request_id not in self.active_connections:
            self.active_connections[request_id] = set()

        self.active_connections[request_id].add(websocket)
        logger.info("websocket_subscribed", request_id=request_id)

    async def unsubscribe(self, request_id: str, websocket: WebSocket) -> None:
        """Unsubscribe from progress updates"""
        if request_id in self.active_connections:
            self.active_connections[request_id].discard(websocket)

            if not self.active_connections[request_id]:
                del self.active_connections[request_id]

    async def publish_progress(
        self,
        request_id: str,
        progress: int | None = None,
        stage: str | None = None,
        eta_seconds: int | None = None,
        error: str | None = None
    ) -> None:
        """Publish progress update to all subscribers"""
        msg = GenerationProgress(
            request_id=request_id,
            type="progress" if error is None else "failed",
            progress=progress,
            stage=stage,
            eta_seconds=eta_seconds,
            error=error
        )

        # Store state
        self.progress_state[request_id] = {
            "progress": progress,
            "stage": stage,
            "eta_seconds": eta_seconds,
            "error": error
        }

        # Send to all subscribers
        if request_id in self.active_connections:
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_json(msg.model_dump())
                except Exception as e:
                    logger.error("websocket_send_failed", request_id=request_id, error=str(e))

    def get_progress(self, request_id: str) -> dict | None:
        """Get current progress state"""
        return self.progress_state.get(request_id)

    async def broadcast_complete(self, request_id: str, music_id: str) -> None:
        """Broadcast completion message"""
        msg = GenerationProgress(
            request_id=request_id,
            type="completed",
            progress=100
        )

        if request_id in self.active_connections:
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_json({
                        **msg.model_dump(),
                        "music_id": music_id
                    })
                except Exception as e:
                    logger.error("websocket_send_failed", request_id=request_id, error=str(e))

        # Clean up
        self.progress_state.pop(request_id, None)


# Global instance
websocket_manager = MusicWebSocket()
```

**Step 4: Run tests to verify they pass**

Run: `cd services/music-orchestration && pytest tests/unit/test_websocket.py -v`
Expected: PASS

**Step 5: Add WebSocket route to main.py**

Edit `services/music-orchestration/music_orchestration/main.py`:
```python
from fastapi import WebSocket, WebSocketDisconnect
from music_orchestration.websocket import websocket_manager


@app.websocket("/ws/music/{request_id}")
async def websocket_music_progress(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    await websocket_manager.subscribe(request_id, websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.unsubscribe(request_id, websocket)
```

**Step 6: Commit**

```bash
git add services/music-orchestration/music_orchestration/websocket.py services/music-orchestration/music_orchestration/main.py services/music-orchestration/tests/unit/test_websocket.py
git commit -m "feat: add WebSocket progress streaming"
```

---

## Task 16: Kubernetes Deployment Manifests

**Files:**
- Create: `services/music-generation/manifests/k8s.yaml`
- Create: `services/music-orchestration/manifests/k8s.yaml`
- Create: `services/music-orchestration/manifests/network-policy.yaml`

**Step 1: Create music-generation k8s manifest**

Create `services/music-generation/manifests/k8s.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chimera
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
  namespace: chimera
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: music-generation
  namespace: chimera
  labels:
    app: music-generation
    version: v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: music-generation
  template:
    metadata:
      labels:
        app: music-generation
        version: v1
    spec:
      containers:
      - name: music-generation
        image: chimera/music-generation:latest
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8011
          protocol: TCP
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "2000m"
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "4000m"
        env:
        - name: MODEL_POOL_SIZE
          value: "2"
        - name: MAX_CONCURRENT_GENERATIONS
          value: "4"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: chimera-secrets
              key: redis-url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chimera-secrets
              key: database-url
        - name: MINIO_ENDPOINT
          value: "minio.chimera.svc.cluster.local:9000"
        volumeMounts:
        - name: model-cache
          mountPath: /models
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      nodeSelector:
        gpu: "nvidia"
---
apiVersion: v1
kind: Service
metadata:
  name: music-generation
  namespace: chimera
  labels:
    app: music-generation
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8011
    targetPort: http
    protocol: TCP
  selector:
    app: music-generation
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: music-generation-hpa
  namespace: chimera
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: music-generation
  minReplicas: 1
  maxReplicas: 2
  metrics:
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 80
```

**Step 2: Create music-orchestration k8s manifest**

Create `services/music-orchestration/manifests/k8s.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: music-orchestration
  namespace: chimera
  labels:
    app: music-orchestration
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: music-orchestration
  template:
    metadata:
      labels:
        app: music-orchestration
        version: v1
    spec:
      containers:
      - name: music-orchestration
        image: chimera/music-orchestration:latest
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8012
          protocol: TCP
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        env:
        - name: GENERATION_SERVICE_URL
          value: "http://music-generation.chimera.svc.cluster.local:8011"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: chimera-secrets
              key: redis-url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chimera-secrets
              key: database-url
        - name: MINIO_ENDPOINT
          value: "minio.chimera.svc.cluster.local:9000"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: chimera-secrets
              key: jwt-secret
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 3
          timeoutSeconds: 2
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: music-orchestration
  namespace: chimera
  labels:
    app: music-orchestration
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8012
    targetPort: http
    protocol: TCP
  selector:
    app: music-orchestration
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: music-orchestration-hpa
  namespace: chimera
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: music-orchestration
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Step 3: Create network policy**

Create `services/music-orchestration/manifests/network-policy.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: music-orchestration-policy
  namespace: chimera
spec:
  podSelector:
    matchLabels:
      app: music-orchestration
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: chimera
    ports:
    - protocol: TCP
      port: 8012
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: chimera
    ports:
    - protocol: TCP
      port: 5432   # PostgreSQL
    - protocol: TCP
      port: 6379   # Redis
    - protocol: TCP
      port: 9000   # MinIO
    - protocol: TCP
      port: 8011   # Music Generation Service
```

**Step 4: Commit**

```bash
git add services/music-generation/manifests/ services/music-orchestration/manifests/
git commit -m "feat: add Kubernetes deployment manifests"
```

---

## Task 17: Docker Build Files

**Files:**
- Create: `services/music-generation/Dockerfile`
- Create: `services/music-orchestration/Dockerfile`

**Step 1: Create music-generation Dockerfile**

Create `services/music-generation/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY music_generation/ ./music_generation/

# Create model cache directory
RUN mkdir -p /models

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# Run application
CMD ["uvicorn", "music_generation.main:app", "--host", "0.0.0.0", "--port", "8011"]
```

**Step 2: Create music-orchestration Dockerfile**

Create `services/music-orchestration/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY music_orchestration/ ./music_orchestration/

# Expose port
EXPOSE 8012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

# Run application
CMD ["uvicorn", "music_orchestration.main:app", "--host", "0.0.0.0", "--port", "8012"]
```

**Step 3: Commit**

```bash
git add services/music-generation/Dockerfile services/music-orchestration/Dockerfile
git commit -m "feat: add Dockerfiles"
```

---

## Task 18: Documentation

**Files:**
- Create: `services/music-orchestration/reference/api.md`
- Create: `services/music-orchestration/reference/runbooks/deployment.md`
- Create: `docs/music-platform/README.md`

**Step 1: Create API documentation**

Create `services/music-orchestration/reference/api.md`:
```markdown
# Music Orchestration Service - API Documentation

## Base URL
```
http://music-orchestration.chimera.svc.cluster.local:8012
```

## Authentication
All endpoints require JWT bearer token:
```
Authorization: Bearer <token>
```

## Endpoints

### POST /api/v1/music/generate
Generate music with caching and approval.

**Request:**
```json
{
  "prompt": "upbeat electronic background",
  "use_case": "marketing",
  "duration_seconds": 30,
  "format": "mp3",
  "genre": "electronic",
  "mood": "upbeat",
  "tempo": 120
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "music_id": "uuid",
  "status": "cached",
  "audio_url": "https://...",
  "duration_seconds": 30,
  "format": "mp3",
  "was_cache_hit": true
}
```

### GET /api/v1/music/{music_id}
Get music metadata.

### POST /api/v1/music/{music_id}/approve
Approve show music for use.

### WebSocket /ws/music/{request_id}
Real-time progress updates.

**Message:**
```json
{
  "type": "progress",
  "request_id": "uuid",
  "progress": 50,
  "stage": "inference",
  "eta_seconds": 15
}
```
```

**Step 2: Create deployment guide**

Create `services/music-orchestration/reference/runbooks/deployment.md`:
```markdown
# Music Platform Deployment Guide

## Prerequisites
- k3s cluster
- PostgreSQL database
- Redis
- MinIO
- NVIDIA GPU (for generation service)

## Local Deployment

```bash
# Create database
createdb chimera_music

# Run migrations
psql chimera_music < services/music-orchestration/migrations/001_create_music_tables.sql

# Start services
cd services/music-generation
uvicorn music_generation.main:app --host 0.0.0.0 --port 8011

cd services/music-orchestration
uvicorn music_orchestration.main:app --host 0.0.0.0 --port 8012
```

## Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace chimera

# Create secrets
kubectl create secret generic chimera-secrets \
  --from-literal=database-url='postgresql+asyncpg://user:pass@postgres/chimera_music' \
  --from-literal=redis-url='redis://redis:6379/0' \
  --from-literal=jwt-secret='your-secret' \
  -n chimera

# Apply manifests
kubectl apply -f services/music-generation/manifests/ -n chimera
kubectl apply -f services/music-orchestration/manifests/ -n chimera

# Verify
kubectl get pods -n chimera
```
```

**Step 3: Create platform overview**

Create `docs/music-platform/README.md`:
```markdown
# Chimera Music Platform

AI-powered music generation for Project Chimera.

## Overview
Generates original music locally via AI for social media content and live theatrical performances.

## Services
- **Music Generation Service** (8011): Model inference
- **Music Orchestration Service** (8012): Caching, approval, show integration

## Quick Start

```bash
# Generate music for social media
curl -X POST http://localhost:8012/api/v1/music/generate \
  -H "Authorization: Bearer <token>" \
  -d '{
    "prompt": "upbeat electronic background",
    "use_case": "marketing",
    "duration_seconds": 30
  }'
```

## Documentation
- [API Documentation](../services/music-orchestration/reference/api.md)
- [Deployment Guide](../services/music-orchestration/reference/runbooks/deployment.md)
- [Design Document](../plans/2026-03-01-music-generation-platform-design.md)
```

**Step 4: Commit**

```bash
git add services/music-orchestration/docs/ docs/music-platform/
git commit -m "docs: add music platform documentation"
```

---

## Task 19: Update Main Documentation

**Files:**
- Modify: `docs/README.md`
- Modify: `Backlog_Project_Chimera.md`

**Step 1: Update main docs README**

Add to `docs/README.md`:
```markdown
## Music Platform
- [Music Platform Overview](music-platform/README.md)
- [Music Generation Design](plans/2026-03-01-music-generation-platform-design.md)
```

**Step 2: Update project backlog**

Add to `Backlog_Project_Chimera.md`:
```markdown
### E9: Music Generation Platform
**Goal**: AI-powered local music generation for social media and live shows

**Stories**:
- S9.1: Model pool manager (MusicGen, ACE-Step)
- S9.2: Caching and approval pipeline
- S9.3: WebSocket progress streaming
- S9.4: Sentiment-based adaptive modulation
- S9.5: Operator Console integration
```

**Step 3: Commit**

```bash
git add docs/README.md Backlog_Project_Chimera.md
git commit -m "docs: update main documentation for music platform"
```

---

## Task 20: End-to-End Integration Test

**Files:**
- Create: `services/music-orchestration/tests/integration/test_e2e.py`

**Step 1: Write e2e test**

Create `services/music-orchestration/tests/integration/test_e2e.py`:
```python
import pytest
import asyncio
from httpx import AsyncClient

from music_orchestration.main import app


@pytest.mark.asyncio
async def test_full_generation_flow():
    """Test complete flow from request to response"""

    # 1. Generate music
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/music/generate",
            json={
                "prompt": "test upbeat music",
                "use_case": "marketing",
                "duration_seconds": 30
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code in [200, 202]
        data = response.json()
        assert "request_id" in data

        # 2. Check status (if generating)
        if data["status"] == "generating":
            status_response = await client.get(f"/api/v1/music/{data['music_id']}")
            assert status_response.status_code == 200
```

**Step 2: Run e2e test**

Run: `cd services/music-orchestration && pytest tests/integration/test_e2e.py -v`
Expected: PASS (may require mock services)

**Step 3: Commit**

```bash
git add services/music-orchestration/tests/integration/test_e2e.py
git commit -m "test: add end-to-end integration test"
```

---

## Task 21: Final Verification

**Files:**
- Test: All services
- Test: All manifests valid

**Step 1: Run all tests**

```bash
cd services/music-generation && pytest tests/ -v --cov=music_generation
cd services/music-orchestration && pytest tests/ -v --cov=music_orchestration
```

Expected: All tests pass, coverage > 95%

**Step 2: Validate Kubernetes manifests**

```bash
kubectl apply --dry-run=client -f services/music-generation/manifests/k8s.yaml
kubectl apply --dry-run=client -f services/music-orchestration/manifests/k8s.yaml
```

Expected: No errors

**Step 3: Verify documentation**

```bash
# Check all docs exist and are readable
cat docs/music-platform/README.md
cat services/music-orchestration/reference/api.md
cat docs/plans/2026-03-01-music-generation-platform-design.md
```

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete music generation platform implementation"
```

**Step 5: Create tag**

```bash
git tag -a v0.1.0-music-platform -m "Music Generation Platform v0.1.0"
git push origin v0.1.0-music-platform
```

---

## Definition of Done Checklist

- [ ] All tasks completed
- [ ] All tests passing with >95% coverage
- [ ] Quality Platform gates passing
- [ ] Documentation complete (API, deployment, README)
- [ ] Kubernetes manifests validated
- [ ] Dockerfiles build successfully
- [ ] Integration with SceneSpeak, Operator Console, Sentiment Analysis documented
- [ ] Code committed and tagged
- [ ] Design document linked from main docs
