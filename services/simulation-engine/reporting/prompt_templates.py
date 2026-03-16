"""Prompt templates for ReACT ReportAgent report generation."""
from typing import Dict, Any


class PromptTemplates:
    """Prompt templates for report generation."""

    def get_prompt(self, section_type: str, context: Dict[str, Any]) -> str:
        """Get prompt for a specific section type."""

        templates = {
            "executive_summary": self._executive_summary_prompt(context),
            "key_findings": self._key_findings_prompt(context),
            "recommendations": self._recommendations_prompt(context)
        }

        return templates.get(section_type, self._default_prompt(context))

    def _executive_summary_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are generating an executive summary for a simulation report.

Simulation Topic: {context['topic']}
Simulation ID: {context['simulation_id']}
Total Rounds: {context['total_rounds']}
Total Actions: {context['total_actions']}

Recent Agent Actions:
{self._format_actions(context['recent_actions'])}

Knowledge Graph Entities: {', '.join(context['entities'][:5])}

Generate a concise 2-3 sentence executive summary that captures:
1. What was simulated
2. Key outcome or trend observed
3. Confidence level in the results

Format your response as a clear paragraph."""

    def _key_findings_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are extracting key findings from a simulation.

Simulation Topic: {context['topic']}
Recent Agent Actions:
{self._format_actions(context['recent_actions'])}

Knowledge Graph Entities: {', '.join(context['entities'][:10])}

Identify 3-5 key findings from this simulation. For each finding:
1. State the finding clearly
2. Provide supporting evidence from agent actions
3. Note any interesting patterns or anomalies

Format as a bulleted list."""

    def _recommendations_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are generating recommendations based on simulation results.

Simulation Topic: {context['topic']}
Key Findings: Assume findings have been analyzed

Based on this simulation, provide 3-5 actionable recommendations:
1. What actions should be taken?
2. What should be monitored?
3. What needs further investigation?

Format as a numbered list with clear action items."""

    def _default_prompt(self, context: Dict[str, Any]) -> str:
        return f"Generate a report section for simulation: {context['topic']}"

    def _format_actions(self, actions: list) -> str:
        """Format actions for display in prompts."""
        if not actions:
            return "No actions available."

        formatted = []
        for action in actions[:5]:
            formatted.append(
                f"- {action['agent']}: {action['action']} - \"{action['content']}\""
            )
        return "\n".join(formatted)
