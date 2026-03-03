"""News sentiment analyzer using WorldMonitor news feeds."""

import logging
from typing import List, Dict, Any
from datetime import datetime
import time

import httpx

from src.config import settings
from src.models.context import NewsSentimentRequest, NewsSentimentResponse
from src.core.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)


class NewsSentimentAnalyzer:
    """Analyzes sentiment of news articles from WorldMonitor."""

    def __init__(self, sidecar_url: str, sentiment_analyzer: SentimentAnalyzer):
        self.sidecar_url = sidecar_url.rstrip('/')
        self.sentiment_analyzer = sentiment_analyzer
        self._http_client: httpx.AsyncClient = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def analyze_news(self, request: NewsSentimentRequest) -> NewsSentimentResponse:
        """Analyze sentiment of news articles."""
        start_time = time.time()

        # Fetch news from sidecar
        articles = await self._fetch_news(request)

        if not articles:
            return NewsSentimentResponse(
                analyzed_articles=0,
                average_sentiment="neutral",
                sentiment_distribution={},
                processing_time_ms=(time.time() - start_time) * 1000
            )

        # Analyze sentiment
        sentiments = []
        for article in articles[:request.max_articles]:
            text = f"{article.get('title', '')} {article.get('content', '')}"
            result = await self.sentiment_analyzer.analyze(text[:500])  # Limit text length
            sentiments.append({
                'article': article,
                'sentiment': result['sentiment']['label'],
                'confidence': result['sentiment']['confidence']
            })

        # Calculate statistics
        sentiment_counts = {}
        for s in sentiments:
            label = s['sentiment']
            sentiment_counts[label] = sentiment_counts.get(label, 0) + 1

        avg_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"

        # Sort by sentiment
        positive = [s for s in sentiments if s['sentiment'] == 'positive']
        negative = [s for s in sentiments if s['sentiment'] == 'negative']

        top_positive = sorted(positive, key=lambda x: x['confidence'], reverse=True)[:5]
        top_negative = sorted(negative, key=lambda x: x['confidence'], reverse=True)[:5]

        return NewsSentimentResponse(
            analyzed_articles=len(sentiments),
            average_sentiment=avg_sentiment,
            sentiment_distribution=sentiment_counts,
            top_positive=[{
                'title': s['article'].get('title'),
                'source': s['article'].get('source'),
                'confidence': s['confidence']
            } for s in top_positive],
            top_negative=[{
                'title': s['article'].get('title'),
                'source': s['article'].get('source'),
                'confidence': s['confidence']
            } for s in top_negative],
            processing_time_ms=(time.time() - start_time) * 1000
        )

    async def _fetch_news(self, request: NewsSentimentRequest) -> List[Dict[str, Any]]:
        """Fetch news from WorldMonitor sidecar."""
        try:
            client = await self._get_client()

            params = {}
            if request.sources:
                params['sources'] = ','.join(request.sources)
            if request.categories:
                params['categories'] = ','.join(request.categories)
            if request.hours:
                params['hours'] = request.hours

            response = await client.get(f"{self.sidecar_url}/api/v1/news", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('articles', [])
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
