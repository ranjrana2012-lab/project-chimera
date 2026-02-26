"""Tests for Operator Console skill"""

import pytest


@pytest.mark.unit
class TestOperatorConsoleSkill:
    """Test cases for Operator Console skill."""

    @pytest.mark.asyncio
    async def test_skill_metadata(self):
        """Test skill metadata is correctly defined."""
        from pathlib import Path
        import yaml

        skill_file = Path(__file__).parent.parent / "skill.yaml"
        data = yaml.safe_load(skill_file.read_text())

        assert data["metadata"]["name"] == "operator-console"
        assert "human-in-the-loop" in data["spec"]["tags"]
