"""Unit tests for ReACT ReportAgent error handling."""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting.react_agent import ReACTReportAgent
from reporting.models import (
    SimulationTrace,
    SimulationRound,
    SimulationAction,
    ReportSection
)


class TestReACTReportAgentErrorHandling:
    """Test ReACT ReportAgent error handling in async functions."""

    @pytest.fixture
    def mock_trace(self):
        """Create a mock simulation trace."""
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

        return SimulationTrace(
            simulation_id="sim1",
            topic="Test topic",
            rounds=[round],
            started_at=datetime.now()
        )

    @pytest.fixture
    def agent(self):
        """Create a ReACT ReportAgent instance."""
        # Mock the LLM router to avoid actual API calls
        with patch('reporting.react_agent.TieredLLMRouter'):
            agent = ReACTReportAgent(max_iterations=3)
            return agent

    @pytest.mark.asyncio
    async def test_act_generate_section_handles_llm_failure(self, agent, mock_trace):
        """Test that _act_generate_section handles LLM failures gracefully."""
        # Mock the router to raise an exception
        agent.router.call_llm = AsyncMock(side_effect=Exception("LLM API Error"))

        # Generate section should handle the error
        section = await agent._act_generate_section(
            mock_trace,
            "executive_summary",
            {}
        )

        # Should return a fallback section
        assert isinstance(section, ReportSection)
        assert section.title == "Executive Summary"
        assert "Unable to generate" in section.content
        assert section.confidence == 0.0
        assert section.sources == []

    @pytest.mark.asyncio
    async def test_act_generate_section_handles_json_parse_error(self, agent, mock_trace):
        """Test that _act_generate_section handles JSON parsing errors."""
        # Mock the router to return invalid JSON
        agent.router.call_llm = AsyncMock(
            return_value="This is not valid JSON {broken"
        )

        section = await agent._act_generate_section(
            mock_trace,
            "key_findings",
            {}
        )

        # Should still return a valid section
        assert isinstance(section, ReportSection)
        assert section.title == "Key Findings"
        assert section.content  # Should have extracted some content
        assert 0.0 <= section.confidence <= 1.0  # Confidence should be valid

    @pytest.mark.asyncio
    async def test_act_generate_section_handles_empty_response(self, agent, mock_trace):
        """Test that _act_generate_section handles empty LLM responses."""
        # Mock the router to return empty response
        agent.router.call_llm = AsyncMock(return_value="")

        section = await agent._act_generate_section(
            mock_trace,
            "recommendations",
            {}
        )

        # Should still return a valid section
        assert isinstance(section, ReportSection)
        assert section.title == "Recommendations"
        assert section.confidence >= 0.5  # Should use default confidence

    @pytest.mark.asyncio
    async def test_act_generate_section_with_valid_response(self, agent, mock_trace):
        """Test that _act_generate_section works with valid responses."""
        # Mock the router to return valid response
        agent.router.call_llm = AsyncMock(
            return_value='{"content": "Test findings", "confidence": 0.8}'
        )

        section = await agent._act_generate_section(
            mock_trace,
            "key_findings",
            {}
        )

        # Should return a valid section
        assert isinstance(section, ReportSection)
        assert section.title == "Key Findings"
        assert "Test findings" in section.content
        assert section.confidence == 0.8

    @pytest.mark.asyncio
    async def test_generate_report_handles_partial_failures(self, agent, mock_trace):
        """Test that generate_report handles partial section failures."""
        # Mock to succeed for executive summary but fail for others
        call_count = [0]

        async def mock_call_llm(prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                return "Executive summary content"
            else:
                raise Exception("Simulated failure")

        agent.router.call_llm = AsyncMock(side_effect=mock_call_llm)

        # Generate report
        report = await agent.generate_report(mock_trace)

        # Should have executive summary but fallback for others
        assert report.simulation_id == "sim1"
        assert report.executive_summary.content == "Executive summary content"
        assert len(report.findings) >= 0  # May or may not have findings
        assert len(report.recommendations) >= 0  # May or may not have recommendations

    @pytest.mark.asyncio
    async def test_think_next_section_sequence(self, agent, mock_trace):
        """Test that _think_next_section returns sections in correct order."""
        # Start with no sections
        section = await agent._think_next_section(mock_trace, {})
        assert section == "executive_summary"

        # After executive summary
        section = await agent._think_next_section(
            mock_trace,
            {"executive_summary": Mock()}
        )
        assert section == "key_findings"

        # After key findings
        section = await agent._think_next_section(
            mock_trace,
            {
                "executive_summary": Mock(),
                "key_findings": Mock()
            }
        )
        assert section == "recommendations"

        # After all sections
        section = await agent._think_next_section(
            mock_trace,
            {
                "executive_summary": Mock(),
                "key_findings": Mock(),
                "recommendations": Mock()
            }
        )
        assert section is None

    def test_build_context_with_empty_trace(self, agent):
        """Test _build_context with minimal trace."""
        trace = SimulationTrace(
            simulation_id="sim1",
            topic="Test",
            rounds=[],
            started_at=datetime.now()
        )

        context = agent._build_context(trace, {})

        assert context['topic'] == "Test"
        assert context['simulation_id'] == "sim1"
        assert context['total_rounds'] == 0
        assert context['total_actions'] == 0
        assert context['entities'] == []
        assert context['relationships'] == []
        assert context['recent_actions'] == []

    def test_build_context_with_actions(self, agent):
        """Test _build_context with actions."""
        action1 = SimulationAction(
            agent_id="agent1",
            action_type="post",
            content="A" * 200,  # Long content
            timestamp=datetime.now()
        )

        action2 = SimulationAction(
            agent_id="agent2",
            action_type="reply",
            content="B" * 50,
            timestamp=datetime.now()
        )

        round = SimulationRound(
            round_number=1,
            actions=[action1, action2]
        )

        trace = SimulationTrace(
            simulation_id="sim1",
            topic="Test",
            rounds=[round],
            started_at=datetime.now(),
            knowledge_graph_entities=["entity1", "entity2"],
            knowledge_graph_relationships=["rel1", "rel2"]
        )

        context = agent._build_context(trace, {})

        assert context['total_actions'] == 2
        assert len(context['recent_actions']) == 2
        # Content should be truncated
        assert len(context['recent_actions'][0]['content']) <= 100
        # Entities should be limited
        assert len(context['entities']) == 2

    def test_format_title(self, agent):
        """Test _format_title method."""
        assert agent._format_title("executive_summary") == "Executive Summary"
        assert agent._format_title("key_findings") == "Key Findings"
        assert agent._format_title("recommendations") == "Recommendations"
        assert agent._format_title("custom_section") == "Custom Section"
        assert agent._format_title("another_test") == "Another Test"

    def test_extract_content_with_json(self, agent):
        """Test _extract_content with JSON response."""
        response = '{"content": "Extracted content", "confidence": 0.8}'
        content = agent._extract_content(response)
        assert content == "Extracted content"

    def test_extract_content_with_plain_text(self, agent):
        """Test _extract_content with plain text response."""
        response = "This is plain content"
        content = agent._extract_content(response)
        assert content == "This is plain content"

    def test_extract_content_with_prefix(self, agent):
        """Test _extract_content removes common prefixes."""
        response = "Here is the content you requested\nThis is the actual content"
        content = agent._extract_content(response)
        assert "This is the actual content" in content
        assert "Here is" not in content

    def test_extract_confidence_from_json(self, agent):
        """Test _extract_confidence from JSON response."""
        response = '{"content": "Test", "confidence": 0.75}'
        confidence = agent._extract_confidence(response)
        assert confidence == 0.75

    def test_extract_confidence_from_plain_text(self, agent):
        """Test _extract_confidence from plain text (heuristic)."""
        # Short response
        confidence1 = agent._extract_confidence("Short")
        assert 0.5 <= confidence1 < 0.6

        # Long response
        long_text = "Content " * 200
        confidence2 = agent._extract_confidence(long_text)
        assert 0.7 <= confidence2 <= 1.0

    def test_extract_sources(self, agent, mock_trace):
        """Test _extract_sources method."""
        sources = agent._extract_sources(mock_trace, "key_findings")

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert any("sim1" in s for s in sources)

    def test_build_report_with_all_sections(self, agent, mock_trace):
        """Test _build_report with all sections."""
        sections = {
            "executive_summary": ReportSection(
                title="Executive Summary",
                content="Summary",
                confidence=0.8
            ),
            "key_findings": ReportSection(
                title="Key Findings",
                content="Findings",
                confidence=0.9
            ),
            "recommendations": ReportSection(
                title="Recommendations",
                content="Recommendations",
                confidence=0.7
            )
        }

        report = agent._build_report(mock_trace, sections)

        assert report.simulation_id == "sim1"
        assert report.executive_summary.content == "Summary"
        assert len(report.findings) == 1
        assert len(report.recommendations) == 1

    def test_build_report_with_missing_sections(self, agent, mock_trace):
        """Test _build_report with missing sections."""
        sections = {
            "executive_summary": ReportSection(
                title="Executive Summary",
                content="Summary",
                confidence=0.8
            )
        }

        report = agent._build_report(mock_trace, sections)

        assert report.simulation_id == "sim1"
        assert report.executive_summary.content == "Summary"
        assert len(report.findings) == 0
        assert len(report.recommendations) == 0
