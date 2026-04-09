"""Integration test for complete report generation pipeline."""
import pytest
from datetime import datetime
from reporting.orchestrator import ReportOrchestrator
from reporting.models import SimulationTrace, SimulationRound, SimulationAction


@pytest.mark.asyncio
async def test_end_to_end_report_generation():
    """Test complete report generation from simulation trace to final report."""
    # Create a realistic simulation trace
    trace = SimulationTrace(
        simulation_id="integration_test_001",
        topic="Impact of AI on job market dynamics",
        rounds=[
            SimulationRound(
                round_number=1,
                actions=[
                    SimulationAction(
                        agent_id="agent_001",
                        action_type="post",
                        content="AI will create new types of jobs we can't imagine yet",
                        timestamp=datetime.now()
                    ),
                    SimulationAction(
                        agent_id="agent_002",
                        action_type="reply",
                        content="But it will also displace many traditional roles",
                        timestamp=datetime.now()
                    )
                ]
            ),
            SimulationRound(
                round_number=2,
                actions=[
                    SimulationAction(
                        agent_id="agent_003",
                        action_type="post",
                        content="The key is reskilling and adaptation",
                        timestamp=datetime.now()
                    )
                ]
            )
        ],
        knowledge_graph_entities=["AI", "jobs", "automation", "reskilling"],
        knowledge_graph_relationships=["AI-impacts->jobs", "automation-replaces->manual_labor"],
        started_at=datetime.now()
    )

    # Generate comprehensive report
    orchestrator = ReportOrchestrator()
    report = await orchestrator.generate_report(trace)

    # Verify all components are present
    assert report.simulation_id == "integration_test_001"
    assert report.topic == "Impact of AI on job market dynamics"

    # Verify ReACT components
    assert report.executive_summary is not None
    assert len(report.executive_summary.title) > 0
    assert len(report.executive_summary.content) > 0

    # Verify ForumEngine components
    assert report.debate_summary is not None
    assert len(report.debate_summary) > 0
    assert report.consensus_score >= 0.0 and report.consensus_score <= 1.0
    assert len(report.debate_arguments) > 0

    # Verify combined metrics
    lower, upper = report.confidence_interval
    assert 0.0 <= lower <= upper <= 1.0
    assert report.overall_confidence >= 0.0 and report.overall_confidence <= 1.0

    # Verify metadata
    assert report.forum_rounds == 3
    assert report.react_iterations >= 0
    assert report.metadata["debate_participants"] > 0
    assert report.metadata["react_sections"] > 0

    print(f"\n✓ Comprehensive report generated successfully")
    print(f"  - Simulation ID: {report.simulation_id}")
    print(f"  - Debate arguments: {len(report.debate_arguments)}")
    print(f"  - Consensus score: {report.consensus_score:.2f}")
    print(f"  - Overall confidence: {report.overall_confidence:.2f}")
    print(f"  - Confidence interval: ({lower:.2f}, {upper:.2f})")


@pytest.mark.asyncio
async def test_report_orchestrator_with_empty_trace():
    """Test that orchestrator handles empty simulation traces gracefully."""
    trace = SimulationTrace(
        simulation_id="empty_test_001",
        topic="Test topic with no data",
        rounds=[],
        knowledge_graph_entities=[],
        knowledge_graph_relationships=[],
        started_at=datetime.now()
    )

    orchestrator = ReportOrchestrator()
    report = await orchestrator.generate_report(trace)

    # Should still generate a report even with empty trace
    assert report.simulation_id == "empty_test_001"
    assert report.debate_summary is not None
    assert report.overall_confidence >= 0.0
