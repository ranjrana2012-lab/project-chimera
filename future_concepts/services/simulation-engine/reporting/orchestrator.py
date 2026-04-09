"""ReportOrchestrator: Combines ForumEngine and ReACT for comprehensive reports."""
from typing import List, Dict, Any
from datetime import datetime
import logging

from .models import (
    ComprehensiveReport, ReportSection, SimulationTrace,
    Argument, Report
)
from .forum_engine import ForumEngine
from .react_agent import ReACTReportAgent

logger = logging.getLogger(__name__)


class ReportOrchestrator:
    """
    Orchestrates Stage 4: Report Generation

    Combines ForumEngine multi-agent debate with ReACT ReportAgent
    to produce comprehensive simulation reports.
    """

    def __init__(self, forum_rounds: int = 3):
        self.forum = ForumEngine()
        self.react_agent = ReACTReportAgent()
        self.forum_rounds = forum_rounds

    async def generate_report(
        self,
        trace: SimulationTrace
    ) -> ComprehensiveReport:
        """Generate comprehensive report using ForumEngine + ReACT"""

        logger.info(f"Starting report generation for simulation {trace.simulation_id}")

        # Step 1: ForumEngine multi-agent debate
        logger.info("Running ForumEngine debate")
        debate_result = await self._run_debate(trace)

        # Step 2: ReACT ReportAgent synthesis
        logger.info("Running ReACT report generation")
        react_report = await self.react_agent.generate_report(trace)

        # Step 3: Combine with confidence intervals
        logger.info("Combining results into comprehensive report")
        comprehensive = self._build_comprehensive_report(
            trace=trace,
            debate_result=debate_result,
            react_report=react_report
        )

        logger.info(f"Report generation complete for {trace.simulation_id}")
        return comprehensive

    async def _run_debate(self, trace: SimulationTrace):
        """Run ForumEngine debate on simulation topic"""

        # Create mock agents for debate (in production, use real agents)
        from agents.profile import AgentProfile, MBTIType, Demographics, BehavioralProfile, PoliticalLeaning

        # Create diverse panel of agents
        agents = []
        mbti_types = [MBTIType.INTJ, MBTIType.ENFP, MBTIType.ISTJ]

        for i, mbti in enumerate(mbti_types):
            agent = AgentProfile(
                id=f"debate_agent_{i}",
                mbti=mbti,
                demographics=Demographics(
                    age=30 + i * 5,
                    gender="unspecified",
                    education="bachelor",
                    occupation="analyst",
                    location="urban",
                    income_level="middle"
                ),
                behavioral=BehavioralProfile(
                    openness=0.6 + i * 0.1,
                    conscientiousness=0.6,
                    extraversion=0.5,
                    agreeableness=0.5,
                    neuroticism=0.4
                ),
                political_leaning=PoliticalLeaning.CENTER,
                information_sources=["news", "research"],
                memory_capacity=100
            )
            agents.append(agent)

        # Run debate
        debate_result = await self.forum.debate_topic(
            topic=trace.topic,
            participants=agents,
            rounds=self.forum_rounds
        )

        return debate_result

    def _build_comprehensive_report(
        self,
        trace: SimulationTrace,
        debate_result,
        react_report: Report
    ) -> ComprehensiveReport:
        """Build comprehensive report from debate and ReACT results"""

        # Calculate overall confidence (combine forum consensus + ReACT confidence)
        overall_confidence = self._calculate_overall_confidence(
            debate_result.consensus_score,
            react_report.executive_summary.confidence
        )

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            overall_confidence,
            len(debate_result.arguments)
        )

        return ComprehensiveReport(
            simulation_id=trace.simulation_id,
            generated_at=datetime.now(),
            topic=trace.topic,

            # ReACT content
            executive_summary=react_report.executive_summary,
            findings=react_report.findings,
            recommendations=react_report.recommendations,

            # ForumEngine content
            debate_summary=debate_result.summary,
            consensus_score=debate_result.consensus_score,
            debate_arguments=debate_result.arguments,

            # Combined metrics
            confidence_interval=confidence_interval,
            overall_confidence=overall_confidence,

            # Metadata
            forum_rounds=self.forum_rounds,
            react_iterations=react_report.metadata.get("iterations", 0),
            metadata={
                "debate_participants": len(debate_result.arguments),
                "react_sections": len(react_report.findings) + len(react_report.recommendations)
            }
        )

    def _calculate_overall_confidence(
        self,
        consensus_score: float,
        react_confidence: float
    ) -> float:
        """Calculate overall confidence from forum consensus and ReACT confidence"""
        # Weighted average: give more weight to forum consensus
        # Forum consensus represents multi-agent agreement
        # ReACT confidence represents LLM certainty
        forum_weight = 0.6
        react_weight = 0.4

        overall = (consensus_score * forum_weight) + (react_confidence * react_weight)
        return max(0.0, min(1.0, overall))

    def _calculate_confidence_interval(
        self,
        confidence: float,
        sample_size: int
    ) -> tuple[float, float]:
        """Calculate confidence interval using Wilson score approximation"""
        import math

        if sample_size < 2:
            return (0.0, 1.0)

        # Margin of error decreases with sample size
        margin = 1.96 / math.sqrt(sample_size) * (1 - confidence)
        lower = max(0.0, confidence - margin)
        upper = min(1.0, confidence + margin)

        return (lower, upper)
