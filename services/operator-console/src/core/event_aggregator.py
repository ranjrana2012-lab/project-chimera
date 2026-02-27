"""Event aggregation from Kafka for Operator Console."""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from src.models.response import EventType, EventSeverity, StreamEvent

logger = logging.getLogger(__name__)


class EventAggregator:
    """Aggregates events from Kafka topics for console display."""

    def __init__(
        self,
        kafka_brokers: str = "localhost:9092",
        topics: list[str] = [
            "chimera.events",
            "chimera.approvals",
            "chimera.overrides",
            "chimera.health",
        ],
        max_events: int = 1000,
    ):
        """Initialize event aggregator.

        Args:
            kafka_brokers: Kafka broker addresses
            topics: Topics to consume
            max_events: Maximum events to keep in memory
        """
        self.kafka_brokers = kafka_brokers
        self.topics = topics
        self.max_events = max_events
        self.events: deque[StreamEvent] = deque(maxlen=max_events)
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self._subscribers: list[asyncio.Queue] = []

    async def start(self) -> None:
        """Start consuming events from Kafka."""
        logger.info(f"Starting event aggregator for topics: {self.topics}")

        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.kafka_brokers,
            group_id="operator-console",
            auto_offset_reset="latest",
            value_deserializer=lambda m: m.decode("utf-8"),
        )

        await self.consumer.start()
        self.running = True

        asyncio.create_task(self._consume_events())
        logger.info("Event aggregator started")

    async def stop(self) -> None:
        """Stop consuming events."""
        logger.info("Stopping event aggregator")
        self.running = False

        if self.consumer:
            await self.consumer.stop()

        logger.info("Event aggregator stopped")

    async def _consume_events(self) -> None:
        """Continuously consume events from Kafka."""
        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                try:
                    event = self._parse_event(msg)
                    if event:
                        self.events.append(event)
                        await self._notify_subscribers(event)
                        logger.debug(f"Processed event: {event.event_type}")

                except Exception as e:
                    logger.error(f"Error processing event: {e}")

        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")

    def _parse_event(self, msg) -> Optional[StreamEvent]:
        """Parse Kafka message into StreamEvent.

        Args:
            msg: Kafka message

        Returns:
            StreamEvent or None if parsing fails
        """
        try:
            data = json.loads(msg.value) if isinstance(msg.value, str) else msg.value

            # Map topic to event type
            topic_mapping = {
                "chimera.events": EventType.INFO,
                "chimera.approvals": EventType.APPROVAL_REQUESTED,
                "chimera.overrides": EventType.OVERRIDE_TRIGGERED,
                "chimera.health": EventType.SERVICE_STATUS_CHANGE,
            }

            event_type = topic_mapping.get(msg.topic, EventType.INFO)

            # Determine severity
            severity = EventSeverity.INFO
            if data.get("severity"):
                severity = EventSeverity(data["severity"])
            elif data.get("error"):
                severity = EventSeverity.ERROR
            elif data.get("warning"):
                severity = EventSeverity.WARNING

            event = StreamEvent(
                event_id=data.get("event_id") or f"{msg.topic}_{msg.offset}",
                event_type=EventType(data.get("event_type", event_type)),
                severity=severity,
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                source_service=data.get("source_service", msg.topic.split(".")[1]),
                title=data.get("title", "Event"),
                message=data.get("message", ""),
                data=data.get("data", {}),
                requires_approval=data.get("requires_approval", False),
                approval_id=data.get("approval_id"),
            )

            return event

        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            logger.error(f"Failed to parse event: {e}")
            return None

    async def _notify_subscribers(self, event: StreamEvent) -> None:
        """Notify all subscribers of new event.

        Args:
            event: Event to broadcast
        """
        for queue in self._subscribers:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to event stream.

        Returns:
            Queue that will receive new events
        """
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from event stream.

        Args:
            queue: Queue to unsubscribe
        """
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_recent_events(
        self, limit: int = 100, event_type: Optional[EventType] = None
    ) -> list[StreamEvent]:
        """Get recent events from buffer.

        Args:
            limit: Maximum events to return
            event_type: Filter by event type

        Returns:
            List of recent events
        """
        events = list(self.events)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]

    def get_stats(self) -> dict:
        """Get aggregator statistics.

        Returns:
            Statistics dictionary
        """
        events_by_type = {}
        events_by_severity = {}

        for event in self.events:
            events_by_type[event.event_type.value] = events_by_type.get(event.event_type.value, 0) + 1
            events_by_severity[event.severity.value] = events_by_severity.get(event.severity.value, 0) + 1

        return {
            "total_events": len(self.events),
            "subscriber_count": len(self._subscribers),
            "events_by_type": events_by_type,
            "events_by_severity": events_by_severity,
            "buffer_usage": len(self.events) / self.max_events,
        }
