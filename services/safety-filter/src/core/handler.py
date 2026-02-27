"""Core handler for Safety Filter service.

This handler coordinates all safety filtering components including
word filter, ML filter, policy engine, and audit logging.
"""

import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from .word_filter import WordFilter
from .ml_filter import MLFilter
from .policy_engine import PolicyEngine, StrictnessLevel
from .audit_logger import AuditLogger
from ..models.request import SafetyCheckRequest, SafetyBatchRequest
from ..models.response import SafetyCheckResponse, SafetyBatchResponse, SafetyDecision


class SafetyHandler:
    """Main handler for safety filtering operations.

    Coordinates all filtering components and provides unified API
    for content safety checks.
    """

    def __init__(self, settings):
        """Initialize the safety handler.

        Args:
            settings: Service configuration settings
        """
        self.settings = settings

        # Initialize components
        self.word_filter = WordFilter(
            word_list_path=getattr(settings, 'word_list_path', None),
            custom_patterns=getattr(settings, 'custom_patterns', None)
        )

        self.ml_filter = MLFilter(
            model_path=getattr(settings, 'ml_model_path', None),
            device=getattr(settings, 'device', None)
        )

        self.policy_engine = PolicyEngine(
            policy_path=getattr(settings, 'policy_path', None),
            default_action=getattr(settings, 'default_action', 'flag'),
            default_strictness=StrictnessLevel.MODERATE
        )

        self.audit_logger = AuditLogger(
            kafka_servers=getattr(settings, 'kafka_servers', None),
            kafka_topic=getattr(settings, 'kafka_topic', 'safety-audit'),
            fallback_log_path=getattr(settings, 'audit_log_path', None),
            enabled=getattr(settings, 'audit_enabled', True)
        )

        # Model version info
        self.model_version = "safety-filter-v0.1.0"

        # Start time for uptime tracking
        self._start_time = time.time()

    async def initialize(self):
        """Initialize all components.

        Loads models, word lists, and policies.
        """
        print("Initializing Safety Filter handler...")

        # Load ML model
        await self.ml_filter.load_model()
        print(f"ML filter model loaded: {self.ml_filter.model_loaded}")

        # Word filter is initialized in constructor
        print(f"Word filter initialized with {len(self.word_filter.word_lists)} categories")

        # Policy engine loads policies in constructor
        print(f"Policy engine initialized with {len(self.policy_engine.rules)} rules")

        # Audit logger initializes in constructor
        print(f"Audit logger initialized (enabled: {self.audit_logger.enabled})")

        print("Safety Filter handler initialization complete")

    async def check_content(
        self,
        request: SafetyCheckRequest
    ) -> SafetyCheckResponse:
        """Perform a safety check on content.

        Args:
            request: Safety check request

        Returns:
            Safety check response
        """
        start_time = time.time()

        # Generate request ID if not provided
        request_id = request.request_id or str(uuid.uuid4())

        try:
            # Extract options
            options = request.options or {}
            strictness = StrictnessLevel(options.strictness) if options.strictness else StrictnessLevel.MODERATE
            categories = [c.value for c in options.categories] if options.categories else None

            # Run word filter
            word_results = await self.word_filter.check(
                request.content,
                categories=categories
            )

            # Run ML filter
            ml_results = await self.ml_filter.classify(
                request.content,
                include_details=options.include_details
            )

            # Evaluate with policy engine
            policy_results = self.policy_engine.evaluate(
                request.content,
                word_results,
                ml_results,
                strictness=strictness,
                categories=categories
            )

            # Build flagged content if requested
            flagged_content = None
            if options.include_flagged_content and not policy_results["safe"]:
                flagged_content = self._build_flagged_content(
                    request.content,
                    word_results,
                    ml_results
                )

            # Build details
            details = None
            if options.include_details:
                details = {
                    "word_filter_results": word_results,
                    "ml_filter_results": ml_results,
                    "category_scores": policy_results["category_scores"],
                    "overall_confidence": policy_results["confidence"],
                    "applied_rules": policy_results["applied_rules"]
                }

            # Build response
            response = SafetyCheckResponse(
                request_id=request_id,
                decision=SafetyDecision(policy_results["decision"]),
                safe=policy_results["safe"],
                confidence=policy_results["confidence"],
                details=details,
                flagged_content=flagged_content,
                processing_time_ms=(time.time() - start_time) * 1000,
                model_version=self.model_version,
                explanation=policy_results["explanation"]
            )

            # Log to audit
            await self.audit_logger.log_check(
                request_id=request_id,
                content=request.content,
                decision=policy_results["decision"],
                safe=policy_results["safe"],
                confidence=policy_results["confidence"],
                details=details,
                user_id=request.user_id,
                source=request.source,
                processing_time_ms=response.processing_time_ms
            )

            return response

        except Exception as e:
            # Log error
            await self.audit_logger.log_error(
                request_id=request_id,
                error_type="safety_check_error",
                error_message=str(e)
            )

            # Return error response
            raise

    async def check_batch(
        self,
        request: SafetyBatchRequest
    ) -> SafetyBatchResponse:
        """Perform safety checks on multiple contents.

        Args:
            request: Batch safety check request

        Returns:
            Batch safety check response
        """
        start_time = time.time()

        # Generate request ID if not provided
        request_id = request.request_id or str(uuid.uuid4())

        # Check each content
        results = []
        safe_count = 0
        flagged_count = 0
        blocked_count = 0
        total_confidence = 0.0

        for i, content in enumerate(request.contents):
            # Create individual request
            individual_request = SafetyCheckRequest(
                content=content,
                options=request.options,
                request_id=f"{request_id}-{i}",
                user_id=None,
                source=None
            )

            # Check content
            result = await self.check_content(individual_request)
            results.append(result)

            # Update aggregates
            if result.safe:
                safe_count += 1
            elif result.decision == SafetyDecision.BLOCK:
                blocked_count += 1
            else:
                flagged_count += 1

            total_confidence += result.confidence

        # Build aggregate stats
        aggregate = {
            "total_items": len(request.contents),
            "safe_count": safe_count,
            "flagged_count": flagged_count,
            "blocked_count": blocked_count,
            "average_confidence": total_confidence / len(request.contents) if request.contents else 0.0
        }

        # Build response
        response = SafetyBatchResponse(
            request_id=request_id,
            results=results,
            aggregate=aggregate,
            total_processing_time_ms=(time.time() - start_time) * 1000,
            model_version=self.model_version
        )

        # Log batch check
        await self.audit_logger.log_batch_check(
            request_id=request_id,
            content_count=len(request.contents),
            aggregate_results=aggregate,
            processing_time_ms=response.total_processing_time_ms
        )

        return response

    def _build_flagged_content(
        self,
        content: str,
        word_results: Dict[str, Any],
        ml_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build flagged content details.

        Args:
            content: Original content
            word_results: Word filter results
            ml_results: ML filter results

        Returns:
            List of flagged content items
        """
        flagged = []

        # Add word filter matches
        for match in word_results.get("matches", []):
            text = match.get("text", "")
            pos = match.get("position", 0)

            flagged.append({
                "category": match.get("category", "unknown"),
                "text": text,
                "start_pos": pos,
                "end_pos": pos + len(text),
                "reason": f"Matched {match.get('category', 'unknown')} pattern",
                "severity": word_results.get("highest_severity", "medium")
            })

        # Add ML-based flagging (if high confidence)
        if ml_results.get("harm_probability", 0) > 0.7:
            top_category = ml_results.get("top_category")
            if top_category:
                flagged.append({
                    "category": top_category,
                    "text": content[:50] + "..." if len(content) > 50 else content,
                    "start_pos": 0,
                    "end_pos": min(50, len(content)),
                    "reason": f"ML detected {top_category} (confidence: {ml_results.get('confidence', 0):.2f})",
                    "severity": "high"
                })

        return flagged

    def get_policies(self) -> Dict[str, Any]:
        """Get current policies.

        Returns:
            Policy information
        """
        return self.policy_engine.get_policies()

    def update_policies(
        self,
        rules: List[Dict[str, Any]],
        default_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update policies.

        Args:
            rules: List of rule dictionaries
            default_action: New default action

        Returns:
            Updated policy information
        """
        self.policy_engine.update_policies(rules, default_action)

        # Log policy update
        version = f"v{int(time.time())}"
        # Note: This is async but we're in sync context
        # In production, handle this properly
        # asyncio.create_task(self.audit_logger.log_policy_update(version, rules))

        return self.policy_engine.get_policies()

    async def filter_content(
        self,
        content: str,
        filter_char: str = "*",
        categories: Optional[List[str]] = None
    ) -> str:
        """Filter content by replacing flagged words.

        Args:
            content: Content to filter
            filter_char: Character to replace with
            categories: Categories to filter

        Returns:
            Filtered content
        """
        return await self.word_filter.filter_content(
            content,
            filter_char=filter_char,
            categories=categories
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components.

        Returns:
            Health status dictionary
        """
        uptime = time.time() - self._start_time

        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "components": {
                "word_filter": {
                    "loaded": True,
                    "categories": len(self.word_filter.word_lists)
                },
                "ml_filter": {
                    "loaded": self.ml_filter.model_loaded,
                    "model_version": self.ml_filter.model_version
                },
                "policy_engine": {
                    "loaded": True,
                    "rules": len(self.policy_engine.rules)
                },
                "audit_logger": {
                    "enabled": self.audit_logger.enabled,
                    "kafka_connected": self.audit_logger.producer.connected
                }
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get operational statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "uptime_seconds": time.time() - self._start_time,
            "audit_stats": self.audit_logger.get_statistics()
        }

    async def close(self):
        """Close all components and cleanup."""
        print("Closing Safety Filter handler...")

        await self.ml_filter.close()
        await self.audit_logger.close()

        print("Safety Filter handler closed")
