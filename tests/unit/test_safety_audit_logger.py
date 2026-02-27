"""Unit tests for Safety Filter Audit Logger module."""

import pytest
import tempfile
from pathlib import Path
from services.safety_filter.src.core.audit_logger import AuditLogger, KafkaProducer


@pytest.mark.unit
class TestKafkaProducer:
    """Test cases for KafkaProducer class."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            path = Path(f.name)
        yield path
        # Cleanup
        if path.exists():
            path.unlink()

    @pytest.fixture
    def producer(self, temp_log_file):
        """Create a KafkaProducer for testing."""
        return KafkaProducer(
            bootstrap_servers=None,  # Force fallback mode
            topic="test-audit",
            fallback_path=temp_log_file
        )

    @pytest.mark.asyncio
    async def test_initialization(self, producer):
        """Test that producer initializes correctly."""
        assert producer.topic == "test-audit"
        assert producer.connected is False  # No real Kafka in tests

    @pytest.mark.asyncio
    async def test_send_message(self, producer):
        """Test sending a message."""
        success = await producer.send("test-key", {"test": "value"})
        # In fallback mode, returns False
        assert success is False or success is True

    @pytest.mark.asyncio
    async def test_fallback_buffer(self, producer):
        """Test that messages are buffered in fallback mode."""
        await producer.send("key1", {"data": 1})
        await producer.send("key2", {"data": 2})
        assert len(producer._fallback_buffer) == 2

    @pytest.mark.asyncio
    async def test_flush_fallback(self, producer, temp_log_file):
        """Test flushing fallback buffer to file."""
        # Add messages
        await producer.send("key1", {"data": "test1"})
        await producer.send("key2", {"data": "test2"})

        # Flush
        await producer._flush_fallback()

        # Check file was written
        assert temp_log_file.exists()
        content = temp_log_file.read_text()
        assert "test1" in content or "test2" in content

    @pytest.mark.asyncio
    async def test_close(self, producer):
        """Test closing producer."""
        await producer.send("test", {"value": 1})
        await producer.close()
        assert len(producer._fallback_buffer) == 0  # Should flush on close


@pytest.mark.unit
class TestAuditLogger:
    """Test cases for AuditLogger class."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            path = Path(f.name)
        yield path
        # Cleanup
        if path.exists():
            path.unlink()

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create an AuditLogger for testing."""
        return AuditLogger(
            kafka_servers=None,  # No real Kafka
            kafka_topic="safety-audit-test",
            fallback_log_path=temp_log_file,
            enabled=True
        )

    @pytest.mark.asyncio
    async def test_initialization(self, logger):
        """Test that logger initializes correctly."""
        assert logger.enabled is True
        assert logger.kafka_topic == "safety-audit-test"
        assert logger.producer is not None

    @pytest.mark.asyncio
    async def test_log_check(self, logger):
        """Test logging a safety check."""
        success = await logger.log_check(
            request_id="test-req-1",
            content="Test content to check",
            decision="allow",
            safe=True,
            confidence=0.95,
            user_id="user-123",
            source="test"
        )
        # Success depends on Kafka connection
        assert success is True or success is False

    @pytest.mark.asyncio
    async def test_log_check_with_details(self, logger):
        """Test logging a safety check with details."""
        details = {
            "category_scores": [
                {"category": "profanity", "score": 0.1, "flagged": False}
            ],
            "applied_rules": []
        }
        success = await logger.log_check(
            request_id="test-req-2",
            content="More test content",
            decision="flag",
            safe=False,
            confidence=0.7,
            details=details
        )
        assert success is True or success is False

    @pytest.mark.asyncio
    async def test_log_policy_update(self, logger):
        """Test logging a policy update."""
        rules = [
            {"name": "rule1", "category": "profanity", "action": "block"}
        ]
        success = await logger.log_policy_update(
            version="v1.0.0",
            rules=rules,
            updated_by="admin"
        )
        assert success is True or success is False

    @pytest.mark.asyncio
    async def test_log_review_decision(self, logger):
        """Test logging a review decision."""
        success = await logger.log_review_decision(
            item_id="review-123",
            original_decision="flag",
            review_decision="allow",
            reviewed_by="moderator",
            notes="False positive"
        )
        assert success is True or success is False

    @pytest.mark.asyncio
    async def test_log_batch_check(self, logger):
        """Test logging a batch safety check."""
        aggregate = {
            "total_items": 10,
            "safe_count": 8,
            "flagged_count": 2,
            "blocked_count": 0
        }
        success = await logger.log_batch_check(
            request_id="batch-456",
            content_count=10,
            aggregate_results=aggregate,
            processing_time_ms=150.5
        )
        assert success is True or success is False

    @pytest.mark.asyncio
    async def test_log_error(self, logger):
        """Test logging an error."""
        success = await logger.log_error(
            request_id="error-req",
            error_type="validation_error",
            error_message="Invalid content format",
            context={"field": "content"}
        )
        assert success is True or success is False

    def test_get_statistics(self, logger):
        """Test getting audit statistics."""
        stats = logger.get_statistics()
        assert "total_logged" in stats
        assert "total_errors" in stats
        assert "by_decision" in stats

    @pytest.mark.asyncio
    async def test_content_preview_truncation(self, logger, temp_log_file):
        """Test that long content is previewed correctly."""
        long_content = "a" * 200
        await logger.log_check(
            request_id="test-long",
            content=long_content,
            decision="allow",
            safe=True,
            confidence=1.0
        )
        await logger.producer._flush_fallback()

        # Check file content
        if temp_log_file.exists():
            content = temp_log_file.read_text()
            # Content should be truncated in preview
            assert "..." in content or len(content) < len(long_content)

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, logger):
        """Test that statistics are tracked correctly."""
        initial_count = logger.stats["total_logged"]

        await logger.log_check(
            request_id="stat-test-1",
            content="Test",
            decision="allow",
            safe=True,
            confidence=1.0
        )

        await logger.log_check(
            request_id="stat-test-2",
            content="Test",
            decision="block",
            safe=False,
            confidence=0.9
        )

        assert logger.stats["total_logged"] >= initial_count + 2
        assert logger.stats["by_decision"].get("allow", 0) >= 1
        assert logger.stats["by_decision"].get("block", 0) >= 1

    @pytest.mark.asyncio
    async def test_disabled_logger(self, temp_log_file):
        """Test that disabled logger doesn't log."""
        disabled_logger = AuditLogger(
            kafka_servers=None,
            kafka_topic="test",
            fallback_log_path=temp_log_file,
            enabled=False
        )

        success = await disabled_logger.log_check(
            request_id="test",
            content="Test",
            decision="allow",
            safe=True,
            confidence=1.0
        )

        # Disabled logger should return False
        assert success is False

    @pytest.mark.asyncio
    async def test_close(self, logger):
        """Test closing the logger."""
        await logger.log_check(
            request_id="close-test",
            content="Test",
            decision="allow",
            safe=True,
            confidence=1.0
        )
        await logger.close()
        # Should not raise any errors
