"""Approval workflow handler for Operator Console."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiokafka import AIOKafkaProducer

from src.models.request import ApprovalRequest, ApprovalResponse, ApprovalStatus
from src.models.response import StreamEvent, EventType, EventSeverity

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Handles approval workflows for AI-generated content."""

    def __init__(
        self,
        kafka_brokers: str = "localhost:9092",
        request_topic: str = "chimera.approvals",
        response_topic: str = "chimera.approvals",
        default_expiry_minutes: int = 30,
    ):
        """Initialize approval handler.

        Args:
            kafka_brokers: Kafka broker addresses
            request_topic: Topic for approval requests
            response_topic: Topic for approval responses
            default_expiry_minutes: Default expiry time for requests
        """
        self.kafka_brokers = kafka_brokers
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.default_expiry_minutes = default_expiry_minutes

        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.approval_history: list[ApprovalResponse] = []
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False

    async def start(self) -> None:
        """Start approval handler."""
        logger.info("Starting approval handler")

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        await self.producer.start()
        self.running = True

        # Start expiry checker
        asyncio.create_task(self._check_expired_requests())

        logger.info("Approval handler started")

    async def stop(self) -> None:
        """Stop approval handler."""
        logger.info("Stopping approval handler")
        self.running = False

        if self.producer:
            await self.producer.stop()

        logger.info("Approval handler stopped")

    async def submit_request(self, request: ApprovalRequest) -> str:
        """Submit a new approval request.

        Args:
            request: Approval request to submit

        Returns:
            Request ID
        """
        # Set expiry if not provided
        if not request.expires_at:
            request.expires_at = datetime.now() + timedelta(minutes=self.default_expiry_minutes)

        self.pending_requests[request.request_id] = request

        logger.info(f"Submitted approval request: {request.request_id}")

        # Broadcast to Kafka
        if self.producer:
            await self.producer.send_and_wait(
                self.request_topic,
                value={
                    "event_type": "approval_requested",
                    "request_id": request.request_id,
                    "source_service": request.source_service,
                    "content_type": request.content_type,
                    "priority": request.priority,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        return request.request_id

    async def approve(
        self,
        request_id: str,
        approved_by: str,
        reason: Optional[str] = None,
        modifications: Optional[dict] = None,
    ) -> ApprovalResponse:
        """Approve a request.

        Args:
            request_id: Request to approve
            approved_by: Operator making approval
            reason: Reason for approval
            modifications: Approved modifications

        Returns:
            Approval response
        """
        if request_id not in self.pending_requests:
            raise ValueError(f"Request not found: {request_id}")

        request = self.pending_requests[request_id]

        # Check if expired
        if request.expires_at and datetime.now() > request.expires_at:
            response = ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.EXPIRED,
                reason="Request expired",
                approved_by=approved_by,
            )
        else:
            response = ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.APPROVED,
                reason=reason,
                approved_by=approved_by,
                modifications=modifications,
            )

        self.approval_history.append(response)
        del self.pending_requests[request_id]

        logger.info(f"Approved request: {request_id} by {approved_by}")

        # Broadcast response
        await self._broadcast_response(response, request)

        return response

    async def reject(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> ApprovalResponse:
        """Reject a request.

        Args:
            request_id: Request to reject
            rejected_by: Operator making rejection
            reason: Reason for rejection

        Returns:
            Approval response
        """
        if request_id not in self.pending_requests:
            raise ValueError(f"Request not found: {request_id}")

        request = self.pending_requests[request_id]

        response = ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.REJECTED,
            reason=reason,
            approved_by=rejected_by,
        )

        self.approval_history.append(response)
        del self.pending_requests[request_id]

        logger.info(f"Rejected request: {request_id} by {rejected_by}")

        # Broadcast response
        await self._broadcast_response(response, request)

        return response

    async def _broadcast_response(
        self, response: ApprovalResponse, request: ApprovalRequest
    ) -> None:
        """Broadcast approval response to Kafka.

        Args:
            response: Approval response
            request: Original request
        """
        if not self.producer:
            return

        await self.producer.send_and_wait(
            self.response_topic,
            value={
                "event_type": "approval_decided",
                "request_id": response.request_id,
                "status": response.status.value,
                "approved_by": response.approved_by,
                "reason": response.reason,
                "source_service": request.source_service,
                "content_type": request.content_type,
                "modifications": response.modifications,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _check_expired_requests(self) -> None:
        """Periodically check for expired requests."""
        while self.running:
            try:
                now = datetime.now()
                expired = [
                    rid
                    for rid, req in self.pending_requests.items()
                    if req.expires_at and now > req.expires_at
                ]

                for rid in expired:
                    request = self.pending_requests.pop(rid)
                    logger.warning(f"Request expired: {rid}")

                    # Broadcast expiry
                    if self.producer:
                        await self.producer.send_and_wait(
                            self.response_topic,
                            value={
                                "event_type": "approval_expired",
                                "request_id": rid,
                                "source_service": request.source_service,
                                "timestamp": now.isoformat(),
                            },
                        )

            except Exception as e:
                logger.error(f"Error checking expired requests: {e}")

            await asyncio.sleep(60)  # Check every minute

    def get_pending_requests(self) -> list[ApprovalRequest]:
        """Get all pending approval requests.

        Returns:
            List of pending requests
        """
        return list(self.pending_requests.values())

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific approval request.

        Args:
            request_id: Request ID

        Returns:
            Approval request or None
        """
        return self.pending_requests.get(request_id)

    def get_history(
        self, limit: int = 100, source_service: Optional[str] = None
    ) -> list[ApprovalResponse]:
        """Get approval history.

        Args:
            limit: Maximum results
            source_service: Filter by service

        Returns:
            List of approval responses
        """
        history = self.approval_history

        if source_service:
            request_ids = {
                rid for rid, req in self.pending_requests.items()
                if req.source_service == source_service
            }
            history = [r for r in history if r.request_id in request_ids]

        return history[-limit:]

    def get_stats(self) -> dict:
        """Get approval statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self.approval_history)
        approved = sum(1 for r in self.approval_history if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in self.approval_history if r.status == ApprovalStatus.REJECTED)

        return {
            "pending_count": len(self.pending_requests),
            "total_decisions": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "approval_rate": approved / total if total > 0 else 0,
        }
