# tests/unit/test_openclaw_skill_registry.py

import pytest
from services.openclaw_orchestrator.src.core.skill_registry import SkillRegistry

class TestSkillRegistry:
    @pytest.fixture
    def registry(self, tmp_path):
        return SkillRegistry(config_path=str(tmp_path))

    def test_list_empty_skills(self, registry):
        assert registry.list_skills() == []

    def test_get_nonexistent_skill(self, registry):
        assert registry.get_skill("nonexistent") is None
