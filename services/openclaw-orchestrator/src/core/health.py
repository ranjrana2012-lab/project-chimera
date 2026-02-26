"""Health checking for OpenClaw Orchestrator"""

import asyncio
import time
from typing import Dict

import redis.asyncio as aioredis
import httpx

from ..config import Settings
from .skill_registry import SkillRegistry


class HealthChecker:
    """Health checker for OpenClaw Orchestrator."""

    def __init__(self, settings: Settings, skill_registry: SkillRegistry):
        self.settings = settings
        self.skill_registry = skill_registry
        self.start_time = time.time()
        self._redis_client: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis client."""
        if self._redis_client is None:
            self._redis_client = await aioredis.from_url(
                f"redis://{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}",
                password=self.settings.redis_password or None,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis_client

    async def _check_redis(self) -> str:
        """Check Redis connection."""
        try:
            redis = await self._get_redis()
            await redis.ping()
            return "healthy"
        except Exception:
            return "unhealthy"

    async def _check_skill_service(self, name: str, url: str) -> str:
        """Check a skill service health."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{url}/health/ready")
                if response.status_code == 200:
                    return "healthy"
                return "degraded"
        except Exception:
            return "unhealthy"

    async def check_liveness(self) -> Dict:
        """Check if the service is alive."""
        uptime = time.time() - self.start_time

        return {
            "status": "healthy",
            "version": self.settings.app_version,
            "uptime_seconds": uptime,
            "components": {
                "orchestrator": "healthy",
            },
            "dependencies": {},
        }

    async def check_readiness(self) -> Dict:
        """Check if the service is ready to accept traffic."""
        components = {
            "skill_registry": "healthy" if self.skill_registry.is_loaded else "starting",
        }

        dependencies = {}

        # Check Redis
        redis_status = await self._check_redis()
        dependencies["redis"] = redis_status

        # Check skill services
        dependencies["scenespeak"] = await self._check_skill_service(
            "scenespeak", self.settings.scenespeak_endpoint
        )
        dependencies["captioning"] = await self._check_skill_service(
            "captioning", self.settings.captioning_endpoint
        )
        dependencies["safety"] = await self._check_skill_service(
            "safety", self.settings.safety_endpoint
        )

        # Determine overall status
        all_healthy = all(
            status == "healthy" for status in dependencies.values()
        ) and all(
            status == "healthy" for status in components.values()
        )

        overall_status = "healthy" if all_healthy else "degraded"

        return {
            "status": overall_status,
            "version": self.settings.app_version,
            "uptime_seconds": time.time() - self.start_time,
            "components": components,
            "dependencies": dependencies,
        }

    async def check_startup(self) -> Dict:
        """Check if the service has started successfully."""
        return await self.check_readiness()

    async def close(self):
        """Close connections."""
        if self._redis_client:
            await self._redis_client.close()
