"""Core handler for BSL Text2Gloss Agent"""

import time
from typing import Dict, Any
from .gloss_translator import GlossTranslator


class BSLHandler:
    def __init__(self, settings):
        self.settings = settings
        self.translator = GlossTranslator(settings)

    async def initialize(self):
        await self.translator.load_model()

    async def translate(self, text: str) -> Dict[str, Any]:
        start_time = time.time()
        result = await self.translator.translate_to_gloss(text)
        return {
            "gloss": result["gloss"],
            "breakdown": result.get("breakdown", []),
            "language": "bsl",
            "confidence": result.get("confidence", 0.88),
            "latency_ms": (time.time() - start_time) * 1000,
        }

    async def close(self):
        await self.translator.close()
