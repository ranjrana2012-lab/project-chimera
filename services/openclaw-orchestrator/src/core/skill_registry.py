"""Skill Registry for OpenClaw Orchestrator"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import httpx
import yaml

from ..config import Settings
from ..models.responses import SkillMetadata


class SkillRegistry:
    """Registry for managing OpenClaw skills."""

    def __init__(self, skills_path: Path):
        self.skills_path = skills_path
        self._skills: Dict[str, SkillMetadata] = {}
        self._load_time: Optional[datetime] = None
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.is_loaded = False

    async def load_skills(self) -> None:
        """Load all skills from the skills directory."""
        skill_dirs = [d for d in self.skills_path.iterdir() if d.is_dir()]

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "skill.yaml"
            if skill_file.exists():
                try:
                    skill_data = yaml.safe_load(skill_file.read_text())
                    metadata = self._parse_skill_metadata(skill_data, skill_dir)
                    self._skills[metadata.name] = metadata
                except Exception as e:
                    print(f"Failed to load skill from {skill_dir}: {e}")

        self.is_loaded = True
        self._load_time = datetime.now()
        print(f"Loaded {len(self._skills)} skills from {self.skills_path}")

    def _parse_skill_metadata(
        self, skill_data: Dict, skill_dir: Path
    ) -> SkillMetadata:
        """Parse skill metadata from skill.yaml."""
        meta = skill_data["metadata"]
        spec = skill_data["spec"]

        return SkillMetadata(
            name=meta["name"],
            version=meta["version"],
            description=spec.get("description", ""),
            category=spec.get("category", "general"),
            enabled=spec.get("enabled", True),
            timeout_ms=spec.get("timeout", 3000),
            cache_enabled=spec["config"].get("caching", {}).get("enabled", False),
            cache_ttl_seconds=spec["config"].get("caching", {}).get("ttl", 300),
            inputs=spec.get("inputs", []),
            outputs=spec.get("outputs", []),
            tags=spec.get("tags", []),
        )

    async def list_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[SkillMetadata]:
        """List available skills with optional filtering."""
        skills = list(self._skills.values())

        if category:
            skills = [s for s in skills if s.category == category]

        if tags:
            skills = [
                s for s in skills if any(tag in s.tags for tag in tags)
            ]

        if enabled_only:
            skills = [s for s in skills if s.enabled]

        return skills

    async def get_skill(self, skill_name: str) -> SkillMetadata:
        """Get metadata for a specific skill."""
        if skill_name not in self._skills:
            raise ValueError(f"Skill not found: {skill_name}")
        return self._skills[skill_name]

    async def enable_skill(self, skill_name: str) -> None:
        """Enable a skill."""
        if skill_name not in self._skills:
            raise ValueError(f"Skill not found: {skill_name}")
        self._skills[skill_name].enabled = True

    async def disable_skill(self, skill_name: str) -> None:
        """Disable a skill."""
        if skill_name not in self._skills:
            raise ValueError(f"Skill not found: {skill_name}")
        self._skills[skill_name].enabled = False

    async def reload_skills(self) -> None:
        """Reload all skills from disk."""
        self._skills.clear()
        await self.load_skills()

    async def list_categories(self) -> List[str]:
        """List all skill categories."""
        categories = set(s.category for s in self._skills.values())
        return sorted(categories)

    def get_cache_key(self, skill_name: str, input_data: Dict[str, Any]) -> str:
        """Generate a cache key for skill invocation."""
        import hashlib
        import json

        key_str = f"{skill_name}:{json.dumps(input_data, sort_keys=True)}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        if cache_key in self._cache:
            result, expiry = self._cache[cache_key]
            if time.time() < expiry:
                return result
            else:
                del self._cache[cache_key]
        return None

    async def cache_result(
        self, cache_key: str, result: Any, ttl_seconds: int
    ) -> None:
        """Cache a result with TTL."""
        expiry = time.time() + ttl_seconds
        self._cache[cache_key] = (result, expiry)

    async def invalidate_cache(self, skill_name: Optional[str] = None) -> None:
        """Invalidate cache for a skill or all skills."""
        if skill_name:
            keys_to_delete = [
                k for k in self._cache.keys() if k.startswith(f"{skill_name}:")
            ]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()

    async def close(self) -> None:
        """Clean up resources."""
        self._cache.clear()
