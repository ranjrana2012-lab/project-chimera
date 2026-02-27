"""Prompt template management."""

from pathlib import Path
from typing import Dict, Any


class PromptManager:
    """Manages prompt templates."""

    def __init__(self, templates_path: str = "/app/configs/prompts"):
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load prompt templates from files."""
        if not self.templates_path.exists():
            self._load_defaults()
            return

        # Check if there are any .md files
        md_files = list(self.templates_path.glob("**/*.md"))
        if not md_files:
            self._load_defaults()
            return

        for template_file in md_files:
            name = template_file.stem
            with open(template_file) as f:
                self.templates[name] = f.read()

    def _load_defaults(self) -> None:
        """Load default prompts."""
        self.templates["dialogue-generation"] = self._default_dialogue_prompt()

    def _default_dialogue_prompt(self) -> str:
        """Default dialogue generation prompt."""
        return """Generate dialogue for a theatre character.

Context: {context}
Character: {character}
Sentiment: {sentiment}

Generate appropriate dialogue:"""

    def get_template(self, name: str) -> str:
        """Get a template by name."""
        return self.templates.get(name, "")

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables."""
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable: {e}")
