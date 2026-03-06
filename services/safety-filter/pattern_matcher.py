"""
Pattern Matcher for Safety Filter.

Provides pattern-based content filtering including:
- Profanity detection
- PII (Personally Identifiable Information) detection
- Harmful content detection
"""

import re
import logging
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass

from models import ModerationLevel, MatchedPattern

logger = logging.getLogger(__name__)


@dataclass
class PatternConfig:
    """Configuration for a pattern category"""
    name: str
    patterns: List[str]
    severity: ModerationLevel
    enabled: bool = True


class PatternMatcher:
    """
    Pattern-based content filtering.

    Features:
    - Profanity detection (keyword list)
    - PII detection (email, phone, SSN patterns)
    - Harmful content patterns
    - Configurable blocklists
    """

    # Profanity blocklist
    PROFANITY_PATTERNS = [
        r'\b(damn|hell|shit|fuck|bitch|bastard|ass|crap|suck|stupid|idiot)\b',
        r'\b\w*shit\w*\b',
        r'\b\w*fuck\w*\b',
        r'\b\w*damn\w*\b',
        r'\b\whell\w*\b',
    ]

    # PII detection patterns
    PII_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'phone'),
        (r'\b\d{3}-\d{2}-\d{4}\b', 'ssn'),
        (r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', 'credit_card'),
    ]

    # Harmful content patterns
    HARMFUL_PATTERNS = [
        (r'\b(kill|murder|death)\b.*(person|people|someone)\b', 'violence_threat'),
        (r'\b(hack|exploit|bypass)\b.*(system|security|password)\b', 'cyberthreat'),
        (r'\b(drug|overdose)\b.*(use|abuse|take)\b', 'substance_abuse'),
        (r'\b(self.harm|suicide|kill.myself)\b', 'self_harm'),
    ]

    def __init__(self, policy: str = "family"):
        """
        Initialize pattern matcher.

        Args:
            policy: Moderation policy to apply (family, teen, adult, unrestricted)
        """
        self.policy = policy
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        self._configure_policy()

    def _configure_policy(self):
        """Configure patterns based on policy"""
        # Profanity patterns based on policy
        profanity_enabled = self.policy in ["family", "teen"]

        if profanity_enabled:
            self._compiled_patterns["profanity"] = [
                (re.compile(pattern, re.IGNORECASE), "profanity")
                for pattern in self.PROFANITY_PATTERNS
            ]

        # PII patterns (always enabled)
        self._compiled_patterns["pii"] = [
            (re.compile(pattern, re.IGNORECASE), pii_type)
            for pattern, pii_type in self.PII_PATTERNS
        ]

        # Harmful content patterns based on policy
        if self.policy in ["family", "teen"]:
            self._compiled_patterns["harmful"] = [
                (re.compile(pattern, re.IGNORECASE), harmful_type)
                for pattern, harmful_type in self.HARMFUL_PATTERNS
            ]

    def check(self, content: str) -> Tuple[bool, List[MatchedPattern]]:
        """
        Check content against all patterns.

        Args:
            content: Content to check

        Returns:
            Tuple of (is_safe, matched_patterns)
        """
        matched = []

        # Check all pattern categories
        for category, patterns in self._compiled_patterns.items():
            for pattern, pattern_type in patterns:
                matches = pattern.finditer(content)
                for match in matches:
                    severity = self._get_severity(category)
                    matched.append(MatchedPattern(
                        pattern=pattern.pattern,
                        type=f"{category}_{pattern_type}",
                        severity=severity,
                        position=match.start()
                    ))

        is_safe = len(matched) == 0
        return is_safe, matched

    def _get_severity(self, category: str) -> ModerationLevel:
        """Get severity level for a pattern category"""
        severity_map = {
            "profanity": ModerationLevel.LOW,
            "pii": ModerationLevel.HIGH,
            "harmful": ModerationLevel.CRITICAL,
        }
        return severity_map.get(category, ModerationLevel.MEDIUM)

    def get_pattern_count(self) -> int:
        """Get total number of active patterns"""
        return sum(len(patterns) for patterns in self._compiled_patterns.values())

    def add_custom_pattern(self, pattern: str, category: str, severity: ModerationLevel):
        """
        Add a custom pattern to the matcher.

        Args:
            pattern: Regex pattern to add
            category: Category for the pattern
            severity: Severity level for matches
        """
        if category not in self._compiled_patterns:
            self._compiled_patterns[category] = []

        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            self._compiled_patterns[category].append((compiled, "custom"))
            logger.info(f"Added custom pattern to {category}: {pattern}")
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")

    def remove_pattern_category(self, category: str):
        """
        Remove all patterns from a category.

        Args:
            category: Category to remove
        """
        if category in self._compiled_patterns:
            del self._compiled_patterns[category]
            logger.info(f"Removed pattern category: {category}")
