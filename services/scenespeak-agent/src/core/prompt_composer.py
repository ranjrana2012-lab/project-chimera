"""
Prompt Composer for SceneSpeak Agent
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class PromptComposer:
    """Composes prompts for LLM inference."""

    def __init__(self, prompts_path: Path, default_version: str = "v1.0.0"):
        self.prompts_path = prompts_path
        self.default_version = default_version
        self._prompts: Dict[str, Any] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load prompt templates from disk."""
        prompt_dir = self.prompts_path / "scenespeak" / "dialogue-generation"

        if not prompt_dir.exists():
            # Use default prompt
            self._prompts["default"] = self._get_default_prompt()
            return

        # Load latest version
        current_file = prompt_dir / "current.md"
        if current_file.exists() or current_file.is_symlink():
            prompt_text = current_file.read_text()
            self._prompts["default"] = self._parse_prompt(prompt_text)
            return

        # Fall back to versioned prompt
        version_file = prompt_dir / f"{self.default_version}.md"
        if version_file.exists():
            prompt_text = version_file.read_text()
            self._prompts["default"] = self._parse_prompt(prompt_text)

    def _parse_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """Parse prompt template with YAML front matter."""
        lines = prompt_text.split("\n")

        # Check for YAML front matter
        if lines[0] == "---":
            yaml_end = lines.index("---", 1) if "---" in lines[1:] else 1
            front_matter = "\n".join(lines[1:yaml_end])
            metadata = yaml.safe_load(front_matter) if front_matter else {}
            template = "\n".join(lines[yaml_end + 1:])
        else:
            metadata = {}
            template = prompt_text

        return {
            "template": template,
            "metadata": metadata,
        }

    def _get_default_prompt(self) -> Dict[str, Any]:
        """Get default prompt template."""
        return {
            "template": """You are a character in a live theatrical performance. Generate dialogue that feels natural, engaging, and appropriate for the scene.

## Current Scene
{scene_title}
Setting: {scene_setting}
Mood: {scene_mood}

## Characters on Stage
{characters_list}

## Recent Dialogue
{dialogue_history}

## Audience Sentiment
Overall: {sentiment_overall}
Intensity: {sentiment_intensity}

## Instructions
Generate 2-3 lines of dialogue for the next character to speak. Be concise but expressive. Include stage directions in [brackets] where appropriate.

## Response
""",
            "metadata": {
                "version": "default",
                "max_tokens": 512,
                "temperature": 0.8,
            },
        }

    async def compose(
        self,
        context: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Compose prompt from context.

        Args:
            context: Full context dictionary
            version: Prompt version to use (optional)

        Returns:
            Composed prompt string
        """
        prompt_data = self._prompts.get(version or "default", self._prompts["default"])
        template = prompt_data["template"]

        # Format template with context
        prompt = template.format(
            scene_title=context["scene"]["title"],
            scene_setting=context["scene"]["setting"],
            scene_mood=context["scene"]["mood"],
            characters_list=", ".join(context["scene"]["characters"]),
            dialogue_history=self._format_dialogue(context["dialogue"]),
            sentiment_overall=context["sentiment"]["overall"],
            sentiment_intensity=context["sentiment"]["intensity"],
        )

        return prompt

    def _format_dialogue(self, dialogue: list) -> str:
        """Format dialogue history for prompt."""
        if not dialogue:
            return "(No previous dialogue)"

        lines = []
        for turn in dialogue[-5:]:  # Last 5 turns
            lines.append(f"{turn['character']}: {turn['text']}")

        return "\n".join(lines)
