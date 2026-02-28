"""SQLAlchemy ORM models for Chimera Quality Platform."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, ForeignKey, Date, Index, DECIMAL
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class TestRun(Base):
    """Test run representing a single execution of tests."""
    __tablename__ = "test_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_number = Column(Integer)
    commit_sha = Column(String(40), nullable=False, index=True)
    branch = Column(String(255), nullable=False, index=True)
    triggered_by = Column(String(255))
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False)
    total_tests = Column(Integer, nullable=False, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration_seconds = Column(Integer)

    # Relationships
    results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")
    coverage_snapshots = relationship("CoverageSnapshot", back_populates="run", cascade="all, delete-orphan")
    mutation_results = relationship("MutationResult", back_populates="run", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="run", cascade="all, delete-orphan")
    quality_gate_results = relationship("QualityGateResult", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_test_runs_started_at", "started_at"),
    )


class TestResult(Base):
    """Result from a single test execution."""
    __tablename__ = "test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(String(500), nullable=False, index=True)
    test_file = Column(String(500))
    test_class = Column(String(255))
    test_function = Column(String(255))
    status = Column(String(50), nullable=False, index=True)
    duration_ms = Column(Integer)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    output = Column(Text)
    error_message = Column(Text)

    # Relationship
    run = relationship("TestRun", back_populates="results")


class CoverageSnapshot(Base):
    """Coverage snapshot for a service."""
    __tablename__ = "coverage_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(100), nullable=False)
    line_coverage = Column(DECIMAL(5, 2))
    branch_coverage = Column(DECIMAL(5, 2))
    lines_covered = Column(Integer)
    lines_total = Column(Integer)

    # Relationship
    run = relationship("TestRun", back_populates="coverage_snapshots")


class MutationResult(Base):
    """Mutation testing result for a service."""
    __tablename__ = "mutation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(100), nullable=False)
    total_mutations = Column(Integer)
    killed_mutations = Column(Integer)
    survived_mutations = Column(Integer)
    timeout_mutations = Column(Integer)
    mutation_score = Column(DECIMAL(5, 2))

    # Relationship
    run = relationship("TestRun", back_populates="mutation_results")


class PerformanceMetric(Base):
    """Performance metric for an endpoint."""
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    endpoint_name = Column(String(255), nullable=False)
    requests_per_second = Column(DECIMAL(10, 2))
    avg_response_time_ms = Column(Integer)
    p95_response_time_ms = Column(Integer)
    p99_response_time_ms = Column(Integer)
    error_rate = Column(DECIMAL(5, 2))

    # Relationship
    run = relationship("TestRun", back_populates="performance_metrics")


class DailySummary(Base):
    """Aggregated daily summary for a service."""
    __tablename__ = "daily_summaries"

    date = Column(Date, nullable=False, primary_key=True)
    service_name = Column(String(100), nullable=False, primary_key=True)
    total_runs = Column(Integer)
    avg_coverage = Column(DECIMAL(5, 2))
    avg_mutation_score = Column(DECIMAL(5, 2))
    avg_duration_seconds = Column(Integer)


class QualityGateResult(Base):
    """Quality gate evaluation result."""
    __tablename__ = "quality_gate_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    gate_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    threshold = Column(DECIMAL(5, 2))
    actual_value = Column(DECIMAL(5, 2))
    message = Column(Text)

    # Relationship
    run = relationship("TestRun", back_populates="quality_gate_results")
