"""
Metrics collector for Operator Console.

Collects metrics from all services via their Prometheus endpoints.
"""

import asyncio
import logging
import httpx
from typing import Dict, Optional, List
from datetime import datetime
from prometheus_client.parser import text_string_to_metric_families

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates metrics from all services."""

    def __init__(self, service_urls: Dict[str, str], poll_interval: float = 5.0, timeout: float = 5.0):
        """Initialize the metrics collector.

        Args:
            service_urls: Dictionary mapping service names to their base URLs
            poll_interval: Seconds between metric collection cycles
            timeout: HTTP request timeout in seconds
        """
        self.service_urls = service_urls
        self.poll_interval = poll_interval
        self.timeout = timeout
        self._latest_metrics: Dict[str, Dict[str, float]] = {}
        self._service_status: Dict[str, str] = {}
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the metrics collection loop."""
        if self._running:
            logger.warning("Metrics collector already running")
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info(f"Metrics collector started with {self.poll_interval}s interval")

    async def stop(self) -> None:
        """Stop the metrics collection loop."""
        if not self._running:
            return

        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self) -> None:
        """Main metrics collection loop."""
        while self._running:
            start_time = asyncio.get_event_loop().time()

            # Collect metrics from all services
            await self._collect_from_all_services()

            # Calculate sleep time to maintain poll interval
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, self.poll_interval - elapsed)
            await asyncio.sleep(sleep_time)

    async def _collect_from_all_services(self) -> None:
        """Collect metrics from all configured services."""
        tasks = [
            self._collect_service_metrics(service_name, service_url)
            for service_name, service_url in self.service_urls.items()
        ]

        # Run all collections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for service_name, result in zip(self.service_urls.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to collect metrics from {service_name}: {result}")
                self._service_status[service_name] = "down"
            elif result is None:
                self._service_status[service_name] = "down"
            else:
                self._service_status[service_name] = "up"

    async def _collect_service_metrics(self, service_name: str, service_url: str) -> Optional[Dict[str, float]]:
        """Collect metrics from a single service.

        Args:
            service_name: Name of the service
            service_url: Base URL of the service

        Returns:
            Dictionary of metric names to values, or None if collection failed
        """
        metrics_url = f"{service_url}/metrics"
        health_url = f"{service_url}/health/live"

        # First check if service is healthy
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                health_response = await client.get(health_url)
                if health_response.status_code != 200:
                    logger.warning(f"Service {service_name} health check failed: {health_response.status_code}")
                    return None
        except Exception as e:
            logger.debug(f"Health check failed for {service_name}: {e}")
            return None

        # Collect metrics
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(metrics_url)
                response.raise_for_status()

                # Parse Prometheus metrics
                metrics = self._parse_prometheus_metrics(response.text)

                # Store latest metrics
                if metrics:
                    self._latest_metrics[service_name] = metrics

                return metrics

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error collecting metrics from {service_name}: {e}")
        except httpx.ConnectError as e:
            logger.warning(f"Connection error collecting metrics from {service_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error collecting metrics from {service_name}: {e}")

        return None

    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, float]:
        """Parse Prometheus metrics text format.

        Args:
            metrics_text: Raw Prometheus metrics text

        Returns:
            Dictionary of metric names to values
        """
        metrics = {}

        try:
            for family in text_string_to_metric_families(metrics_text):
                # Skip metrics that are too complex or have multiple labels
                if len(family.samples) == 1 and not family.samples[0].labels:
                    metric_name = family.name
                    metric_value = family.samples[0].value
                    metrics[metric_name] = metric_value
                elif family.samples:
                    # For metrics with labels, use the first sample's value
                    # In production, you might want to aggregate or handle differently
                    metric_name = family.name
                    metric_value = family.samples[0].value
                    metrics[metric_name] = metric_value

        except Exception as e:
            logger.error(f"Error parsing Prometheus metrics: {e}")

        return metrics

    async def collect_once(self) -> Dict[str, Dict[str, float]]:
        """Collect metrics from all services once (non-blocking).

        Returns:
            Dictionary mapping service names to their metrics
        """
        await self._collect_from_all_services()
        return self._latest_metrics.copy()

    def get_metrics(self, service_name: str) -> Optional[Dict[str, float]]:
        """Get latest metrics for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary of metric names to values, or None if not available
        """
        return self._latest_metrics.get(service_name)

    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get all collected metrics.

        Returns:
            Dictionary mapping service names to their metrics
        """
        return self._latest_metrics.copy()

    def get_service_status(self, service_name: str) -> str:
        """Get status of a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Service status: "up", "down", or "unknown"
        """
        return self._service_status.get(service_name, "unknown")

    def get_all_service_status(self) -> Dict[str, str]:
        """Get status of all services.

        Returns:
            Dictionary mapping service names to their status
        """
        return self._service_status.copy()

    def is_running(self) -> bool:
        """Check if the collector is running.

        Returns:
            True if collector is running, False otherwise
        """
        return self._running


__all__ = [
    "MetricsCollector",
]
