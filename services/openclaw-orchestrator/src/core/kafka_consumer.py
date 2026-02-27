"""Kafka event consumer."""
import json
from typing import Callable, Dict, Any
from aiokafka import AIOKafkaConsumer
import asyncio


class KafkaConsumer:
    """Consumes events from Kafka."""

    def __init__(self, bootstrap_servers: str, topics: list[str]):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.consumer = None
        self.handlers: Dict[str, Callable] = {}

    def on(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self.handlers[event_type] = handler

    async def start(self, group_id: str = "openclaw-orchestrator"):
        """Start the consumer."""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        await self.consumer.start()

    async def stop(self):
        """Stop the consumer."""
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        """Consume and process events."""
        async for msg in self.consumer:
            event = msg.value
            event_type = event.get("event_type")

            handler = self.handlers.get(event_type)
            if handler:
                await handler(event)
