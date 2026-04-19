import asyncio
import json
import logging
import os
from typing import Callable, Awaitable, Dict, Any, List, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

logger = logging.getLogger(__name__)

class KafkaEventBus:
    def __init__(self, bootstrap_servers: str, service_name: str):
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.producer = None
        self.consumers: List[AIOKafkaConsumer] = []
        self.consumer_tasks: List[asyncio.Task] = []

    async def start(self):
        """Initialize the Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info(f"{self.service_name} Kafka EventBus producer started")

    async def stop(self):
        """Stop producer and all consumers"""
        if self.producer:
            await self.producer.stop()
            logger.info(f"{self.service_name} Kafka EventBus producer stopped")
        
        for task in self.consumer_tasks:
            task.cancel()
        
        for consumer in self.consumers:
            await consumer.stop()

    async def publish(self, topic: str, payload: dict, key: Optional[str] = None):
        """Publish a message to a Kafka topic"""
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")
        
        b_key = key.encode('utf-8') if key else None
        await self.producer.send_and_wait(topic, value=payload, key=b_key)
        logger.debug(f"Published to {topic}: {payload}")

    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Subscribe to a Kafka topic and process messages with the handler"""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=f"{self.service_name}-group",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset="latest" # "earliest" if you want to retry old missed messages
        )
        await consumer.start()
        self.consumers.append(consumer)
        logger.info(f"{self.service_name} Subscribed to topic {topic}")

        async def _consume_loop():
            try:
                async for msg in consumer:
                    logger.debug(f"Received from {topic}: {msg.value}")
                    try:
                        await handler(msg.value)
                    except Exception as e:
                        logger.error(f"Error handling message from {topic}: {e}", exc_info=True)
            except asyncio.CancelledError:
                logger.info(f"Consumer loop for {topic} cancelled")
            except Exception as e:
                logger.error(f"Consumer loop for {topic} threw an exception: {e}")

        task = asyncio.create_task(_consume_loop())
        self.consumer_tasks.append(task)
