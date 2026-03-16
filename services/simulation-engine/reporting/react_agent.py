"""ReACT (Reasoning and Acting) Report Agent for comprehensive report generation."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from .models import (
    Report, ReportSection, SimulationTrace,
    SimulationAction, SimulationRound
)
from simulation.llm_router import TieredLLMRouter
from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class ReACTReportAgent:
    """
    ReACT (Reasoning and Acting) Report Agent

    Follows thought-action-observation loop:
    - Thought: What analysis is needed?
    - Action: Query simulation data / Call LLM
    - Observation: What did we find?
    - Iterate until complete report generated
    """

    def __init__(self, max_iterations: int = 10):
        self.router = TieredLLMRouter()
        self.templates = PromptTemplates()
        self.max_iterations = max_iterations

    async def generate_report(
        self,
        trace: SimulationTrace
    ) -> Report:
        """Generate comprehensive report using ReACT pattern."""
        logger.info(f"Starting ReACT report generation for simulation {trace.simulation_id}")

        # Initialize report structure
        report_sections: Dict[str, ReportSection] = {}

        # ReACT Loop
        for iteration in range(self.max_iterations):
            logger.debug(f"ReACT iteration {iteration + 1}/{self.max_iterations}")

            # THOUGHT: What section should we work on next?
            thought = await self._think_next_section(trace, report_sections)

            if thought is None:  # Report complete
                logger.info("ReACT loop: Report complete")
                break

            # ACTION: Generate the section content
            action_result = await self._act_generate_section(
                trace, thought, report_sections
            )

            # OBSERVATION: Store the result
            report_sections[thought] = action_result
            logger.debug(f"Generated section: {thought}")

        # Build final report
        return self._build_report(trace, report_sections)

    async def _think_next_section(
        self,
        trace: SimulationTrace,
        completed_sections: Dict[str, ReportSection]
    ) -> Optional[str]:
        """Determine which section to work on next."""

        # Define required sections in order
        required_sections = [
            "executive_summary",
            "key_findings",
            "recommendations"
        ]

        # Find first incomplete section
        for section in required_sections:
            if section not in completed_sections:
                return section

        # All sections complete
        return None

    async def _act_generate_section(
        self,
        trace: SimulationTrace,
        section_type: str,
        completed_sections: Dict[str, ReportSection]
    ) -> ReportSection:
        """Generate content for a specific section."""

        # Build context from simulation trace
        context = self._build_context(trace, completed_sections)

        # Get prompt template for this section
        prompt = self.templates.get_prompt(section_type, context)

        # Call LLM to generate content
        response = await self.router.call_llm(prompt)

        # Parse response
        title = self._format_title(section_type)
        content = self._extract_content(response)
        confidence = self._extract_confidence(response)
        sources = self._extract_sources(trace, section_type)

        return ReportSection(
            title=title,
            content=content,
            confidence=confidence,
            sources=sources
        )

    def _build_context(
        self,
        trace: SimulationTrace,
        completed_sections: Dict[str, ReportSection]
    ) -> Dict[str, Any]:
        """Build context for LLM prompt."""

        # Summarize simulation
        total_actions = sum(len(round.actions) for round in trace.rounds)

        context = {
            "topic": trace.topic,
            "simulation_id": trace.simulation_id,
            "total_rounds": len(trace.rounds),
            "total_actions": total_actions,
            "entities": trace.knowledge_graph_entities[:10],  # Limit context
            "relationships": trace.knowledge_graph_relationships[:5],
        }

        # Add recent actions as examples
        recent_actions = []
        for round in trace.rounds[-3:]:  # Last 3 rounds
            for action in round.actions[:3]:  # Up to 3 actions per round
                recent_actions.append({
                    "agent": action.agent_id,
                    "action": action.action_type,
                    "content": action.content[:100]  # Truncate
                })
        context["recent_actions"] = recent_actions

        return context

    def _format_title(self, section_type: str) -> str:
        """Format section title from section type."""
        titles = {
            "executive_summary": "Executive Summary",
            "key_findings": "Key Findings",
            "recommendations": "Recommendations"
        }
        return titles.get(section_type, section_type.replace("_", " ").title())

    def _extract_content(self, response: str) -> str:
        """Extract main content from LLM response."""
        # Try to parse as JSON first
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                return data.get("content", response)
        except json.JSONDecodeError:
            pass

        # Remove markdown formatting if present
        content = response.strip()

        # Remove common prefixes
        if content.lower().startswith("here is"):
            content = content.split("\n", 1)[-1]
        elif content.lower().startswith("the executive summary"):
            content = content.split(":", 1)[-1] if ":" in content else content

        return content.strip()

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence score from LLM response."""
        # Try to parse as JSON first
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "confidence" in data:
                return float(data["confidence"])
        except json.JSONDecodeError:
            pass

        # Simple heuristic: longer responses = higher confidence
        # In production, could use structured output with explicit confidence
        base_confidence = 0.5
        length_bonus = min(len(response) / 1000, 0.3)
        return min(base_confidence + length_bonus, 1.0)

    def _extract_sources(
        self,
        trace: SimulationTrace,
        section_type: str
    ) -> List[str]:
        """Extract sources for this section."""
        sources = []

        # Add entities as sources
        if trace.knowledge_graph_entities:
            sources.extend(trace.knowledge_graph_entities[:3])

        # Add simulation ID as source reference
        sources.append(f"Simulation {trace.simulation_id}")

        return sources

    def _build_report(
        self,
        trace: SimulationTrace,
        sections: Dict[str, ReportSection]
    ) -> Report:
        """Build final report from generated sections."""

        # Get sections (with defaults for missing)
        executive_summary = sections.get("executive_summary", ReportSection(
            title="Executive Summary",
            content="Unable to generate executive summary.",
            confidence=0.0
        ))

        findings = [sections["key_findings"]] if "key_findings" in sections else []
        recommendations = [sections["recommendations"]] if "recommendations" in sections else []

        return Report(
            simulation_id=trace.simulation_id,
            generated_at=datetime.now(),
            executive_summary=executive_summary,
            findings=findings,
            recommendations=recommendations,
            confidence_interval=(0.0, 1.0),  # Will be refined by orchestrator
            metadata={"iterations": len(sections)}
        )
