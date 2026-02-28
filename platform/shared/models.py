"""SQLAlchemy ORM models for Chimera Quality Platform."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, ForeignKey, Date, Index, DECIMAL, Boolean, CheckConstraint
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
        CheckConstraint("status IN ('running', 'passed', 'failed', 'cancelled', 'timeout')", name="check_test_runs_status"),
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

    __table_args__ = (
        CheckConstraint("status IN ('passed', 'failed', 'skipped', 'error', 'timeout')", name="check_test_results_status"),
    )


class CoverageSnapshot(Base):
    """Coverage snapshot for a service."""
    __tablename__ = "coverage_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(100), nullable=False)
    line_coverage = Column(DECIMAL(5, 2), nullable=False)
    branch_coverage = Column(DECIMAL(5, 2), nullable=False)
    lines_covered = Column(Integer, nullable=False)
    lines_total = Column(Integer, nullable=False)

    # Relationship
    run = relationship("TestRun", back_populates="coverage_snapshots")

    __table_args__ = (
        CheckConstraint("line_coverage >= 0 AND line_coverage <= 100", name="check_coverage_line_coverage"),
        CheckConstraint("branch_coverage >= 0 AND branch_coverage <= 100", name="check_coverage_branch_coverage"),
        CheckConstraint("lines_covered >= 0", name="check_coverage_lines_covered"),
        CheckConstraint("lines_total >= 0 AND lines_total >= lines_covered", name="check_coverage_lines_total"),
    )


class MutationResult(Base):
    """Mutation testing result for a service."""
    __tablename__ = "mutation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(100), nullable=False)
    total_mutations = Column(Integer, nullable=False)
    killed_mutations = Column(Integer)
    survived_mutations = Column(Integer)
    timeout_mutations = Column(Integer)
    mutation_score = Column(DECIMAL(5, 2))

    # Relationship
    run = relationship("TestRun", back_populates="mutation_results")

    __table_args__ = (
        CheckConstraint("total_mutations >= 0", name="check_mutation_total_mutations"),
        CheckConstraint("mutation_score IS NULL OR (mutation_score >= 0 AND mutation_score <= 100)", name="check_mutation_score"),
    )


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
    total_runs = Column(Integer, nullable=False, default=0)
    avg_coverage = Column(DECIMAL(5, 2))
    avg_mutation_score = Column(DECIMAL(5, 2))
    avg_duration_seconds = Column(Integer)


class QualityGateResult(Base):
    """Quality gate evaluation result."""
    __tablename__ = "quality_gate_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    gate_name = Column(String(100), nullable=False)
    passed = Column(Boolean, nullable=False)
    score = Column(DECIMAL(5, 2))
    message = Column(Text)

    # Relationship
    run = relationship("TestRun", back_populates="quality_gate_results")
