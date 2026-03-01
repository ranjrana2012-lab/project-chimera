from typing import Any
from music_orchestration.cache import CacheManager
from music_orchestration.schemas import MusicRequest, UserContext, UseCase
from music_orchestration.auth import PermissionChecker


class RequestRouter:
    """Routes requests to cache or generation service"""

    def __init__(
        self,
        cache: CacheManager,
        generation_client: Any | None = None
    ):
        self.cache = cache
        self.generation_client = generation_client

    async def route(
        self,
        request: MusicRequest,
        user: UserContext
    ) -> dict[str, Any]:
        """Route request to cache or generation"""
        # Check permissions
        PermissionChecker.require_permission("music:generate")(user)

        # Check cache first
        cache_key = self.cache.get_cache_key(request)
        cached = await self.cache.get(cache_key)

        if cached:
            return {
                "music_id": cached.get("music_id"),
                "status": "cached",
                "was_cache_hit": True
            }

        # Route to generation
        if not self.generation_client:
            return {
                "music_id": None,
                "status": "error",
                "error": "Generation service not available"
            }

        # Select model based on use case
        model_name = self._select_model(request.use_case)

        # Call generation service
        result = await self.generation_client.generate(
            model_name=model_name,
            prompt=request.prompt,
            duration_seconds=request.duration_seconds
        )

        return {
            "music_id": result.get("music_id"),
            "status": "generating",
            "was_cache_hit": False
        }

    def _select_model(self, use_case: UseCase) -> str:
        """Select model based on use case"""
        if use_case == UseCase.MARKETING:
            return "musicgen"
        return "acestep"
