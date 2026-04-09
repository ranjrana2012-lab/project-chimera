"""LTX-2 API client for video generation"""

import httpx
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from models import (
    LTXVideoRequest, LTXVideoResult, LTXModel, Resolution, CameraMotion
)
from metrics import video_generation_duration, active_generations


class LTXAPIClient:
    """Async client for LTX-2 API"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.ltx.video/v1",
        timeout: int = 300
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def text_to_video(
        self,
        prompt: str,
        duration: int = 10,
        resolution: str = "1920x1080",
        fps: int = 24,
        model: str = "ltx-2-3-pro",
        generate_audio: bool = True,
        camera_motion: Optional[str] = None,
        lora_path: Optional[str] = None
    ) -> LTXVideoResult:
        """Generate video from text prompt"""

        start_time = datetime.utcnow()
        active_generations.inc()

        try:
            payload = {
                "prompt": prompt,
                "duration": duration,
                "resolution": resolution,
                "fps": fps,
                "model": model
            }

            if generate_audio:
                payload["generate_audio"] = True

            if camera_motion:
                payload["camera_motion"] = camera_motion

            if lora_path:
                payload["lora_path"] = lora_path

            response = await self._client.post(
                "/text-to-video",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            duration_sec = (datetime.utcnow() - start_time).total_seconds()
            video_generation_duration.labels(
                model=model,
                resolution=resolution
            ).observe(duration_sec)

            return LTXVideoResult(
                video_id=data.get("id", ""),
                url=data.get("url", ""),
                duration=data.get("duration", 0.0),
                resolution=data.get("resolution", resolution),
                fps=data.get("fps", fps),
                has_audio=data.get("has_audio", False),
                status=data.get("status", "processing")
            )

        finally:
            active_generations.dec()

    async def batch_generate(
        self,
        requests: List[LTXVideoRequest],
        max_concurrent: int = 3
    ) -> List[LTXVideoResult]:
        """Generate multiple videos in parallel batches"""

        results = []

        # Process in batches
        for i in range(0, len(requests), max_concurrent):
            batch = requests[i:i + max_concurrent]

            # Parallel generation within batch
            tasks = [
                self.text_to_video(
                    prompt=req.prompt,
                    duration=req.duration,
                    resolution=req.resolution.value,
                    fps=req.fps,
                    model=req.model.value,
                    generate_audio=req.generate_audio,
                    camera_motion=req.camera_motion.value if req.camera_motion else None,
                    lora_path=req.lora_id
                )
                for req in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    # Log error but continue
                    logger.error(f"Error in batch generation: {result}")
                elif result is not None:
                    results.append(result)

        return results

    async def health_check(self) -> bool:
        """Check if LTX API is accessible"""
        try:
            if not self._client:
                # Initialize client for health check
                self._client = httpx.AsyncClient(
                    base_url=self.api_base,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )

            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False


# Global client instance
_client: Optional[LTXAPIClient] = None


def get_ltx_client() -> LTXAPIClient:
    """Get or create global LTX client instance"""
    global _client
    if _client is None:
        from config import settings
        _client = LTXAPIClient(
            api_key=settings.ltx_api_key,
            api_base=settings.ltx_api_base
        )
    return _client
