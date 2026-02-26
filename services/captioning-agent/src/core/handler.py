"""Core handler for Captioning Agent"""

import time
from typing import Dict, Any
from .transcriber import Transcriber


class CaptioningHandler:
    def __init__(self, settings):
        self.settings = settings
        self.transcriber = Transcriber(settings)

    async def initialize(self):
        await self.transcriber.load_model()

    async def transcribe(self, audio_data: bytes, language: str = None) -> Dict[str, Any]:
        start_time = time.time()
        result = await self.transcriber.transcribe(audio_data, language)
        return {
            "text": result["text"],
            "language": result.get("language", self.settings.language),
            "confidence": result.get("confidence", 0.95),
            "timestamp": result.get("timestamp"),
            "latency_ms": (time.time() - start_time) * 1000,
        }

    async def close(self):
        await self.transcriber.close()
