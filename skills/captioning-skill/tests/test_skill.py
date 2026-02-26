"""Tests for Captioning skill"""

import pytest


@pytest.mark.unit
class TestCaptioningSkill:
    """Test cases for Captioning skill."""

    @pytest.mark.asyncio
    async def test_skill_metadata(self):
        """Test skill metadata is correctly defined."""
        from pathlib import Path
        import yaml

        skill_file = Path(__file__).parent.parent / "skill.yaml"
        data = yaml.safe_load(skill_file.read_text())

        assert data["metadata"]["name"] == "captioning"
        assert len(data["spec"]["inputs"]) == 2
        assert len(data["spec"]["outputs"]) == 4
