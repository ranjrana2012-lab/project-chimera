"""Tests for ReACT ReportAgent."""
import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting.react_agent import ReACTReportAgent
from reporting.models import (
    SimulationTrace, SimulationRound, SimulationAction,
    Report, ReportSection
)


def create_mock_simulation_trace() -> SimulationTrace:
    """Create a mock simulation trace for testing."""
    return SimulationTrace(
        simulation_id="test_sim_001",
        topic="Impact of carbon tax on consumer behavior",
        rounds=[
            SimulationRound(
                round_number=1,
                actions=[
                    SimulationAction(
                        agent_id="agent_001",
                        action_type="post",
                        content="Carbon tax will increase prices",
                        timestamp=datetime.now()
                    ),
                    SimulationAction(
                        agent_id="agent_002",
                        action_type="reply",
                        content="But it encourages green alternatives",
                        timestamp=datetime.now()
                    )
                ]
            )
        ],
        knowledge_graph_entities=["carbon_tax", "consumer_behavior", "green_energy"],
        knowledge_graph_relationships=["carbon_tax-affects->consumer_behavior"],
        started_at=datetime.now()
    )


@pytest.mark.asyncio
async def test_react_report_generation():
    """Test basic ReACT report generation."""
    agent = ReACTReportAgent()
    trace = create_mock_simulation_trace()
    report = await agent.generate_report(trace)

    assert report.simulation_id == "test_sim_001"
    assert isinstance(report.executive_summary, ReportSection)
    assert len(report.executive_summary.content) > 0
    assert len(report.findings) >= 1
    assert len(report.recommendations) >= 1


@pytest.mark.asyncio
async def test_react_thought_action_observation_loop():
    """Test that ReACT loop iterates correctly."""
    agent = ReACTReportAgent()
    trace = create_mock_simulation_trace()

    # Generate report
    report = await agent.generate_report(trace)

    # Verify all sections were generated
    assert report.executive_summary.title == "Executive Summary"
    assert len(report.findings) > 0
    assert len(report.recommendations) > 0


@pytest.mark.asyncio
async def test_react_with_empty_trace():
    """Test ReACT handles edge case of empty simulation."""
    agent = ReACTReportAgent()
    trace = SimulationTrace(
        simulation_id="empty_sim",
        topic="Empty topic",
        rounds=[],
        started_at=datetime.now()
    )

    report = await agent.generate_report(trace)
    assert report.simulation_id == "empty_sim"
    # Should still generate minimal report
    assert len(report.executive_summary.content) > 0


@pytest.mark.asyncio
async def test_react_confidence_scoring():
    """Test that confidence scores are generated."""
    agent = ReACTReportAgent()
    trace = create_mock_simulation_trace()
    report = await agent.generate_report(trace)

    # Executive summary should have confidence
    assert 0.0 <= report.executive_summary.confidence <= 1.0

    # Findings and recommendations should have confidence
    for finding in report.findings:
        assert 0.0 <= finding.confidence <= 1.0

    for recommendation in report.recommendations:
        assert 0.0 <= recommendation.confidence <= 1.0


@pytest.mark.asyncio
async def test_react_sources_tracking():
    """Test that sources are tracked."""
    agent = ReACTReportAgent()
    trace = create_mock_simulation_trace()
    report = await agent.generate_report(trace)

    # Executive summary should have sources
    assert len(report.executive_summary.sources) > 0

    # Should include simulation ID as source
    assert any("test_sim_001" in source for source in report.executive_summary.sources)


@pytest.mark.asyncio
async def test_react_with_multiple_rounds():
    """Test ReACT with simulation containing multiple rounds."""
    agent = ReACTReportAgent()
    trace = SimulationTrace(
        simulation_id="multi_round_sim",
        topic="Multi-round simulation",
        rounds=[
            SimulationRound(
                round_number=1,
                actions=[
                    SimulationAction(
                        agent_id="agent_001",
                        action_type="post",
                        content="Initial post",
                        timestamp=datetime.now()
                    )
                ]
            ),
            SimulationRound(
                round_number=2,
                actions=[
                    SimulationAction(
                        agent_id="agent_002",
                        action_type="reply",
                        content="Follow-up reply",
                        timestamp=datetime.now()
                    )
                ]
            )
        ],
        started_at=datetime.now()
    )

    report = await agent.generate_report(trace)
    assert report.simulation_id == "multi_round_sim"
    assert len(report.executive_summary.content) > 0
