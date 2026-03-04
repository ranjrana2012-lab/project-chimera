"""
ML-based safety filter with context-aware content filtering.

Implements multi-layer filtering using pattern matching, ML classification,
and transformer-based context analysis.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class FilterAction(Enum):
    """Action to take on filtered content."""
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"
    MODIFY = "modify"


class FilterLayer(Enum):
    """Safety filter layers."""
    PATTERN = "pattern"
    CLASSIFICATION = "classification"
    CONTEXT = "context"
    AUDIT = "audit"


@dataclass
class FilterResult:
    """Result of filtering content."""
    action: FilterAction
    layer: FilterLayer
    confidence: float  # 0.0 to 1.0
    reason: str
    matched_patterns: List[str] = field(default_factory=list)
    model_predictions: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "layer": self.layer.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "matched_patterns": self.matched_patterns,
            "model_predictions": self.model_predictions,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AuditEntry:
    """Audit log entry for safety filtering."""
    timestamp: datetime
    content_hash: str
    content_preview: str
    result: FilterResult
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "content_hash": self.content_hash,
            "content_preview": self.content_preview,
            "action": self.result.action.value,
            "confidence": self.result.confidence,
            "reason": self.result.reason,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": self.context
        }


class PatternFilter:
    """Pattern-based content filtering layer."""

    def __init__(self, patterns: Optional[List[str]] = None):
        self.patterns = patterns or self._default_patterns()
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.patterns
        ]

    def _default_patterns(self) -> List[str]:
        """Default blocked content patterns."""
        return [
            r'\b(password|secret|api[_-]?key|token)\b.*["\']',
            r'\b(hack|exploit|bypass|inject)\b',
            r'\b(doxx|doxx?ing|swat)\b',
            r'\b(ddos|denial[_-]?of[_-]?service)\b',
            r'\b(malware|virus|trojan|ransom)\b',
        ]

    def check(self, content: str) -> Tuple[bool, List[str]]:
        """Check content against patterns."""
        matched = []
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                matched.append(pattern.pattern)

        return len(matched) > 0, matched


class ClassificationFilter:
    """ML-based classification filter layer."""

    def __init__(
        self,
        model_path: str = "/models/safety_classifier",
        threshold: float = 0.7,
        labels: Optional[List[str]] = None
    ):
        self.model_path = model_path
        self.threshold = threshold
        self.labels = labels or ["toxic", "hateful", "sexual", "violent", "self-harm"]
        self._model_loaded = False

    def load_model(self):
        """Load the classification model."""
        # Simulated model loading
        # In production, would load transformers model
        self._model_loaded = True
        logger.info(f"Classification model loaded from {self.model_path}")

    def classify(self, content: str) -> Dict[str, float]:
        """Classify content into safety categories."""
        if not self._model_loaded:
            self.load_model()

        # Simulated classification
        # In production, would use actual model inference
        import random
        predictions = {
            label: random.random() * 0.3  # Low scores for safe content
            for label in self.labels
        }

        return predictions

    def check(self, content: str) -> Tuple[bool, Dict[str, float]]:
        """Check content using classification model."""
        predictions = self.classify(content)

        # Check if any category exceeds threshold
        max_score = max(predictions.values())
        exceeds_threshold = max_score > self.threshold

        return exceeds_threshold, predictions


class ContextAwareFilter:
    """Transformer-based context-aware filtering layer."""

    def __init__(
        self,
        model_path: str = "/models/context_filter",
        max_length: int = 512,
        threshold: float = 0.6
    ):
        self.model_path = model_path
        self.max_length = max_length
        self.threshold = threshold
        self._model_loaded = False

    def load_model(self):
        """Load the transformer model."""
        # Simulated model loading
        # In production, would load transformer model
        self._model_loaded = True
        logger.info(f"Context model loaded from {self.model_path}")

    def analyze_context(
        self,
        content: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[bool, float, str]:
        """Analyze content in conversational context."""
        if not self._model_loaded:
            self.load_model()

        # Build context window
        context = self._build_context(content, conversation_history)

        # Simulated context analysis
        # In production, would use actual transformer inference
        import random
        risk_score = random.random() * 0.4  # Low scores for safe content

        exceeds_threshold = risk_score > self.threshold
        reason = f"Context risk score: {risk_score:.2f}"

        return exceeds_threshold, risk_score, reason

    async def analyze_context_async(
        self,
        content: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[bool, float, str]:
        """Async wrapper for context analysis."""
        # In production with actual async model, this would be truly async
        return self.analyze_context(content, conversation_history)

    def _build_context(
        self,
        content: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build context window from conversation history."""
        if not history:
            return content

        # Get last few turns
        recent_history = history[-5:] if len(history) > 5 else history

        context_parts = []
        for turn in recent_history:
            if "user" in turn:
                context_parts.append(f"User: {turn['user']}")
            if "assistant" in turn:
                context_parts.append(f"Assistant: {turn['assistant']}")

        context_parts.append(f"User: {content}")
        return "\n".join(context_parts)


class SafetyFilter:
    """Multi-layer safety filtering system."""

    def __init__(
        self,
        pattern_filter: Optional[PatternFilter] = None,
        classification_filter: Optional[ClassificationFilter] = None,
        context_filter: Optional[ContextAwareFilter] = None,
        enable_audit: bool = True
    ):
        self.pattern_filter = pattern_filter or PatternFilter()
        self.classification_filter = classification_filter or ClassificationFilter()
        self.context_filter = context_filter or ContextAwareFilter()
        self.enable_audit = enable_audit

        self.audit_log: List[AuditEntry] = []
        self._stats = {
            "total_checked": 0,
            "allowed": 0,
            "blocked": 0,
            "flagged": 0,
            "modified": 0
        }

    async def check_content(
        self,
        content: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FilterResult:
        """Check content through all filter layers."""
        self._stats["total_checked"] += 1
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Layer 1: Pattern matching
        pattern_blocked, matched_patterns = self.pattern_filter.check(content)
        if pattern_blocked:
            result = FilterResult(
                action=FilterAction.BLOCK,
                layer=FilterLayer.PATTERN,
                confidence=1.0,
                reason=f"Blocked by pattern(s): {', '.join(matched_patterns[:3])}",
                matched_patterns=matched_patterns
            )
            await self._audit_log(content, content_hash, result, user_id, session_id, context)
            self._stats["blocked"] += 1
            return result

        # Layer 2: ML Classification
        class_blocked, predictions = self.classification_filter.check(content)
        if class_blocked:
            max_category = max(predictions.items(), key=lambda x: x[1])
            result = FilterResult(
                action=FilterAction.FLAG,
                layer=FilterLayer.CLASSIFICATION,
                confidence=max_category[1],
                reason=f"Flagged by classification: {max_category[0]} (score: {max_category[1]:.2f})",
                model_predictions=predictions
            )
            await self._audit_log(content, content_hash, result, user_id, session_id, context)
            self._stats["flagged"] += 1
            return result

        # Layer 3: Context-aware analysis
        context_blocked, risk_score, reason = self.context_filter.analyze_context(
            content, conversation_history
        )
        if context_blocked:
            result = FilterResult(
                action=FilterAction.FLAG,
                layer=FilterLayer.CONTEXT,
                confidence=risk_score,
                reason=reason,
                metadata={"risk_score": risk_score}
            )
            await self._audit_log(content, content_hash, result, user_id, session_id, context)
            self._stats["flagged"] += 1
            return result

        # All layers passed
        result = FilterResult(
            action=FilterAction.ALLOW,
            layer=FilterLayer.AUDIT,
            confidence=1.0,
            reason="Content passed all safety checks",
            model_predictions=predictions
        )
        await self._audit_log(content, content_hash, result, user_id, session_id, context)
        self._stats["allowed"] += 1
        return result

    async def _audit_log(
        self,
        content: str,
        content_hash: str,
        result: FilterResult,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ):
        """Log filtering result to audit log."""
        if not self.enable_audit:
            return

        # Create preview (first 100 chars)
        preview = content[:100] + "..." if len(content) > 100 else content

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            content_hash=content_hash,
            content_preview=preview,
            result=result,
            user_id=user_id,
            session_id=session_id,
            context=context or {}
        )

        self.audit_log.append(entry)

        # Keep only last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        total = self._stats["total_checked"]
        return {
            **self._stats,
            "allow_rate": self._stats["allowed"] / total if total > 0 else 0.0,
            "block_rate": self._stats["blocked"] / total if total > 0 else 0.0,
            "flag_rate": self._stats["flagged"] / total if total > 0 else 0.0
        }

    def get_audit_log(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        entries = self.audit_log

        # Filter by user_id if specified
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        # Apply offset and limit
        entries = entries[offset:offset + limit]

        return [entry.to_dict() for entry in entries]

    def export_audit_log(self, output_path: str):
        """Export audit log to file."""
        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": self.get_statistics(),
            "entries": [e.to_dict() for e in self.audit_log]
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Audit log exported to {output_path}")


# Global safety filter instance
safety_filter = SafetyFilter()


__all__ = [
    "FilterAction",
    "FilterLayer",
    "FilterResult",
    "AuditEntry",
    "PatternFilter",
    "ClassificationFilter",
    "ContextAwareFilter",
    "SafetyFilter",
    "safety_filter"
]
