"""Tests for SkillRegistry"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.core.skill_registry import SkillRegistry


@pytest.fixture
def temp_skills_dir():
    """Create a temporary skills directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_path = Path(tmpdir)

        # Create a sample skill
        sample_skill = {
            "apiVersion": "openclaw.io/v1",
            "kind": "Skill",
            "metadata": {
                "name": "test-skill",
                "version": "1.0.0",
            },
            "spec": {
                "description": "A test skill",
                "category": "test",
                "enabled": True,
                "timeout": 3000,
                "inputs": [],
                "outputs": [],
                "config": {
                    "caching": {
                        "enabled": True,
                        "ttl": 300,
                    },
                },
                "tags": ["test"],
            },
        }

        skill_dir = skills_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text(yaml.dump(sample_skill))

        yield skills_path


@pytest.mark.unit
class TestSkillRegistry:
    """Test cases for SkillRegistry."""

    @pytest.mark.asyncio
    async def test_load_skills(self, temp_skills_dir):
        """Test loading skills from directory."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        assert registry.is_loaded
        assert len(registry._skills) == 1
        assert "test-skill" in registry._skills

    @pytest.mark.asyncio
    async def test_list_skills(self, temp_skills_dir):
        """Test listing skills."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        skills = await registry.list_skills()

        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].enabled is True

    @pytest.mark.asyncio
    async def test_get_skill(self, temp_skills_dir):
        """Test getting a specific skill."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        skill = await registry.get_skill("test-skill")

        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"
        assert skill.category == "test"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, temp_skills_dir):
        """Test getting a non-existent skill."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        with pytest.raises(ValueError):
            await registry.get_skill("non-existent")

    @pytest.mark.asyncio
    async def test_enable_disable_skill(self, temp_skills_dir):
        """Test enabling and disabling skills."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        await registry.disable_skill("test-skill")
        skill = await registry.get_skill("test-skill")
        assert skill.enabled is False

        await registry.enable_skill("test-skill")
        skill = await registry.get_skill("test-skill")
        assert skill.enabled is True

    @pytest.mark.asyncio
    async def test_cache_operations(self, temp_skills_dir):
        """Test cache operations."""
        registry = SkillRegistry(temp_skills_dir)

        cache_key = registry.get_cache_key("test-skill", {"input": "data"})

        # Test cache miss
        result = await registry.get_cached_result(cache_key)
        assert result is None

        # Test cache set and hit
        await registry.cache_result(cache_key, {"output": "result"}, 300)
        result = await registry.get_cached_result(cache_key)
        assert result == {"output": "result"}

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, temp_skills_dir):
        """Test cache invalidation."""
        registry = SkillRegistry(temp_skills_dir)

        await registry.cache_result("key1", {"data": "1"}, 300)
        await registry.cache_result("test-skill:key2", {"data": "2"}, 300)

        # Invalidate specific skill
        await registry.invalidate_cache("test-skill")

        assert await registry.get_cached_result("key1") == {"data": "1"}
        assert await registry.get_cached_result("test-skill:key2") is None

    @pytest.mark.asyncio
    async def test_list_categories(self, temp_skills_dir):
        """Test listing skill categories."""
        registry = SkillRegistry(temp_skills_dir)
        await registry.load_skills()

        categories = await registry.list_categories()

        assert "test" in categories
