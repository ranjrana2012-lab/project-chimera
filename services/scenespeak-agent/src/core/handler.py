"""
Core handler for SceneSpeak Agent
"""

import time
from typing import Any, Dict, Optional

from .context_builder import ContextBuilder
from .prompt_composer import PromptComposer
from .inference_engine import InferenceEngine
from .caches.redis_cache import RedisCache
from ..config import Settings


class SceneSpeakHandler:
    """Main handler for SceneSpeak operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.context_builder: Optional[ContextBuilder] = None
        self.prompt_composer: Optional[PromptComposer] = None
        self.inference_engine: Optional[InferenceEngine] = None
        self.cache: Optional[RedisCache] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the handler and its components."""
        # Initialize cache
        if self.settings.cache_enabled:
            self.cache = RedisCache(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                password=self.settings.redis_password or None,
            )
            await self.cache.connect()

        # Initialize components
        self.context_builder = ContextBuilder(self.settings)
        self.prompt_composer = PromptComposer(
            self.settings.prompts_path,
            self.settings.default_prompt_version,
        )
        self.inference_engine = InferenceEngine(self.settings)

        # Load model
        await self.inference_engine.load_model()

        self._initialized = True

    async def generate_dialogue(
        self,
        scene_context: Dict[str, Any],
        dialogue_context: list,
        sentiment_vector: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate dialogue for a scene.

        Args:
            scene_context: Current scene state
            dialogue_context: Recent dialogue turns
            sentiment_vector: Audience sentiment (optional)

        Returns:
            Generated dialogue and metadata
        """
        start_time = time.time()

        # Build context
        full_context = await self.context_builder.build(
            scene_context=scene_context,
            dialogue_context=dialogue_context,
            sentiment_vector=sentiment_vector,
        )

        # Check cache
        cache_key = None
        if self.cache:
            import json
            import hashlib
            cache_data = json.dumps(full_context, sort_keys=True)
            cache_key = f"scenespeak:{hashlib.sha256(cache_data.encode()).hexdigest()}"

            cached = await self.cache.get(cache_key)
            if cached:
                return {
                    **cached,
                    "cached": True,
                    "latency_ms": (time.time() - start_time) * 1000,
                }

        # Compose prompt
        prompt = await self.prompt_composer.compose(full_context)

        # Run inference
        result = await self.inference_engine.generate(
            prompt=prompt,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            top_p=self.settings.top_p,
            top_k=self.settings.top_k,
        )

        response = {
            "proposed_lines": result["text"],
            "stage_cues": result.get("stage_cues", []),
            "metadata": {
                "model": self.settings.model_name,
                "tokens_used": result.get("tokens_used", 0),
                "generation_id": result.get("generation_id", ""),
            },
            "cached": False,
            "latency_ms": (time.time() - start_time) * 1000,
        }

        # Cache result
        if self.cache and cache_key:
            await self.cache.set(
                cache_key,
                response,
                ttl=self.settings.cache_ttl_seconds,
            )

        return response

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the service."""
        return {
            "status": "healthy" if self._initialized else "initializing",
            "model_loaded": self.inference_engine.is_loaded if self.inference_engine else False,
            "cache_connected": self.cache.is_connected if self.cache else False,
        }

    async def close(self) -> None:
        """Clean up resources."""
        if self.inference_engine:
            await self.inference_engine.close()
        if self.cache:
            await self.cache.close()
