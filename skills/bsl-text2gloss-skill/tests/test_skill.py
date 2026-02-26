"""Tests for BSL Text2Gloss skill"""

import pytest


@pytest.mark.unit
class TestBSLText2GlossSkill:
    """Test cases for BSL Text2Gloss skill."""

    @pytest.mark.asyncio
    async def test_skill_metadata(self):
        """Test skill metadata is correctly defined."""
        from pathlib import Path
        import yaml

        skill_file = Path(__file__).parent.parent / "skill.yaml"
        data = yaml.safe_load(skill_file.read_text())

        assert data["metadata"]["name"] == "bsl-text2gloss"
        assert data["spec"]["outputs"][0]["name"] == "gloss"
