"""Manual override manager for Operator Console."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from aiokafka import AIOKafkaProducer

from src.models.request import OverrideRequest, OverrideType
from src.models.response import ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)


class ActiveOverride:
    """Represents an active override."""

    def __init__(
        self,
        override_id: str,
        request: OverrideRequest,
        initiated_by: str,
    ):
        """Initialize active override.

        Args:
            override_id: Unique override ID
            request: Override request
            initiated_by: Operator who initiated
        """
        self.override_id = override_id
        self.request = request
        self.initiated_by = initiated_by
        self.created_at = datetime.now()
        self.active = True

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "override_id": self.override_id,
            "override_type": self.request.override_type.value,
            "target_service": self.request.target_service,
            "reason": self.request.reason,
            "initiated_by": self.initiated_by,
            "created_at": self.created_at.isoformat(),
            "active": self.active,
            "parameters": self.request.parameter,
        }


class OverrideManager:
    """Manages manual overrides for services."""

    def __init__(
        self,
        kafka_brokers: str = "localhost:9092",
        override_topic: str = "chimera.overrides",
    ):
        """Initialize override manager.

        Args:
            kafka_brokers: Kafka broker addresses
            override_topic: Topic for override commands
        """
        self.kafka_brokers = kafka_brokers
        self.override_topic = override_topic

        self.active_overrides: dict[str, ActiveOverride] = {}
        self.override_history: list[dict] = []
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False
        self._override_counter = 0

    async def start(self) -> None:
        """Start override manager."""
        logger.info("Starting override manager")

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        await self.producer.start()
        self.running = True

        logger.info("Override manager started")

    async def stop(self) -> None:
        """Stop override manager."""
        logger.info("Stopping override manager")
        self.running = False

        # Deactivate all active overrides
        for override in list(self.active_overrides.values()):
            await self.release_override(override.override_id, "system_shutdown")

        if self.producer:
            await self.producer.stop()

        logger.info("Override manager stopped")

    async def trigger_override(
        self,
        request: OverrideRequest,
        initiated_by: str,
    ) -> str:
        """Trigger a manual override.

        Args:
            request: Override request
            initiated_by: Operator initiating override

        Returns:
            Override ID
        """
        self._override_counter += 1
        override_id = f"override_{self._override_counter}_{int(datetime.now().timestamp())}"

        override = ActiveOverride(override_id, request, initiated_by)
        self.active_overrides[override_id] = override

        logger.warning(
            f"Override triggered: {override_id} - {request.override_type.value} "
            f"on {request.target_service} by {initiated_by}"
        )

        # Broadcast override command
        await self._broadcast_override(override)

        return override_id

    async def release_override(
        self,
        override_id: str,
        released_by: str,
    ) -> bool:
        """Release an active override.

        Args:
            override_id: Override to release
            released_by: Operator releasing override

        Returns:
            True if released successfully
        """
        if override_id not in self.active_overrides:
            logger.warning(f"Override not found: {override_id}")
            return False

        override = self.active_overrides[override_id]
        override.active = False

        logger.info(f"Override released: {override_id} by {released_by}")

        # Add to history
        self.override_history.append(override.to_dict())

        # Remove from active
        del self.active_overrides[override_id]

        # Broadcast release
        await self._broadcast_release(override_id, override.request.target_service)

        return True

    async def _broadcast_override(self, override: ActiveOverride) -> None:
        """Broadcast override command to Kafka.

        Args:
            override: Override to broadcast
        """
        if not self.producer:
            return

        await self.producer.send_and_wait(
            self.override_topic,
            value={
                "event_type": "override_triggered",
                "override_id": override.override_id,
                "override_type": override.request.override_type.value,
                "target_service": override.request.target_service,
                "reason": override.request.reason,
                "initiated_by": override.initiated_by,
                "parameters": override.request.parameter,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _broadcast_release(self, override_id: str, target_service: str) -> None:
        """Broadcast override release to Kafka.

        Args:
            override_id: Override being released
            target_service: Target service
        """
        if not self.producer:
            return

        await self.producer.send_and_wait(
            self.override_topic,
            value={
                "event_type": "override_released",
                "override_id": override_id,
                "target_service": target_service,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def emergency_stop_all(self, initiated_by: str, reason: str) -> str:
        """Trigger emergency stop on all services.

        Args:
            initiated_by: Operator initiating stop
            reason: Reason for emergency stop

        Returns:
            Override ID
        """
        request = OverrideRequest(
            override_type=OverrideType.EMERGENCY_STOP,
            target_service="all",
            reason=reason,
        )

        override_id = await self.trigger_override(request, initiated_by)

        logger.critical(f"EMERGENCY STOP triggered by {initiated_by}: {reason}")

        return override_id

    def get_active_overrides(self) -> list[dict]:
        """Get all active overrides.

        Returns:
            List of active overrides
        """
        return [o.to_dict() for o in self.active_overrides.values()]

    def get_override(self, override_id: str) -> Optional[dict]:
        """Get specific override.

        Args:
            override_id: Override ID

        Returns:
            Override dict or None
        """
        override = self.active_overrides.get(override_id)
        return override.to_dict() if override else None

    def get_overrides_for_service(self, service_name: str) -> list[dict]:
        """Get active overrides for a service.

        Args:
            service_name: Service name

        Returns:
            List of overrides
        """
        return [
            o.to_dict()
            for o in self.active_overrides.values()
            if o.request.target_service in (service_name, "all")
        ]

    def get_history(self, limit: int = 100) -> list[dict]:
        """Get override history.

        Args:
            limit: Maximum results

        Returns:
            List of historical overrides
        """
        return self.override_history[-limit:]

    def get_stats(self) -> dict:
        """Get override statistics.

        Returns:
            Statistics dictionary
        """
        override_counts = {}
        for override in self.active_overrides.values():
            otype = override.request.override_type.value
            override_counts[otype] = override_counts.get(otype, 0) + 1

        return {
            "active_count": len(self.active_overrides),
            "total_history": len(self.override_history),
            "override_counts": override_counts,
        }
