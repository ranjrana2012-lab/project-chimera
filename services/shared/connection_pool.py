"""
Connection Pool Manager for Project Chimera services.

Manages persistent HTTP connections between services to eliminate
TCP handshake overhead and improve performance.

Usage:
    pool = ConnectionPoolManager(max_connections=10)
    session = await pool.get_session("http://sentiment-agent:8004")
    response = await session.get("/health")
"""

import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Statistics for a connection pool."""
    service_url: str
    total_requests: int = 0
    active_connections: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class ConnectionPoolManager:
    """
    Manages persistent HTTP connections between services.

    Features:
    - Reuses connections across requests to same service
    - Configurable pool size per service
    - Automatic cleanup of stale connections
    - Connection health checking
    - Statistics tracking for monitoring
    """

    def __init__(
        self,
        max_connections: int = 10,
        max_keepalive_connections: int = 5,
        connection_timeout: float = 30.0,
        read_timeout: float = 60.0,
        keepalive_expiry: float = 300.0,
    ):
        """
        Initialize the connection pool manager.

        Args:
            max_connections: Maximum number of connections per service pool
            max_keepalive_connections: Maximum number of keepalive connections to cache
            connection_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
            keepalive_expiry: Expire keepalive connections after this many seconds
        """
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.keepalive_expiry = keepalive_expiry

        # Pool storage: service_url -> httpx.AsyncClient
        self._pools: Dict[str, httpx.AsyncClient] = {}
        self._stats: Dict[str, PoolStats] = {}
        self._lock = asyncio.Lock()

    async def get_session(self, service_url: str) -> httpx.AsyncClient:
        """
        Get or create a pooled HTTP session for the service.

        Args:
            service_url: Base URL of the service (e.g., "http://sentiment-agent:8004")

        Returns:
            httpx.AsyncClient configured for the service
        """
        async with self._lock:
            # Return existing session if available and healthy
            if service_url in self._pools:
                client = self._pools[service_url]
                stats = self._stats[service_url]

                # Check if connection is stale
                if stats.last_used:
                    age = (datetime.utcnow() - stats.last_used).total_seconds()
                    if age > self.keepalive_expiry:
                        logger.info(f"Closing stale connection to {service_url}")
                        await self._close_session(service_url)
                    else:
                        stats.last_used = datetime.utcnow()
                        stats.active_connections += 1
                        return client

            # Create new session
            logger.info(f"Creating new connection pool for {service_url}")
            client = httpx.AsyncClient(
                base_url=service_url,
                limits=httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive_connections,
                ),
                timeout=httpx.Timeout(
                    connect=self.connection_timeout,
                    read=self.read_timeout,
                    write=self.read_timeout,
                    pool=self.connection_timeout,
                ),
            )

            self._pools[service_url] = client
            self._stats[service_url] = PoolStats(
                service_url=service_url,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
            )

            return client

    async def release_session(self, service_url: str) -> None:
        """
        Release a session back to the pool (decrement active count).

        Args:
            service_url: Base URL of the service
        """
        if service_url in self._stats:
            self._stats[service_url].active_connections = max(
                0, self._stats[service_url].active_connections - 1
            )
            self._stats[service_url].last_used = datetime.utcnow()

    async def _close_session(self, service_url: str) -> None:
        """
        Close and remove a session from the pool.

        Args:
            service_url: Base URL of the service
        """
        if service_url in self._pools:
            await self._pools[service_url].aclose()
            del self._pools[service_url]
            if service_url in self._stats:
                del self._stats[service_url]

    async def close_all(self) -> None:
        """Close all connection pools."""
        logger.info("Closing all connection pools")
        async with self._lock:
            for service_url in list(self._pools.keys()):
                await self._close_session(service_url)

    def get_stats(self, service_url: str) -> Optional[PoolStats]:
        """
        Get statistics for a service's connection pool.

        Args:
            service_url: Base URL of the service

        Returns:
            PoolStats if available, None otherwise
        """
        return self._stats.get(service_url)

    def get_all_stats(self) -> Dict[str, PoolStats]:
        """Get statistics for all connection pools."""
        return self._stats.copy()

    async def health_check(self, service_url: str) -> bool:
        """
        Perform health check on a service using pooled connection.

        Args:
            service_url: Base URL of the service

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            session = await self.get_session(service_url)
            response = await session.get("/health", timeout=5.0)
            is_healthy = response.status_code == 200

            if is_healthy:
                stats = self._stats.get(service_url)
                if stats:
                    stats.total_requests += 1
            else:
                stats = self._stats.get(service_url)
                if stats:
                    stats.failed_requests += 1

            return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for {service_url}: {e}")
            stats = self._stats.get(service_url)
            if stats:
                stats.failed_requests += 1
            return False


# Global connection pool instance
_global_pool: Optional[ConnectionPoolManager] = None


def get_global_pool() -> ConnectionPoolManager:
    """Get or create the global connection pool instance."""
    global _global_pool
    if _global_pool is None:
        _global_pool = ConnectionPoolManager()
    return _global_pool


async def close_global_pool() -> None:
    """Close the global connection pool instance."""
    global _global_pool
    if _global_pool is not None:
        await _global_pool.close_all()
        _global_pool = None


__all__ = [
    "ConnectionPoolManager",
    "PoolStats",
    "get_global_pool",
    "close_global_pool",
]
