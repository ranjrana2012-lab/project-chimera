"""Kafka event producer."""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from aiokafka import AIOKafkaProducer
import asyncio


class KafkaProducer:
    """Produces events to Kafka."""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        """Start the producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        await self.producer.start()

    async def stop(self):
        """Stop the producer."""
        if self.producer:
            await self.producer.stop()

    async def publish(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        source_service: str = "openclaw-orchestrator"
    ) -> None:
        """Publish an event to Kafka."""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_service": source_service,
            "data": data
        }

        await self.producer.send_and_wait(topic, value=event)
