"""Unit tests for reporting models."""
import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting.models import (
    ReportSection,
    Report,
    SimulationTrace,
    SimulationRound,
    SimulationAction
)


class TestReportSection:
    """Test ReportSection model with confidence validation."""

    def test_confidence_within_bounds(self):
        """Test that confidence is clamped to [0.0, 1.0]."""
        # Test normal values
        section = ReportSection(
            title="Test",
            content="Test content",
            confidence=0.5
        )
        assert section.confidence == 0.5

    def test_confidence_clamped_above(self):
        """Test that confidence > 1.0 is clamped to 1.0."""
        section = ReportSection(
            title="Test",
            content="Test content",
            confidence=1.5
        )
        assert section.confidence == 1.0

    def test_confidence_clamped_below(self):
        """Test that confidence < 0.0 is clamped to 0.0."""
        section = ReportSection(
            title="Test",
            content="Test content",
            confidence=-0.5
        )
        assert section.confidence == 0.0

    def test_confidence_boundary_values(self):
        """Test boundary values for confidence."""
        section1 = ReportSection(
            title="Test",
            content="Test content",
            confidence=0.0
        )
        assert section1.confidence == 0.0

        section2 = ReportSection(
            title="Test",
            content="Test content",
            confidence=1.0
        )
        assert section2.confidence == 1.0

    def test_confidence_extreme_values(self):
        """Test extreme values are properly clamped."""
        section1 = ReportSection(
            title="Test",
            content="Test content",
            confidence=100.0
        )
        assert section1.confidence == 1.0

        section2 = ReportSection(
            title="Test",
            content="Test content",
            confidence=-100.0
        )
        assert section2.confidence == 0.0


class TestSimulationTrace:
    """Test SimulationTrace model."""

    def test_create_minimal_trace(self):
        """Test creating a minimal simulation trace."""
        action = SimulationAction(
            agent_id="agent1",
            action_type="post",
            content="Test post",
            timestamp=datetime.now()
        )

        round = SimulationRound(
            round_number=1,
            actions=[action]
        )

        trace = SimulationTrace(
            simulation_id="sim1",
            topic="Test topic",
            rounds=[round],
            started_at=datetime.now()
        )

        assert trace.simulation_id == "sim1"
        assert trace.topic == "Test topic"
        assert len(trace.rounds) == 1
        assert len(trace.knowledge_graph_entities) == 0


class TestReport:
    """Test Report model."""

    def test_create_report(self):
        """Test creating a complete report."""
        executive_summary = ReportSection(
            title="Executive Summary",
            content="Test summary",
            confidence=0.8
        )

        finding = ReportSection(
            title="Finding 1",
            content="Test finding",
            confidence=0.9
        )

        recommendation = ReportSection(
            title="Recommendation 1",
            content="Test recommendation",
            confidence=0.7
        )

        report = Report(
            simulation_id="sim1",
            generated_at=datetime.now(),
            executive_summary=executive_summary,
            findings=[finding],
            recommendations=[recommendation]
        )

        assert report.simulation_id == "sim1"
        assert len(report.findings) == 1
        assert len(report.recommendations) == 1
        assert report.executive_summary.confidence == 0.8
