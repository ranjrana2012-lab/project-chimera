"""Unit tests for Operator Console core modules."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.operator_console.src.core.event_aggregator import EventAggregator
from services.operator_console.src.core.approval_handler import ApprovalHandler, ApprovalStatus
from services.operator_console.src.core.override_manager import OverrideManager, OverrideType
from services.operator_console.src.models.request import ApprovalRequest, OverrideRequest


@pytest.fixture
def mock_kafka_message():
    """Create a mock Kafka message."""
    msg = MagicMock()
    msg.topic = "chimera.events"
    msg.offset = 123
    msg.value = '{"event_type": "script_generated", "source_service": "script-agent", "title": "Script Generated", "message": "Test event", "severity": "info"}'
    return msg


class TestEventAggregator:
    """Tests for EventAggregator."""

    @pytest.mark.asyncio
    async def test_event_aggregator_initialization(self):
        """Test event aggregator initialization."""
        aggregator = EventAggregator(
            kafka_brokers="localhost:9092",
            topics=["test.topic"],
            max_events=100,
        )
        assert aggregator.kafka_brokers == "localhost:9092"
        assert aggregator.topics == ["test.topic"]
        assert aggregator.max_events == 100
        assert len(aggregator.events) == 0
        assert aggregator.running is False

    @pytest.mark.asyncio
    async def test_event_aggregator_subscribe(self):
        """Test subscribing to event stream."""
        aggregator = EventAggregator(
            kafka_brokers="localhost:9092",
            topics=["test.topic"],
        )
        queue = aggregator.subscribe()
        assert queue in aggregator._subscribers

        aggregator.unsubscribe(queue)
        assert queue not in aggregator._subscribers

    @pytest.mark.asyncio
    async def test_get_recent_events(self):
        """Test getting recent events."""
        aggregator = EventAggregator(
            kafka_brokers="localhost:9092",
            topics=["test.topic"],
        )

        from services.operator_console.src.models.response import EventType, EventSeverity, StreamEvent

        # Add some test events
        for i in range(10):
            event = StreamEvent(
                event_id=f"event-{i}",
                event_type=EventType.INFO,
                source_service="test",
                title=f"Event {i}",
                message=f"Message {i}",
            )
            aggregator.events.append(event)

        recent = aggregator.get_recent_events(limit=5)
        assert len(recent) == 5

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting aggregator statistics."""
        aggregator = EventAggregator(
            kafka_brokers="localhost:9092",
            topics=["test.topic"],
        )

        from services.operator_console.src.models.response import EventType, EventSeverity, StreamEvent

        # Add test events
        event = StreamEvent(
            event_id="test-1",
            event_type=EventType.SCRIPT_GENERATED,
            severity=EventSeverity.ERROR,
            source_service="script-agent",
            title="Test",
            message="Test",
        )
        aggregator.events.append(event)

        stats = aggregator.get_stats()
        assert stats["total_events"] == 1
        assert "events_by_type" in stats
        assert "events_by_severity" in stats


class TestApprovalHandler:
    """Tests for ApprovalHandler."""

    @pytest.mark.asyncio
    async def test_approval_handler_initialization(self):
        """Test approval handler initialization."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
            request_topic="approvals",
            response_topic="approvals",
        )
        assert handler.kafka_brokers == "localhost:9092"
        assert len(handler.pending_requests) == 0
        assert handler.running is False

    @pytest.mark.asyncio
    async def test_submit_approval_request(self):
        """Test submitting an approval request."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        handler.producer = AsyncMock()
        handler.producer.send_and_wait = AsyncMock()

        request = ApprovalRequest(
            request_id="test-approval-1",
            source_service="script-agent",
            content_type="script",
            content_preview="Test script content",
        )

        request_id = await handler.submit_request(request)
        assert request_id == "test-approval-1"
        assert request_id in handler.pending_requests

    @pytest.mark.asyncio
    async def test_approve_request(self):
        """Test approving a request."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        handler.producer = AsyncMock()
        handler.producer.send_and_wait = AsyncMock()

        # Create a pending request
        request = ApprovalRequest(
            request_id="test-approval-2",
            source_service="lighting-agent",
            content_type="lighting_cue",
            content_preview="Test lighting",
        )
        handler.pending_requests["test-approval-2"] = request

        response = await handler.approve(
            request_id="test-approval-2",
            approved_by="operator",
            reason="Approved",
        )

        assert response.status == ApprovalStatus.APPROVED
        assert "test-approval-2" not in handler.pending_requests
        assert len(handler.approval_history) == 1

    @pytest.mark.asyncio
    async def test_reject_request(self):
        """Test rejecting a request."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        handler.producer = AsyncMock()
        handler.producer.send_and_wait = AsyncMock()

        # Create a pending request
        request = ApprovalRequest(
            request_id="test-approval-3",
            source_service="audio-agent",
            content_type="audio_cue",
            content_preview="Test audio",
        )
        handler.pending_requests["test-approval-3"] = request

        response = await handler.reject(
            request_id="test-approval-3",
            rejected_by="operator",
            reason="Not appropriate",
        )

        assert response.status == ApprovalStatus.REJECTED
        assert response.reason == "Not appropriate"
        assert "test-approval-3" not in handler.pending_requests

    @pytest.mark.asyncio
    async def test_get_pending_requests(self):
        """Test getting pending requests."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
        )

        # Add pending requests
        for i in range(3):
            request = ApprovalRequest(
                request_id=f"approval-{i}",
                source_service="test-service",
                content_type="test",
                content_preview=f"Content {i}",
            )
            handler.pending_requests[f"approval-{i}"] = request

        pending = handler.get_pending_requests()
        assert len(pending) == 3

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting approval statistics."""
        handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
        )

        # Add some history
        from services.operator_console.src.models.request import ApprovalResponse

        handler.approval_history = [
            ApprovalResponse(
                request_id="1",
                status=ApprovalStatus.APPROVED,
                approved_by="operator",
            ),
            ApprovalResponse(
                request_id="2",
                status=ApprovalStatus.REJECTED,
                approved_by="operator",
                reason="Rejected",
            ),
        ]

        stats = handler.get_stats()
        assert stats["pending_count"] == 0
        assert stats["total_decisions"] == 2
        assert stats["approved_count"] == 1
        assert stats["rejected_count"] == 1


class TestOverrideManager:
    """Tests for OverrideManager."""

    @pytest.mark.asyncio
    async def test_override_manager_initialization(self):
        """Test override manager initialization."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )
        assert manager.kafka_brokers == "localhost:9092"
        assert len(manager.active_overrides) == 0
        assert manager.running is False

    @pytest.mark.asyncio
    async def test_trigger_override(self):
        """Test triggering an override."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        request = OverrideRequest(
            override_type=OverrideType.SERVICE_PAUSE,
            target_service="script-agent",
            reason="Testing override",
        )

        override_id = await manager.trigger_override(request, "operator")
        assert override_id.startswith("override_")
        assert override_id in manager.active_overrides

    @pytest.mark.asyncio
    async def test_release_override(self):
        """Test releasing an override."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        # Create an active override
        request = OverrideRequest(
            override_type=OverrideType.SERVICE_PAUSE,
            target_service="script-agent",
            reason="Testing",
        )
        override_id = await manager.trigger_override(request, "operator")

        # Release it
        success = await manager.release_override(override_id, "operator")
        assert success is True
        assert override_id not in manager.active_overrides
        assert len(manager.override_history) == 1

    @pytest.mark.asyncio
    async def test_emergency_stop_all(self):
        """Test emergency stop on all services."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        override_id = await manager.emergency_stop_all("operator", "Emergency test")
        assert override_id.startswith("override_")
        assert override_id in manager.active_overrides

        override = manager.active_overrides[override_id]
        assert override.request.target_service == "all"
        assert override.request.override_type == OverrideType.EMERGENCY_STOP

    @pytest.mark.asyncio
    async def test_get_active_overrides(self):
        """Test getting active overrides."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        # Add some overrides
        for i in range(2):
            request = OverrideRequest(
                override_type=OverrideType.SERVICE_PAUSE,
                target_service=f"service-{i}",
                reason=f"Reason {i}",
            )
            await manager.trigger_override(request, "operator")

        active = manager.get_active_overrides()
        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_get_overrides_for_service(self):
        """Test getting overrides for a specific service."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        # Add overrides for different services
        request1 = OverrideRequest(
            override_type=OverrideType.SERVICE_PAUSE,
            target_service="script-agent",
            reason="Test 1",
        )
        await manager.trigger_override(request1, "operator")

        request2 = OverrideRequest(
            override_type=OverrideType.SERVICE_PAUSE,
            target_service="audio-agent",
            reason="Test 2",
        )
        await manager.trigger_override(request2, "operator")

        script_overrides = manager.get_overrides_for_service("script-agent")
        assert len(script_overrides) == 1
        assert script_overrides[0]["target_service"] == "script-agent"

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting override statistics."""
        manager = OverrideManager(
            kafka_brokers="localhost:9092",
        )

        # Mock the producer
        manager.producer = AsyncMock()
        manager.producer.send_and_wait = AsyncMock()

        # Add some overrides
        for i in range(3):
            request = OverrideRequest(
                override_type=OverrideType.SERVICE_PAUSE,
                target_service=f"service-{i}",
                reason="Test",
            )
            await manager.trigger_override(request, "operator")

        stats = manager.get_stats()
        assert stats["active_count"] == 3
        assert stats["total_history"] == 0

        # Release one to add to history
        override_id = list(manager.active_overrides.keys())[0]
        await manager.release_override(override_id, "operator")

        stats = manager.get_stats()
        assert stats["active_count"] == 2
        assert stats["total_history"] == 1
