"""Unit tests for SceneSpeak Prompt Manager."""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from services.scenespeak_agent.src.core.prompt_manager import PromptManager


@pytest.mark.unit
class TestPromptManager:
    """Test cases for PromptManager."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary directory for prompt templates."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def empty_templates_dir(self, temp_templates_dir):
        """Create an empty templates directory."""
        return temp_templates_dir

    @pytest.fixture
    def populated_templates_dir(self, temp_templates_dir):
        """Create a templates directory with sample prompts."""
        # Create subdirectory
        subdir = temp_templates_dir / "subdir"
        subdir.mkdir()

        # Create sample prompt files
        prompt1 = temp_templates_dir / "dialogue-generation.md"
        prompt1.write_text(
            "Generate dialogue for a theatre character.\n\n"
            "Context: {context}\n"
            "Character: {character}\n"
            "Sentiment: {sentiment}\n\n"
            "Generate appropriate dialogue:"
        )

        prompt2 = subdir / "stage-directions.md"
        prompt2.write_text(
            "Generate stage directions.\n\n"
            "Scene: {scene}\n"
            "Action: {action}\n\n"
            "Generate directions:"
        )

        return temp_templates_dir

    @pytest.fixture
    def manager_with_defaults(self):
        """Create a manager with default prompts (non-existing path)."""
        return PromptManager(templates_path="/nonexistent/path")

    @pytest.fixture
    def manager_with_populated(self, populated_templates_dir):
        """Create a manager with populated templates."""
        return PromptManager(templates_path=str(populated_templates_dir))

    def test_initialization_with_defaults(self, manager_with_defaults):
        """Test manager initialization with default prompts."""
        assert manager_with_defaults.templates_path == Path("/nonexistent/path")
        assert isinstance(manager_with_defaults.templates, dict)
        # Should load default prompts when directory doesn't exist
        assert "dialogue-generation" in manager_with_defaults.templates

    def test_initialization_with_populated(self, manager_with_populated):
        """Test manager initialization with populated templates."""
        assert isinstance(manager_with_populated.templates, dict)
        assert "dialogue-generation" in manager_with_populated.templates
        assert "stage-directions" in manager_with_populated.templates

    def test_load_templates_from_nonexistent_path(self):
        """Test loading templates from non-existent path loads defaults."""
        manager = PromptManager(templates_path="/totally/nonexistent/path")
        assert "dialogue-generation" in manager.templates
        # Check it contains the default prompt
        assert "Context:" in manager.templates["dialogue-generation"]
        assert "Character:" in manager.templates["dialogue-generation"]

    def test_load_templates_from_empty_dir(self, empty_templates_dir):
        """Test loading templates from empty directory loads defaults."""
        manager = PromptManager(templates_path=str(empty_templates_dir))
        assert "dialogue-generation" in manager.templates
        # Should have default prompt since no .md files found
        assert "Context:" in manager.templates["dialogue-generation"]

    def test_load_templates_from_populated_dir(self, populated_templates_dir):
        """Test loading templates from populated directory."""
        manager = PromptManager(templates_path=str(populated_templates_dir))
        assert "dialogue-generation" in manager.templates
        assert "stage-directions" in manager.templates

        # Check content of loaded templates
        assert "Generate dialogue for a theatre character" in manager.templates["dialogue-generation"]
        assert "{context}" in manager.templates["dialogue-generation"]
        assert "Generate stage directions" in manager.templates["stage-directions"]
        assert "{scene}" in manager.templates["stage-directions"]

    def test_load_templates_from_nested_structure(self, temp_templates_dir):
        """Test loading templates from nested directory structure."""
        # Create nested structure
        level1 = temp_templates_dir / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        prompt1 = level1 / "prompt1.md"
        prompt1.write_text("Level 1: {var1}")

        prompt2 = level2 / "prompt2.md"
        prompt2.write_text("Level 2: {var2}")

        manager = PromptManager(templates_path=str(temp_templates_dir))

        # Both templates should be loaded
        assert "prompt1" in manager.templates
        assert "prompt2" in manager.templates
        assert manager.templates["prompt1"] == "Level 1: {var1}"
        assert manager.templates["prompt2"] == "Level 2: {var2}"

    def test_get_template_existing(self, manager_with_populated):
        """Test getting an existing template."""
        template = manager_with_populated.get_template("dialogue-generation")
        assert "Generate dialogue for a theatre character" in template
        assert "{context}" in template

    def test_get_template_nonexistent(self, manager_with_populated):
        """Test getting a non-existent template."""
        template = manager_with_populated.get_template("nonexistent")
        assert template == ""

    def test_render_template_success(self, manager_with_populated):
        """Test successfully rendering a template with variables."""
        template = manager_with_populated.get_template("dialogue-generation")
        rendered = manager_with_populated.render(
            template,
            {
                "context": "A tense scene in a dimly lit room",
                "character": "PROTAGONIST",
                "sentiment": "nervous"
            }
        )

        assert "A tense scene in a dimly lit room" in rendered
        assert "PROTAGONIST" in rendered
        assert "nervous" in rendered
        assert "{context}" not in rendered  # Variables should be replaced

    def test_render_template_with_default(self, manager_with_defaults):
        """Test rendering the default template."""
        template = manager_with_defaults.get_template("dialogue-generation")
        rendered = manager_with_defaults.render(
            template,
            {
                "context": "Test context",
                "character": "TEST_CHAR",
                "sentiment": "neutral"
            }
        )

        assert "Test context" in rendered
        assert "TEST_CHAR" in rendered
        assert "neutral" in rendered

    def test_render_template_missing_variable(self, manager_with_populated):
        """Test rendering template with missing variable raises ValueError."""
        template = manager_with_populated.get_template("dialogue-generation")

        with pytest.raises(ValueError, match="Missing variable"):
            manager_with_populated.render(
                template,
                {
                    "context": "Test context",
                    # Missing 'character' and 'sentiment'
                }
            )

    def test_render_empty_template(self, manager_with_populated):
        """Test rendering an empty template."""
        rendered = manager_with_populated.render("", {"var": "value"})
        assert rendered == ""

    def test_render_template_with_extra_variables(self, manager_with_populated):
        """Test rendering template with extra variables (should work)."""
        template = manager_with_populated.get_template("dialogue-generation")
        # Extra variables should be ignored
        rendered = manager_with_populated.render(
            template,
            {
                "context": "Test",
                "character": "CHAR",
                "sentiment": "happy",
                "extra_var": "This should be ignored"
            }
        )

        assert "Test" in rendered
        assert "CHAR" in rendered
        assert "happy" in rendered

    def test_default_dialogue_prompt_structure(self, manager_with_defaults):
        """Test the structure of the default dialogue prompt."""
        default_prompt = manager_with_defaults._default_dialogue_prompt()

        assert "Context:" in default_prompt
        assert "Character:" in default_prompt
        assert "Sentiment:" in default_prompt
        assert "{context}" in default_prompt
        assert "{character}" in default_prompt
        assert "{sentiment}" in default_prompt
        assert "Generate appropriate dialogue:" in default_prompt

    def test_template_files_only_md(self, temp_templates_dir):
        """Test that only .md files are loaded as templates."""
        # Create various files
        (temp_templates_dir / "template1.md").write_text("MD Template: {var}")
        (temp_templates_dir / "template2.txt").write_text("TXT Template: {var}")
        (temp_templates_dir / "template3.yaml").write_text("key: value")
        (temp_templates_dir / "README.md").write_text("Readme content")

        manager = PromptManager(templates_path=str(temp_templates_dir))

        # Only .md files should be loaded
        assert "template1" in manager.templates
        assert "README" in manager.templates
        assert "template2" not in manager.templates
        assert "template3" not in manager.templates

    def test_template_name_from_filename(self, temp_templates_dir):
        """Test that template names are derived from filenames without extension."""
        (temp_templates_dir / "my-custom-template.md").write_text("Content")
        (temp_templates_dir / "another_one.md").write_text("Content")

        manager = PromptManager(templates_path=str(temp_templates_dir))

        assert "my-custom-template" in manager.templates
        assert "another_one" in manager.templates
