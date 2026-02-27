"""Tests for OpenClaw Kafka integration."""

import sys
from pathlib import Path
import importlib.util

# Direct module loading to avoid dependency issues
kafka_producer_path = Path(__file__).parent.parent.parent / "services" / "openclaw-orchestrator" / "src" / "core" / "kafka_producer.py"
kafka_consumer_path = Path(__file__).parent.parent.parent / "services" / "openclaw-orchestrator" / "src" / "core" / "kafka_consumer.py"

spec1 = importlib.util.spec_from_file_location("kafka_producer", kafka_producer_path)
kafka_producer_module = importlib.util.module_from_spec(spec1)
sys.modules["kafka_producer"] = kafka_producer_module
spec1.loader.exec_module(kafka_producer_module)

spec2 = importlib.util.spec_from_file_location("kafka_consumer", kafka_consumer_path)
kafka_consumer_module = importlib.util.module_from_spec(spec2)
sys.modules["kafka_consumer"] = kafka_consumer_module
spec2.loader.exec_module(kafka_consumer_module)

KafkaProducer = kafka_producer_module.KafkaProducer
KafkaConsumer = kafka_consumer_module.KafkaConsumer

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.unit
class TestKafkaProducer:
    """Test Kafka producer functionality."""

    @pytest.fixture
    def mock_aiokafka_producer(self):
        """Mock AIOKafkaProducer."""
        with patch("kafka_producer.AIOKafkaProducer") as mock:
            mock_instance = AsyncMock()
            mock_instance.start = AsyncMock()
            mock_instance.stop = AsyncMock()
            mock_instance.send_and_wait = AsyncMock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def producer(self, mock_aiokafka_producer):
        """Create a Kafka producer instance with mocked AIOKafkaProducer."""
        return KafkaProducer(bootstrap_servers="localhost:9092")

    @pytest.mark.asyncio
    async def test_start_producer(self, producer, mock_aiokafka_producer):
        """Test starting the producer."""
        await producer.start()
        assert producer.producer is not None
        mock_aiokafka_producer.assert_called_once()
        producer.producer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_producer(self, producer, mock_aiokafka_producer):
        """Test stopping the producer."""
        await producer.start()
        await producer.stop()
        producer.producer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event(self, producer, mock_aiokafka_producer):
        """Test publishing an event to Kafka."""
        await producer.start()

        topic = "test-topic"
        event_type = "test.event"
        data = {"key": "value"}

        await producer.publish(topic, event_type, data)

        # Verify send_and_wait was called
        producer.producer.send_and_wait.assert_called_once()

        # Get the call arguments
        call_args = producer.producer.send_and_wait.call_args
        assert call_args[0][0] == topic  # First positional arg is topic

        # Verify event structure
        event = call_args[1]["value"]  # value is passed as keyword arg
        assert "event_id" in event
        assert event["event_type"] == event_type
        assert event["event_version"] == "1.0.0"
        assert event["source_service"] == "openclaw-orchestrator"
        assert event["data"] == data
        assert "timestamp" in event

    @pytest.mark.asyncio
    async def test_publish_event_with_custom_source(self, producer, mock_aiokafka_producer):
        """Test publishing an event with custom source service."""
        await producer.start()

        topic = "test-topic"
        event_type = "test.event"
        data = {"key": "value"}
        source_service = "custom-service"

        await producer.publish(topic, event_type, data, source_service=source_service)

        # Get the call arguments
        call_args = producer.producer.send_and_wait.call_args
        event = call_args[1]["value"]
        assert event["source_service"] == source_service

    @pytest.mark.asyncio
    async def test_publish_event_generates_unique_id(self, producer, mock_aiokafka_producer):
        """Test that each published event gets a unique ID."""
        await producer.start()

        event_ids = []
        for _ in range(5):
            await producer.publish("test-topic", "test.event", {"index": len(event_ids)})
            call_args = producer.producer.send_and_wait.call_args
            event = call_args[1]["value"]
            event_ids.append(event["event_id"])

        # All IDs should be unique
        assert len(set(event_ids)) == 5

    @pytest.mark.asyncio
    async def test_publish_event_timestamp_format(self, producer, mock_aiokafka_producer):
        """Test that event timestamp is in ISO format with Z suffix."""
        await producer.start()

        await producer.publish("test-topic", "test.event", {})

        call_args = producer.producer.send_and_wait.call_args
        event = call_args[1]["value"]
        timestamp = event["timestamp"]

        assert timestamp.endswith("Z")
        # Should be parseable as ISO format
        iso_timestamp = timestamp[:-1]  # Remove Z
        datetime.fromisoformat(iso_timestamp)


@pytest.mark.unit
class TestKafkaConsumer:
    """Test Kafka consumer functionality."""

    @pytest.fixture
    def mock_aiokafka_consumer(self):
        """Mock AIOKafkaConsumer."""
        with patch("kafka_consumer.AIOKafkaConsumer") as mock:
            mock_instance = AsyncMock()
            mock_instance.start = AsyncMock()
            mock_instance.stop = AsyncMock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def consumer(self, mock_aiokafka_consumer):
        """Create a Kafka consumer instance with mocked AIOKafkaConsumer."""
        return KafkaConsumer(
            bootstrap_servers="localhost:9092",
            topics=["test-topic-1", "test-topic-2"]
        )

    def test_register_handler(self, consumer):
        """Test registering an event handler."""
        async def handler(event):
            pass

        consumer.on("test.event", handler)
        assert "test.event" in consumer.handlers
        assert consumer.handlers["test.event"] == handler

    @pytest.mark.asyncio
    async def test_start_consumer(self, consumer, mock_aiokafka_consumer):
        """Test starting the consumer."""
        await consumer.start(group_id="test-group")
        assert consumer.consumer is not None
        mock_aiokafka_consumer.assert_called_once()

        # Verify consumer was created with correct topics
        call_args = mock_aiokafka_consumer.call_args
        assert "test-topic-1" in call_args[0]
        assert "test-topic-2" in call_args[0]

    @pytest.mark.asyncio
    async def test_start_consumer_default_group(self, consumer, mock_aiokafka_consumer):
        """Test starting consumer with default group ID."""
        await consumer.start()

        # Verify default group ID is used
        call_args = mock_aiokafka_consumer.call_args
        assert call_args[1]["group_id"] == "openclaw-orchestrator"

    @pytest.mark.asyncio
    async def test_stop_consumer(self, consumer, mock_aiokafka_consumer):
        """Test stopping the consumer."""
        await consumer.start()
        await consumer.stop()
        consumer.consumer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_consume_event(self, consumer):
        """Test consuming and processing events."""
        # Mock the consumer with event iteration
        async def mock_handler(event):
            return event

        consumer.on("test.event", mock_handler)

        # Create mock consumer that yields events
        mock_consumer_instance = AsyncMock()
        mock_consumer_instance.start = AsyncMock()
        mock_consumer_instance.stop = AsyncMock()

        # Create mock messages
        mock_msg_1 = AsyncMock()
        mock_msg_1.value = {
            "event_type": "test.event",
            "data": {"key": "value1"}
        }

        mock_msg_2 = AsyncMock()
        mock_msg_2.value = {
            "event_type": "other.event",
            "data": {"key": "value2"}
        }

        async def event_iterator():
            yield mock_msg_1
            yield mock_msg_2

        mock_consumer_instance.__aiter__ = lambda self: event_iterator()

        with patch("kafka_consumer.AIOKafkaConsumer",
                   return_value=mock_consumer_instance):
            await consumer.start()

            # Start consuming (but we'll only process one event for this test)
            consume_task = asyncio.create_task(consumer.consume())

            # Give it time to process the first event
            await asyncio.sleep(0.01)

            # Cancel the consume task
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_consume_unknown_event_type(self, consumer):
        """Test consuming events with unknown event types."""
        # No handlers registered
        mock_consumer_instance = AsyncMock()
        mock_consumer_instance.start = AsyncMock()
        mock_consumer_instance.stop = AsyncMock()

        mock_msg = AsyncMock()
        mock_msg.value = {
            "event_type": "unknown.event",
            "data": {"key": "value"}
        }

        async def event_iterator():
            yield mock_msg

        mock_consumer_instance.__aiter__ = lambda self: event_iterator()

        with patch("kafka_consumer.AIOKafkaConsumer",
                   return_value=mock_consumer_instance):
            await consumer.start()

            # Should not raise an error, just skip the event
            consume_task = asyncio.create_task(consumer.consume())
            await asyncio.sleep(0.01)
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

    def test_multiple_handlers(self, consumer):
        """Test registering multiple handlers."""
        async def handler1(event):
            pass

        async def handler2(event):
            pass

        consumer.on("event.type.1", handler1)
        consumer.on("event.type.2", handler2)

        assert len(consumer.handlers) == 2
        assert consumer.handlers["event.type.1"] == handler1
        assert consumer.handlers["event.type.2"] == handler2
