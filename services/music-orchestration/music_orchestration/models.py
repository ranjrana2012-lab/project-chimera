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
