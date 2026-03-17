"""Tests for Stage 4 Report Generation Integration"""
import pytest
from datetime import datetime
from reporting.orchestrator import ReportOrchestrator
from reporting.models import (
    SimulationTrace, SimulationRound, SimulationAction,
    ComprehensiveReport
)
from agents.profile import AgentProfile, MBTIType, Demographics, BehavioralProfile, PoliticalLeaning


def create_mock_simulation_trace() -> SimulationTrace:
    return SimulationTrace(
        simulation_id="test_sim_001",
        topic="Impact of remote work on employee productivity",
        rounds=[
            SimulationRound(
                round_number=1,
                actions=[
                    SimulationAction(
                        agent_id="agent_001",
                        action_type="post",
                        content="Remote work increases flexibility",
                        timestamp=datetime.now()
                    )
                ]
            )
        ],
        knowledge_graph_entities=["remote_work", "productivity"],
        started_at=datetime.now()
    )


async def create_mock_agents(count: int) -> list[AgentProfile]:
    agents = []
    for i in range(count):
        agents.append(AgentProfile(
            id=f"agent_{i}",
            mbti=MBTIType.INTJ,
            demographics=Demographics(
                age=30,
                gender="unspecified",
                education="bachelor",
                occupation="analyst",
                location="urban",
                income_level="middle"
            ),
            behavioral=BehavioralProfile(
                openness=0.7,
                conscientiousness=0.6,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.4
            ),
            political_leaning=PoliticalLeaning.CENTER,
            information_sources=["news"],
            memory_capacity=100
        ))
    return agents


@pytest.mark.asyncio
async def test_report_orchestration():
    orchestrator = ReportOrchestrator()
    trace = create_mock_simulation_trace()

    report = await orchestrator.generate_report(trace)

    assert isinstance(report, ComprehensiveReport)
    assert report.simulation_id == "test_sim_001"
    assert report.confidence_interval is not None
    assert len(report.confidence_interval) == 2
    assert report.debate_summary is not None
    assert len(report.debate_summary) > 0
    assert report.overall_confidence >= 0.0 and report.overall_confidence <= 1.0


@pytest.mark.asyncio
async def test_orchestration_with_debate():
    """Test that forum debate is conducted"""
    orchestrator = ReportOrchestrator()
    trace = create_mock_simulation_trace()

    report = await orchestrator.generate_report(trace)

    # Verify debate was conducted
    assert report.consensus_score >= 0.0 and report.consensus_score <= 1.0
    assert len(report.debate_arguments) > 0


@pytest.mark.asyncio
async def test_orchestration_with_react():
    """Test that ReACT report sections are generated"""
    orchestrator = ReportOrchestrator()
    trace = create_mock_simulation_trace()

    report = await orchestrator.generate_report(trace)

    # Verify ReACT sections
    assert report.executive_summary is not None
    assert len(report.findings) > 0
    assert len(report.recommendations) > 0


@pytest.mark.asyncio
async def test_orchestration_confidence_calculation():
    """Test that confidence intervals are calculated"""
    orchestrator = ReportOrchestrator()
    trace = create_mock_simulation_trace()

    report = await orchestrator.generate_report(trace)

    # Verify confidence metrics
    lower, upper = report.confidence_interval
    assert 0.0 <= lower <= upper <= 1.0
    assert report.overall_confidence >= 0.0 and report.overall_confidence <= 1.0


@pytest.mark.asyncio
async def test_orchestration_metadata():
    """Test that metadata is captured"""
    orchestrator = ReportOrchestrator()
    trace = create_mock_simulation_trace()

    report = await orchestrator.generate_report(trace)

    assert report.forum_rounds == 3
    assert report.react_iterations >= 0
