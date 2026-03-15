"""Integration with Visual Core service"""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VisualCoreClient:
    """Client for Visual Core service integration"""

    def __init__(self, base_url: str = "http://visual-core:8014"):
        self.base_url = base_url
        self.timeout = 600

    async def generate_video(
        self,
        narrative: str,
        style: str = "corporate_briefing",
        duration: int = 90
    ) -> str:
        """Generate video using Visual Core"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/generate/prompt",
                json={
                    "prompt": narrative,
                    "duration": duration,
                    "style": style
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["url"]
