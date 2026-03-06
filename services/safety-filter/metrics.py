"""
Business metrics for Safety Filter.

Provides Prometheus metrics for content moderation tracking.
"""

from prometheus_client import Gauge, Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Moderation outcomes
moderation_checks = Counter(
    'safety_moderation_checks_total',
    'Total content moderation checks',
    ['policy', 'result']  # result: allow, block, flag
)

# Content safety score
safety_score = Gauge(
    'safety_content_safety_score',
    'Content safety score (0-1)',
    ['policy']
)

# Pattern matches
pattern_matches = Counter(
    'safety_pattern_matches_total',
    'Total pattern matches',
    ['pattern_type', 'severity']
)

# Moderation duration
moderation_duration = Histogram(
    'safety_moderation_duration_seconds',
    'Time spent moderating content',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Content length
content_length = Histogram(
    'safety_content_length_chars',
    'Length of moderated content in characters',
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

# Blocklist size
blocklist_size = Gauge(
    'safety_blocklist_patterns_total',
    'Number of patterns in blocklists',
    ['policy']
)

# Audit log size
audit_log_size = Gauge(
    'safety_audit_log_entries_total',
    'Current number of audit log entries'
)


def record_moderation(
    policy: str,
    is_safe: bool,
    action: str,
    content_length_chars: int,
    duration: float,
    pattern_match_count: int = 0,
    confidence: float = 1.0
) -> None:
    """
    Record a moderation event.

    Args:
        policy: Moderation policy used
        is_safe: Whether content was deemed safe
        action: Action taken (allow, block, flag)
        content_length_chars: Length of content in characters
        duration: Time taken for moderation in seconds
        pattern_match_count: Number of pattern matches
        confidence: Confidence score (0-1)
    """
    try:
        # Record check result
        result = "allow" if is_safe else action
        moderation_checks.labels(policy=policy, result=result).inc()

        # Record duration
        moderation_duration.observe(duration)

        # Record content length
        content_length.observe(content_length_chars)

        # Record safety score
        safety_score.labels(policy=policy).set(confidence if is_safe else 1.0 - confidence)

        logger.debug(
            f"Recorded moderation: policy={policy}, is_safe={is_safe}, "
            f"action={action}, duration={duration:.3f}s"
        )
    except Exception as e:
        logger.error(f"Failed to record moderation metrics: {e}")


def record_pattern_match(pattern_type: str, severity: str) -> None:
    """
    Record a pattern match event.

    Args:
        pattern_type: Type of pattern matched
        severity: Severity level of the pattern
    """
    try:
        pattern_matches.labels(
            pattern_type=pattern_type,
            severity=severity
        ).inc()
    except Exception as e:
        logger.error(f"Failed to record pattern match metrics: {e}")


def update_blocklist_size(policy: str, size: int) -> None:
    """
    Update blocklist size metric.

    Args:
        policy: Moderation policy name
        size: Number of patterns in blocklist
    """
    try:
        blocklist_size.labels(policy=policy).set(size)
    except Exception as e:
        logger.error(f"Failed to update blocklist size metric: {e}")


def update_audit_log_size(size: int) -> None:
    """
    Update audit log size metric.

    Args:
        size: Current number of audit log entries
    """
    try:
        audit_log_size.set(size)
    except Exception as e:
        logger.error(f"Failed to update audit log size metric: {e}")


__all__ = [
    "moderation_checks",
    "safety_score",
    "pattern_matches",
    "moderation_duration",
    "content_length",
    "blocklist_size",
    "audit_log_size",
    "record_moderation",
    "record_pattern_match",
    "update_blocklist_size",
    "update_audit_log_size",
]
