"""Core handler for Sentiment Agent"""

import time
from typing import Dict, Any, List
from .sentiment_analyzer import SentimentAnalyzer


class SentimentHandler:
    def __init__(self, settings):
        self.settings = settings
        self.analyzer = SentimentAnalyzer(settings)

    async def initialize(self):
        await self.analyzer.load_model()

    async def analyze(self, text: str) -> Dict[str, Any]:
        start_time = time.time()
        result = await self.analyzer.analyze(text)
        return {
            **result,
            "latency_ms": (time.time() - start_time) * 1000,
        }

    async def analyze_batch(self, texts: List[str]) -> Dict[str, Any]:
        start_time = time.time()
        results = await self.analyzer.analyze_batch(texts)
        return {
            "results": results,
            "latency_ms": (time.time() - start_time) * 1000,
        }

    async def close(self):
        await self.analyzer.close()
