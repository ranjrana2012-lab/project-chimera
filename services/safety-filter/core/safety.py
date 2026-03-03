"""
Safety Filter Agent - Multi-Layer Content Filtering Module

Implements comprehensive content safety filtering for theatre performances:
- Word-based filtering (block lists)
- ML-based contextual filtering
- Policy template system
- Audit logging for all filtered content
"""

import re
import time
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum
from datetime import datetime

from prometheus_client import Counter, Histogram


# Configure logging
logger = logging.getLogger(__name__)


# Metrics
content_checks = Counter(
    'safety_content_checks_total',
    'Total content safety checks',
    ['policy', 'result']
)
filter_accuracy = Histogram(
    'safety_filter_accuracy',
    'Content filter accuracy scores'
)


class ContentSeverity(Enum):
    """Severity levels for filtered content."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FilterLayer(Enum):
    """Different filtering layers."""
    WORD_BASED = "word_based"
    ML_BASED = "ml_based"
    CONTEXTUAL = "contextual"


@dataclass
class FilterResult:
    """Result from content filtering."""
    is_safe: bool
    severity: ContentSeverity
    matched_terms: List[str]
    layer: FilterLayer
    confidence: float
    policy_violated: Optional[str]
    reasoning: str
    processing_time_ms: float


@dataclass
class PolicyTemplate:
    """Policy template for content filtering."""
    name: str
    description: str
    word_blocklist: Set[str]
    phrase_blocklist: Set[str]
    severity_threshold: ContentSeverity
    require_ml_confirmation: bool = False
    custom_rules: Dict = None

    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = {}


# Predefined policy templates
POLICY_TEMPLATES: Dict[str, PolicyTemplate] = {
    "family": PolicyTemplate(
        name="family",
        description="Family-friendly filtering (all ages)",
        word_blocklist={
            # Profanity
            "damn", "hell", "shit",
            # Inappropriate content
            "kill", "murder", "death", "violence",
            # Adult themes
            "sex", "drug", "alcohol"
        },
        phrase_blocklist={
            "what the hell", "what the fuck",
            "son of a bitch", "middle finger",
            "drug use", "sexual content"
        },
        severity_threshold=ContentSeverity.LOW,
        require_ml_confirmation=False
    ),

    "teen": PolicyTemplate(
        name="teen",
        description="Teen filtering (13+)",
        word_blocklist={
            # Strong profanity
            "fuck", "shit", "damn", "hell",
            # Mild violence
            "kill", "death", "murder",
            # Adult themes
            "sex", "drug"
        },
        phrase_blocklist={
            "fuck you", "what the fuck",
            "son of a bitch",
            "sexual content"
        },
        severity_threshold=ContentSeverity.MEDIUM,
        require_ml_confirmation=True
    ),

    "adult": PolicyTemplate(
        name="adult",
        description="Adult filtering (18+)",
        word_blocklist={
            # Only extreme content blocked
            "racial_slur", "hate_speech"
        },
        phrase_blocklist=set(),
        severity_threshold=ContentSeverity.HIGH,
        require_ml_confirmation=True
    ),

    "unrestricted": PolicyTemplate(
        name="unrestricted",
        description="No filtering (unrestricted)",
        word_blocklist=set(),
        phrase_blocklist=set(),
        severity_threshold=ContentSeverity.CRITICAL,
        require_ml_confirmation=False
    )
}


class WordBasedFilter:
    """
    Word-based content filter using blocklists.

    Features:
    - Word matching
    - Phrase matching
    - Case-insensitive
    - Partial word matching prevention
    """

    def __init__(self, policy: PolicyTemplate):
        """
        Initialize word-based filter.

        Args:
            policy: Policy template with blocklists
        """
        self.policy = policy

        # Compile regex patterns for efficiency
        self.word_patterns = [
            re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            for word in policy.word_blocklist
        ]

        self.phrase_patterns = [
            re.compile(re.escape(phrase), re.IGNORECASE)
            for phrase in policy.phrase_blocklist
        ]

    def check(self, content: str) -> FilterResult:
        """
        Check content against word and phrase blocklists.

        Args:
            content: Content to check

        Returns:
            Filter result with matched terms
        """
        start_time = time.time()
        matched_terms = []

        # Check word matches
        for pattern in self.word_patterns:
            matches = pattern.findall(content)
            if matches:
                matched_terms.extend(matches)

        # Check phrase matches
        for pattern in self.phrase_patterns:
            if pattern.search(content):
                matched_terms.append(pattern.pattern)

        is_safe = len(matched_terms) == 0

        if not is_safe:
            severity = self.policy.severity_threshold
            content_checks.labels(policy=self.policy.name, result="blocked").inc()
        else:
            content_checks.labels(policy=self.policy.name, result="safe").inc()

        return FilterResult(
            is_safe=is_safe,
            severity=self.policy.severity_threshold if not is_safe else ContentSeverity.SAFE,
            matched_terms=list(set(matched_terms)),
            layer=FilterLayer.WORD_BASED,
            confidence=1.0 if not is_safe else 0.0,
            policy_violated=self.policy.name if not is_safe else None,
            reasoning=f"Blocked terms: {', '.join(set(matched_terms))}" if matched_terms else "",
            processing_time_ms=(time.time() - start_time) * 1000
        )


class MLBasedFilter:
    """
    ML-based contextual content filter.

    Uses machine learning to understand context and detect
    inappropriate content beyond simple keyword matching.

    Note: This is a simplified implementation. A production system
    would use actual ML models.
    """

    def __init__(self, policy: PolicyTemplate):
        """
        Initialize ML-based filter.

        Args:
            policy: Policy template
        """
        self.policy = policy
        # In production, this would load an ML model
        # For now, we use rule-based heuristics

        # Contextual patterns that suggest inappropriate content
        self.contextual_patterns = {
            "violence": [
                re.compile(r'\bkill\b.*\bperson\b', re.IGNORECASE),
                re.compile(r'\battack\b.*\bweapon\b', re.IGNORECASE),
                re.compile(r'\bhurt\b.*\bbody\b', re.IGNORECASE)
            ],
            "adult": [
                re.compile(r'\bsex\b.*\bact\b', re.IGNORECASE),
                re.compile(r'\bnaked\b.*\bbody\b', re.IGNORECASE),
                re.compile(r'\bdrug\b.*\buse\b', re.IGNORECASE)
            ],
            "hate_speech": [
                re.compile(r'\bhate\b.*\bgroup\b', re.IGNORECASE),
                re.compile(r'discriminat.*against', re.IGNORECASE)
            ]
        }

    def check(self, content: str) -> FilterResult:
        """
        Check content using contextual analysis.

        Args:
            content: Content to check

        Returns:
            Filter result with contextual analysis
        """
        start_time = time.time()

        # Check contextual patterns
        for category, patterns in self.contextual_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    return FilterResult(
                        is_safe=False,
                        severity=ContentSeverity.MEDIUM,
                        matched_terms=[category],
                        layer=FilterLayer.ML_BASED,
                        confidence=0.75,
                        policy_violated=self.policy.name,
                        reasoning=f"Contextual pattern detected: {category}",
                        processing_time_ms=(time.time() - start_time) * 1000
                    )

        # No issues found
        return FilterResult(
            is_safe=True,
            severity=ContentSeverity.SAFE,
            matched_terms=[],
            layer=FilterLayer.ML_BASED,
            confidence=0.95,
            policy_violated=None,
            reasoning="No contextual issues detected",
            processing_time_ms=(time.time() - start_time) * 1000
        )


class SafetyFilterService:
    """
    Multi-layer safety filtering service.

    Features:
    - Word-based filtering (Layer 1)
    - ML-based contextual filtering (Layer 2)
    - Policy template system
    - Audit logging
    - Aggregated results
    """

    def __init__(self, policy_name: str = "family"):
        """
        Initialize safety filter service.

        Args:
            policy_name: Name of policy template to use
        """
        self.policy = POLICY_TEMPLATES.get(policy_name, POLICY_TEMPLATES["family"])
        self.word_filter = WordBasedFilter(self.policy)
        self.ml_filter = MLBasedFilter(self.policy)

        # Audit log
        self.audit_log: List[Dict] = []

    def check_content(self, content: str, content_id: Optional[str] = None) -> FilterResult:
        """
        Check content using multi-layer filtering.

        Args:
            content: Content to check
            content_id: Optional content identifier

        Returns:
            Aggregated filter result
        """
        # Layer 1: Word-based filter
        word_result = self.word_filter.check(content)

        if not word_result.is_safe:
            # Word filter caught something - block immediately
            return self._create_aggregated_result([word_result])

        # Layer 2: ML-based filter (if required)
        if self.policy.require_ml_confirmation:
            ml_result = self.ml_filter.check(content)

            if not ml_result.is_safe:
                return self._create_aggregated_result([word_result, ml_result])

        # All layers passed
        result = FilterResult(
            is_safe=True,
            severity=ContentSeverity.SAFE,
            matched_terms=[],
            layer=FilterLayer.CONTEXTUAL,
            confidence=1.0,
            policy_violated=None,
            reasoning="Content passed all safety checks",
            processing_time_ms=0
        )

        # Log to audit
        self._audit_log(content, content_id, result)

        return result

    def _create_aggregated_result(self, results: List[FilterResult]) -> FilterResult:
        """Aggregate results from multiple filtering layers."""
        # Find the most severe result
        unsafe_results = [r for r in results if not r.is_safe]

        if unsafe_results:
            # Return the most severe violation
            worst_result = max(unsafe_results, key=lambda x: x.severity.value)

            return FilterResult(
                is_safe=False,
                severity=worst_result.severity,
                matched_terms=worst_result.matched_terms,
                layer=FilterLayer.CONTEXTUAL,
                confidence=worst_result.confidence,
                policy_violated=worst_result.policy_violated,
                reasoning=f"Blocked by {worst_result.layer.value}: {worst_result.reasoning}",
                processing_time_ms=sum(r.processing_time_ms for r in results)
            )

        # All safe
        return FilterResult(
            is_safe=True,
            severity=ContentSeverity.SAFE,
            matched_terms=[],
            layer=FilterLayer.CONTEXTUAL,
            confidence=1.0,
            reasoning="Content passed all safety checks",
            processing_time_ms=sum(r.processing_time_ms for r in results)
        )

    def _audit_log(self, content: str, content_id: Optional[str], result: FilterResult):
        """Add entry to audit log."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_id": content_id,
            "content_preview": content[:100] if content else "",  # First 100 chars
            "is_safe": result.is_safe,
            "severity": result.severity.value,
            "policy": result.policy_violated,
            "layer": result.layer.value,
            "matched_terms": result.matched_terms,
            "reasoning": result.reasoning
        }

        self.audit_log.append(log_entry)

        # Keep log size manageable
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]  # Keep last 5000

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]

    def get_stats(self) -> dict:
        """Get safety filter statistics."""
        if not self.audit_log:
            return {"total_checks": 0}

        total = len(self.audit_log)
        blocked = sum(1 for entry in self.audit_log if not entry["is_safe"])

        return {
            "total_checks": total,
            "blocked": blocked,
            "allowed": total - blocked,
            "block_rate": blocked / total if total > 0 else 0,
            "current_policy": self.policy.name
        }


# Convenience function for checking content
def check_content_safety(
    content: str,
    policy: str = "family",
    content_id: Optional[str] = None
) -> dict:
    """
    Check if content is safe according to policy.

    Args:
        content: Content to check
        policy: Policy template name
        content_id: Optional content identifier

    Returns:
        Safety check result as dictionary
    """
    filter_service = SafetyFilterService(policy_name=policy)
    result = filter_service.check_content(content, content_id)

    return {
        "is_safe": result.is_safe,
        "severity": result.severity.value,
        "matched_terms": result.matched_terms,
        "layer": result.layer.value,
        "confidence": result.confidence,
        "policy": result.policy_violated,
        "reasoning": result.reasoning,
        "processing_time_ms": result.processing_time_ms
    }
