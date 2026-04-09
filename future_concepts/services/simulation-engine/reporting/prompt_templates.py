"""Prompt templates for ReACT ReportAgent report generation."""
from typing import Dict, Any
import html


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
        # Use .get() with defaults to prevent KeyError
        topic = context.get('topic', 'Unknown Topic')
        simulation_id = context.get('simulation_id', 'Unknown')
        total_rounds = context.get('total_rounds', 0)
        total_actions = context.get('total_actions', 0)
        recent_actions = context.get('recent_actions', [])
        entities = context.get('entities', [])

        return f"""You are generating an executive summary for a simulation report.

Simulation Topic: {topic}
Simulation ID: {simulation_id}
Total Rounds: {total_rounds}
Total Actions: {total_actions}

Recent Agent Actions:
{self._format_actions(recent_actions)}

Knowledge Graph Entities: {', '.join(entities[:5])}

Generate a concise 2-3 sentence executive summary that captures:
1. What was simulated
2. Key outcome or trend observed
3. Confidence level in the results

Format your response as a clear paragraph."""

    def _key_findings_prompt(self, context: Dict[str, Any]) -> str:
        # Use .get() with defaults to prevent KeyError
        topic = context.get('topic', 'Unknown Topic')
        recent_actions = context.get('recent_actions', [])
        entities = context.get('entities', [])

        return f"""You are extracting key findings from a simulation.

Simulation Topic: {topic}
Recent Agent Actions:
{self._format_actions(recent_actions)}

Knowledge Graph Entities: {', '.join(entities[:10])}

Identify 3-5 key findings from this simulation. For each finding:
1. State the finding clearly
2. Provide supporting evidence from agent actions
3. Note any interesting patterns or anomalies

Format as a bulleted list."""

    def _recommendations_prompt(self, context: Dict[str, Any]) -> str:
        # Use .get() with defaults to prevent KeyError
        topic = context.get('topic', 'Unknown Topic')

        return f"""You are generating recommendations based on simulation results.

Simulation Topic: {topic}
Key Findings: Assume findings have been analyzed

Based on this simulation, provide 3-5 actionable recommendations:
1. What actions should be taken?
2. What should be monitored?
3. What needs further investigation?

Format as a numbered list with clear action items."""

    def _default_prompt(self, context: Dict[str, Any]) -> str:
        # Use .get() with defaults to prevent KeyError
        topic = context.get('topic', 'Unknown Topic')
        return f"Generate a report section for simulation: {topic}"

    def _format_actions(self, actions: list) -> str:
        """Format actions for display in prompts."""
        if not actions:
            return "No actions available."

        formatted = []
        for action in actions[:5]:
            # Sanitize content to prevent XSS
            safe_content = html.escape(str(action.get('content', '')))
            agent = action.get('agent', 'Unknown')
            action_type = action.get('action', 'unknown')
            formatted.append(
                f"- {agent}: {action_type} - \"{safe_content}\""
            )
        return "\n".join(formatted)
