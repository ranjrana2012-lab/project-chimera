"""
Content Moderator for Safety Filter.

Provides multi-layer content moderation with:
- Pattern matching (via PatternMatcher)
- Context-aware filtering
- Audit logging
"""

import time
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

from pattern_matcher import PatternMatcher
from models import (
    ModerationResult,
    FilterAction,
    FilterLayer,
    ModerationLevel,
    MatchedPattern
)

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Audit log entry for moderation events"""
    timestamp: datetime
    content_hash: str
    content_preview: str
    result: ModerationResult
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "content_hash": self.content_hash,
            "content_preview": self.content_preview,
            "is_safe": self.result.is_safe,
            "action": self.result.action.value,
            "level": self.result.level.value,
            "reason": self.result.reason,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": self.context
        }


class ContentModerator:
    """
    Multi-layer content moderation engine.

    Features:
    - Pattern-based filtering (Layer 1)
    - Context-aware analysis (Layer 2)
    - Rule-based with ML enhancement capability
    - Comprehensive audit logging
    """

    def __init__(
        self,
        policy: str = "family",
        enable_ml_filter: bool = False,
        audit_log_max_size: int = 10000
    ):
        """
        Initialize content moderator.

        Args:
            policy: Default moderation policy
            enable_ml_filter: Enable ML-based filtering (future enhancement)
            audit_log_max_size: Maximum audit log size
        """
        self.policy = policy
        self.enable_ml_filter = enable_ml_filter
        self.audit_log_max_size = audit_log_max_size

        # Initialize pattern matcher
        self.pattern_matcher = PatternMatcher(policy=policy)

        # Audit log
        self.audit_log: List[AuditEntry] = []

        # Statistics
        self._stats = {
            "total_checks": 0,
            "allowed": 0,
            "blocked": 0,
            "flagged": 0,
        }

    def moderate(
        self,
        text: str,
        content_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ModerationResult:
        """
        Perform full moderation with detailed results.

        Args:
            text: Content to moderate
            content_id: Optional content identifier
            user_id: Optional user identifier
            session_id: Optional session identifier
            context: Additional context

        Returns:
            ModerationResult with full details
        """
        start_time = time.time()
        self._stats["total_checks"] += 1

        # Generate content hash for audit
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        # Layer 1: Pattern matching
        is_safe, matched_patterns = self.pattern_matcher.check(text)

        if not is_safe:
            # Content blocked by pattern matching
            result = self._create_block_result(
                matched_patterns,
                content_id,
                start_time
            )
            self._stats["blocked"] += 1
        else:
            # Layer 2: Context-aware analysis
            context_safe, context_reason = self._check_context(text, context)

            if not context_safe:
                result = self._create_flag_result(
                    context_reason,
                    content_id,
                    start_time
                )
                self._stats["flagged"] += 1
            else:
                # Content passed all checks
                result = self._create_safe_result(content_id, start_time)
                self._stats["allowed"] += 1

        # Audit log
        self._add_audit_entry(
            text, content_hash, result, user_id, session_id, context
        )

        return result

    def is_safe(
        self,
        text: str,
        policy: Optional[str] = None
    ) -> bool:
        """
        Quick boolean safety check.

        Args:
            text: Content to check
            policy: Optional policy override

        Returns:
            True if content is safe, False otherwise
        """
        effective_policy = policy or self.policy

        # Use pattern matcher for quick check
        if effective_policy != self.policy:
            matcher = PatternMatcher(policy=effective_policy)
            is_safe, _ = matcher.check(text)
        else:
            is_safe, _ = self.pattern_matcher.check(text)

        return is_safe

    def _check_context(
        self,
        text: str,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check content in context.

        Args:
            text: Content to check
            context: Additional context

        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for repeated patterns (spam)
        if context and context.get("check_spam"):
            words = text.lower().split()
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Flag if any word appears more than 5 times
            for word, count in word_counts.items():
                if count > 5 and len(word) > 3:
                    return False, f"Potential spam: repeated word '{word}'"

        # Check length (very long content might be problematic)
        if len(text) > 10000:
            return False, "Content exceeds maximum length"

        return True, None

    def _create_block_result(
        self,
        matched_patterns: List[MatchedPattern],
        content_id: Optional[str],
        start_time: float
    ) -> ModerationResult:
        """Create a block result"""
        # Get highest severity
        severities = [p.severity for p in matched_patterns]
        highest_severity = max(severities, key=lambda x: x.value)

        processing_time = (time.time() - start_time) * 1000

        return ModerationResult(
            is_safe=False,
            action=FilterAction.BLOCK,
            level=highest_severity,
            confidence=1.0,
            layer=FilterLayer.PATTERN,
            reason=f"Blocked by {len(matched_patterns)} pattern(s)",
            matched_patterns=matched_patterns,
            processing_time_ms=processing_time,
            content_id=content_id
        )

    def _create_flag_result(
        self,
        reason: str,
        content_id: Optional[str],
        start_time: float
    ) -> ModerationResult:
        """Create a flag result"""
        processing_time = (time.time() - start_time) * 1000

        return ModerationResult(
            is_safe=False,
            action=FilterAction.FLAG,
            level=ModerationLevel.MEDIUM,
            confidence=0.75,
            layer=FilterLayer.CONTEXT,
            reason=reason,
            matched_patterns=[],
            processing_time_ms=processing_time,
            content_id=content_id
        )

    def _create_safe_result(
        self,
        content_id: Optional[str],
        start_time: float
    ) -> ModerationResult:
        """Create a safe result"""
        processing_time = (time.time() - start_time) * 1000

        return ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Content passed all safety checks",
            matched_patterns=[],
            processing_time_ms=processing_time,
            content_id=content_id
        )

    def _add_audit_entry(
        self,
        content: str,
        content_hash: str,
        result: ModerationResult,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ):
        """Add entry to audit log"""
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

        # Trim audit log if necessary
        if len(self.audit_log) > self.audit_log_max_size:
            self.audit_log = self.audit_log[-self.audit_log_max_size // 2:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get moderation statistics"""
        total = self._stats["total_checks"]
        return {
            **self._stats,
            "allow_rate": self._stats["allowed"] / total if total > 0 else 0.0,
            "block_rate": self._stats["blocked"] / total if total > 0 else 0.0,
            "flag_rate": self._stats["flagged"] / total if total > 0 else 0.0,
            "current_policy": self.policy,
            "pattern_count": self.pattern_matcher.get_pattern_count(),
        }

    def get_audit_log(
        self,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        entries = self.audit_log

        # Filter by user_id if specified
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        # Get most recent entries
        entries = entries[-limit:]

        return [entry.to_dict() for entry in entries]

    def set_policy(self, policy: str):
        """Change moderation policy"""
        if policy != self.policy:
            self.policy = policy
            self.pattern_matcher = PatternMatcher(policy=policy)
            logger.info(f"Policy changed to: {policy}")
