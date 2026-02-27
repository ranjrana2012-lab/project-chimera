"""Skill registry for loading and managing skills."""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime

from ..models.skill import Skill, SkillHealth


class SkillRegistry:
    """Manages skill registration and health monitoring."""

    def __init__(self, config_path: str = "/app/configs/skills"):
        self.config_path = Path(config_path)
        self.skills: Dict[str, Skill] = {}
        self.health: Dict[str, SkillHealth] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load skill configurations from ConfigMaps."""
        try:
            config.load_kube_config()
            api = client.CoreV1Api()

            # Get ConfigMaps in current namespace
            namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read().strip()
            configmaps = api.list_namespaced_config_map(
                namespace=namespace,
                label_selector="project-chimera.io/component=skill"
            )

            for cm in configmaps.items:
                skill_name = cm.metadata.name.replace("-skill-config", "")
                skill_data = json.loads(cm.data["skill.json"])
                self.skills[skill_name] = Skill(**skill_data)

        except Exception as e:
            # Fallback to local files
            if self.config_path.exists():
                for skill_file in self.config_path.glob("*.json"):
                    with open(skill_file) as f:
                        skill_data = json.load(f)
                        skill = Skill(**skill_data)
                        self.skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self.skills.values())

    def get_healthy_skills(self) -> List[Skill]:
        """Get all healthy skills."""
        return [
            skill for skill in self.skills.values()
            if self.health.get(skill.name, SkillHealth(name=skill.name, healthy=False, last_check="")).healthy
        ]

    async def check_health(self, session: aiohttp.ClientSession) -> None:
        """Check health of all skills."""
        for skill in self.skills.values():
            try:
                async with session.get(
                    f"{skill.endpoint}/health/ready",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_healthy = response.status == 200
                    self.health[skill.name] = SkillHealth(
                        name=skill.name,
                        healthy=is_healthy,
                        last_check=datetime.utcnow().isoformat()
                    )
            except Exception as e:
                self.health[skill.name] = SkillHealth(
                    name=skill.name,
                    healthy=False,
                    last_check=datetime.utcnow().isoformat(),
                    error_message=str(e)
                )
