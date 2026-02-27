"""Audit logging for safety filter.

This module provides Kafka-based audit logging for all safety checks,
including content, decisions, and metadata for compliance and analysis.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio


class KafkaProducer:
    """Mock Kafka producer for audit logging.

    In production, this would use aiokafka or confluent-kafka.
    For now, it provides a file-based fallback.
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: str = "safety-audit",
        fallback_path: Optional[Path] = None
    ):
        """Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic to publish to
            fallback_path: Fallback file path if Kafka unavailable
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.fallback_path = fallback_path
        self.connected = False
        self._fallback_buffer: List[Dict[str, Any]] = []

        # Try to connect to Kafka
        if bootstrap_servers:
            try:
                # In production, initialize real Kafka producer here
                # from aiokafka import AIOKafkaProducer
                # self.producer = AIOKafkaProducer(
                #     bootstrap_servers=bootstrap_servers,
                #     value_serializer=lambda v: json.dumps(v).encode()
                # )
                # await self.producer.start()
                self.connected = True
            except Exception as e:
                print(f"Warning: Could not connect to Kafka: {e}")
                self.connected = False

    async def send(self, key: str, value: Dict[str, Any]) -> bool:
        """Send a message to Kafka.

        Args:
            key: Message key
            value: Message value dictionary

        Returns:
            True if sent successfully
        """
        if self.connected:
            try:
                # In production, use real Kafka send
                # await self.producer.send_and_wait(self.topic, key=key.encode(), value=value)
                return True
            except Exception as e:
                print(f"Error sending to Kafka: {e}")

        # Fallback to buffer
        self._fallback_buffer.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })

        # Flush buffer if it gets too large
        if len(self._fallback_buffer) > 100:
            await self._flush_fallback()

        return False

    async def _flush_fallback(self):
        """Flush fallback buffer to file."""
        if not self.fallback_path or not self._fallback_buffer:
            return

        try:
            with open(self.fallback_path, 'a') as f:
                for entry in self._fallback_buffer:
                    f.write(json.dumps(entry) + '\n')
            self._fallback_buffer.clear()
        except Exception as e:
            print(f"Error writing fallback log: {e}")

    async def close(self):
        """Close the producer."""
        # Flush any remaining fallback buffer
        await self._flush_fallback()

        if self.connected:
            # In production, close real Kafka producer
            # await self.producer.stop()
            pass


class AuditLogger:
    """Audit logger for safety filter operations.

    Logs all safety checks, decisions, and related metadata to Kafka
    for compliance, monitoring, and analysis.
    """

    def __init__(
        self,
        kafka_servers: Optional[str] = None,
        kafka_topic: str = "safety-audit",
        fallback_log_path: Optional[Path] = None,
        enabled: bool = True
    ):
        """Initialize audit logger.

        Args:
            kafka_servers: Kafka bootstrap servers
            kafka_topic: Topic for audit logs
            fallback_log_path: Fallback file path
            enabled: Whether audit logging is enabled
        """
        self.enabled = enabled
        self.kafka_topic = kafka_topic
        self.fallback_log_path = fallback_log_path

        # Initialize producer
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            topic=kafka_topic,
            fallback_path=fallback_log_path
        )

        # Statistics
        self.stats = {
            "total_logged": 0,
            "total_errors": 0,
            "by_decision": {},
            "by_category": {}
        }

    async def log_check(
        self,
        request_id: str,
        content: str,
        decision: str,
        safe: bool,
        confidence: float,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        source: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> bool:
        """Log a safety check result.

        Args:
            request_id: Request identifier
            content: Content that was checked
            decision: Safety decision (allow/block/flag/warn)
            safe: Whether content was deemed safe
            confidence: Decision confidence
            details: Optional detailed results
            user_id: Optional user identifier
            source: Optional content source
            processing_time_ms: Optional processing time

        Returns:
            True if logged successfully
        """
        if not self.enabled:
            return False

        # Build audit entry
        entry = {
            "event_type": "safety_check",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "content_length": len(content),
            "decision": decision,
            "safe": safe,
            "confidence": confidence,
            "user_id": user_id,
            "source": source,
            "processing_time_ms": processing_time_ms
        }

        # Add details if provided
        if details:
            # Add category scores
            if "category_scores" in details:
                entry["category_scores"] = details["category_scores"]

            # Add flagged content (truncated)
            if "flagged_content" in details:
                entry["flagged_content_count"] = len(details["flagged_content"])

            # Add applied rules
            if "applied_rules" in details:
                entry["applied_rules"] = details["applied_rules"]

        # Update statistics
        self.stats["total_logged"] += 1
        self.stats["by_decision"][decision] = self.stats["by_decision"].get(decision, 0) + 1

        # Send to Kafka
        success = await self.producer.send(
            key=request_id,
            value=entry
        )

        if not success:
            self.stats["total_errors"] += 1

        return success

    async def log_policy_update(
        self,
        version: str,
        rules: List[Dict[str, Any]],
        updated_by: Optional[str] = None
    ) -> bool:
        """Log a policy update.

        Args:
            version: New policy version
            rules: Updated rules
            updated_by: User who made the update

        Returns:
            True if logged successfully
        """
        if not self.enabled:
            return False

        entry = {
            "event_type": "policy_update",
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "rule_count": len(rules),
            "rules": rules,
            "updated_by": updated_by
        }

        return await self.producer.send(
            key=f"policy-{version}",
            value=entry
        )

    async def log_review_decision(
        self,
        item_id: str,
        original_decision: str,
        review_decision: str,
        reviewed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Log a review decision.

        Args:
            item_id: Item being reviewed
            original_decision: Original automated decision
            review_decision: Human reviewer's decision
            reviewed_by: Reviewer identifier
            notes: Optional review notes

        Returns:
            True if logged successfully
        """
        if not self.enabled:
            return False

        entry = {
            "event_type": "review_decision",
            "timestamp": datetime.now().isoformat(),
            "item_id": item_id,
            "original_decision": original_decision,
            "review_decision": review_decision,
            "reviewed_by": reviewed_by,
            "notes": notes
        }

        return await self.producer.send(
            key=f"review-{item_id}",
            value=entry
        )

    async def log_batch_check(
        self,
        request_id: str,
        content_count: int,
        aggregate_results: Dict[str, Any],
        processing_time_ms: float,
        user_id: Optional[str] = None
    ) -> bool:
        """Log a batch safety check.

        Args:
            request_id: Request identifier
            content_count: Number of items checked
            aggregate_results: Aggregated results
            processing_time_ms: Total processing time
            user_id: Optional user identifier

        Returns:
            True if logged successfully
        """
        if not self.enabled:
            return False

        entry = {
            "event_type": "batch_safety_check",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "content_count": content_count,
            "aggregate_results": aggregate_results,
            "processing_time_ms": processing_time_ms,
            "user_id": user_id
        }

        return await self.producer.send(
            key=request_id,
            value=entry
        )

    async def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log an error.

        Args:
            request_id: Request identifier
            error_type: Type of error
            error_message: Error message
            context: Optional error context

        Returns:
            True if logged successfully
        """
        if not self.enabled:
            return False

        entry = {
            "event_type": "error",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }

        return await self.producer.send(
            key=f"error-{request_id}",
            value=entry
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self.stats,
            "kafka_connected": self.producer.connected,
            "fallback_buffer_size": len(self.producer._fallback_buffer),
            "uptime_seconds": getattr(self, '_start_time', time.time())
        }

    async def search_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        decision: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search audit logs (for fallback file only).

        Args:
            start_time: Start time filter
            end_time: End time filter
            decision: Decision filter
            user_id: User ID filter
            limit: Maximum results

        Returns:
            List of matching log entries
        """
        if not self.fallback_log_path or not self.fallback_log_path.exists():
            return []

        results = []
        try:
            with open(self.fallback_log_path, 'r') as f:
                for line in f:
                    if len(results) >= limit:
                        break

                    try:
                        entry = json.loads(line.strip())
                        value = entry.get("value", {})

                        # Apply filters
                        if start_time:
                            entry_time = datetime.fromisoformat(value.get("timestamp", ""))
                            if entry_time < start_time:
                                continue

                        if end_time:
                            entry_time = datetime.fromisoformat(value.get("timestamp", ""))
                            if entry_time > end_time:
                                continue

                        if decision and value.get("decision") != decision:
                            continue

                        if user_id and value.get("user_id") != user_id:
                            continue

                        results.append(value)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error searching logs: {e}")

        return results

    async def export_logs(
        self,
        output_path: Path,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Export audit logs to a file.

        Args:
            output_path: Output file path
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Number of entries exported
        """
        logs = await self.search_logs(
            start_time=start_time,
            end_time=end_time,
            limit=1000000
        )

        with open(output_path, 'w') as f:
            json.dump(logs, f, indent=2)

        return len(logs)

    async def close(self):
        """Close the audit logger."""
        await self.producer.close()
