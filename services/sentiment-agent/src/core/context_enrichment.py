"""Context enrichment for sentiment analysis."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import httpx

from ..models.context import GlobalContext, ContextEnrichmentOptions

logger = logging.getLogger(__name__)


class ContextEnricher:
    """Enriches sentiment responses with global context from WorldMonitor."""

    def __init__(self, sidecar_url: str):
        self.sidecar_url = sidecar_url.rstrip('/')
        self._context_cache: Optional[GlobalContext] = None
        self._cache_timestamp: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_context(self, options: ContextEnrichmentOptions) -> Optional[GlobalContext]:
        """Get global context, using cache if fresh."""
        if not options.include_context:
            return None

        # Check cache freshness (default 5 minutes)
        cache_ttl = 300
        if self._context_cache and self._cache_timestamp:
            age = (datetime.now() - self._cache_timestamp).total_seconds()
            if age < cache_ttl:
                return self._filter_context(self._context_cache, options)

        # Fetch fresh context
        try:
            context = await self._fetch_context()
            if context:
                self._context_cache = context
                self._cache_timestamp = datetime.now()
                return self._filter_context(context, options)
        except Exception as e:
            logger.warning(f"Failed to fetch context: {e}")
            # Return stale context if available
            if self._context_cache:
                cached = self._filter_context(self._context_cache, options)
                cached.stale = True
                return cached

        return None

    async def _fetch_context(self) -> Optional[GlobalContext]:
        """Fetch context from WorldMonitor sidecar."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.sidecar_url}/api/v1/context/global")
            response.raise_for_status()
            data = response.json()
            return GlobalContext(**data)
        except Exception as e:
            logger.error(f"Error fetching context: {e}")
            return None

    def _filter_context(self, context: GlobalContext, options: ContextEnrichmentOptions) -> GlobalContext:
        """Filter context based on options."""
        # Create a copy to avoid modifying the cached context
        filtered = context.model_copy()

        if not options.include_cii:
            filtered.global_cii = 0
        if not options.include_threats:
            filtered.active_threats = []
        if not options.include_events:
            filtered.major_events = []

        return filtered

    async def get_country_context(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get country-specific context."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.sidecar_url}/api/v1/context/country/{country_code}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching country context: {e}")
            return None

    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get the current cached context as a dict for WebSocket streaming."""
        if self._context_cache:
            return self._context_cache.model_dump()
        return None
