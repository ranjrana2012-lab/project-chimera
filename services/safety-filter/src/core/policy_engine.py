"""Policy evaluation and decision engine.

This module evaluates content against configurable policies and
makes final safety decisions based on multiple filter outputs.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import yaml
import json


class StrictnessLevel(str, Enum):
    """Strictness levels for policy evaluation."""
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    STRICT = "strict"


class ActionType(str, Enum):
    """Possible actions for content."""
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"
    WARN = "warn"


class PolicyRule:
    """A single policy rule for content evaluation."""

    def __init__(
        self,
        name: str,
        category: str,
        action: str,
        threshold: float = 0.7,
        enabled: bool = True,
        conditions: Optional[Dict[str, Any]] = None
    ):
        """Initialize a policy rule.

        Args:
            name: Rule name/identifier
            category: Content category this applies to
            action: Action to take (allow, block, flag, warn)
            threshold: Confidence threshold (0.0-1.0)
            enabled: Whether the rule is enabled
            conditions: Optional conditions for application
        """
        self.name = name
        self.category = category
        self.action = action
        self.threshold = threshold
        self.enabled = enabled
        self.conditions = conditions or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "action": self.action,
            "threshold": self.threshold,
            "enabled": self.enabled,
            "conditions": self.conditions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        """Create rule from dictionary."""
        return cls(
            name=data["name"],
            category=data["category"],
            action=data["action"],
            threshold=data.get("threshold", 0.7),
            enabled=data.get("enabled", True),
            conditions=data.get("conditions")
        )


class PolicyEngine:
    """Policy evaluation engine for safety decisions.

    This engine combines results from multiple filters (word list,
    ML classifier, etc.) and applies configurable policies to make
    final safety decisions.
    """

    # Strictness thresholds
    STRICTNESS_THRESHOLDS = {
        StrictnessLevel.PERMISSIVE: {
            "block": 0.95,
            "flag": 0.85,
            "warn": 0.70
        },
        StrictnessLevel.MODERATE: {
            "block": 0.85,
            "flag": 0.70,
            "warn": 0.55
        },
        StrictnessLevel.STRICT: {
            "block": 0.70,
            "flag": 0.55,
            "warn": 0.40
        }
    }

    def __init__(
        self,
        policy_path: Optional[Path] = None,
        default_action: str = "flag",
        default_strictness: StrictnessLevel = StrictnessLevel.MODERATE
    ):
        """Initialize the policy engine.

        Args:
            policy_path: Path to policy configuration file
            default_action: Default action when no rules match
            default_strictness: Default strictness level
        """
        self.policy_path = policy_path
        self.default_action = default_action
        self.default_strictness = default_strictness

        # Policy rules
        self.rules: List[PolicyRule] = []

        # Category weights for decision making
        self.category_weights = {
            "hate_speech": 1.0,
            "sexual_content": 0.95,
            "violence": 0.9,
            "self_harm": 1.0,
            "harassment": 0.85,
            "profanity": 0.5,
            "misinformation": 0.7,
            "spam": 0.3
        }

        # Load policies if path provided
        if policy_path:
            self.load_policies(policy_path)

    def load_policies(self, path: Path):
        """Load policies from file.

        Args:
            path: Path to policy file (JSON or YAML)
        """
        try:
            if path.suffix in ['.yml', '.yaml']:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                with open(path, 'r') as f:
                    data = json.load(f)

            # Load rules
            if "rules" in data:
                self.rules = [
                    PolicyRule.from_dict(rule_data)
                    for rule_data in data["rules"]
                ]

            # Load category weights if present
            if "category_weights" in data:
                self.category_weights.update(data["category_weights"])

            # Load default action if present
            if "default_action" in data:
                self.default_action = data["default_action"]

            print(f"Loaded {len(self.rules)} policy rules from {path}")

        except Exception as e:
            print(f"Warning: Could not load policies from {path}: {e}")
            print("Using default policies")

    def save_policies(self, path: Optional[Path] = None):
        """Save current policies to file.

        Args:
            path: Path to save to (default: policy_path)
        """
        save_path = path or self.policy_path
        if not save_path:
            raise ValueError("No save path specified")

        data = {
            "rules": [rule.to_dict() for rule in self.rules],
            "category_weights": self.category_weights,
            "default_action": self.default_action
        }

        with open(save_path, 'w') as f:
            if save_path.suffix in ['.yml', '.yaml']:
                yaml.safe_dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)

    def add_rule(self, rule: PolicyRule):
        """Add a policy rule.

        Args:
            rule: Rule to add
        """
        # Remove existing rule with same name
        self.rules = [r for r in self.rules if r.name != rule.name]
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """Remove a policy rule by name.

        Args:
            rule_name: Name of rule to remove
        """
        self.rules = [r for r in self.rules if r.name != rule_name]

    def get_rule(self, rule_name: str) -> Optional[PolicyRule]:
        """Get a policy rule by name.

        Args:
            rule_name: Name of rule to get

        Returns:
            Rule if found, None otherwise
        """
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

    def evaluate(
        self,
        content: str,
        word_filter_results: Dict[str, Any],
        ml_filter_results: Dict[str, Any],
        strictness: Optional[StrictnessLevel] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate content against policies.

        Args:
            content: Text content being evaluated
            word_filter_results: Results from word filter
            ml_filter_results: Results from ML filter
            strictness: Strictness level (default: default_strictness)
            categories: Categories to check (default: all)

        Returns:
            Dictionary with final decision and details
        """
        start_time = time.time()

        if strictness is None:
            strictness = self.default_strictness

        # Get thresholds for strictness level
        thresholds = self.STRICTNESS_THRESHOLDS[strictness]

        # Evaluate each filter's results
        word_decision = self._evaluate_word_filter(
            word_filter_results,
            thresholds
        )

        ml_decision = self._evaluate_ml_filter(
            ml_filter_results,
            thresholds,
            categories
        )

        # Apply policy rules
        rule_decisions = self._apply_rules(
            content,
            word_filter_results,
            ml_filter_results,
            categories
        )

        # Combine all decisions
        final_decision = self._combine_decisions(
            word_decision,
            ml_decision,
            rule_decisions,
            thresholds
        )

        # Build result
        result = {
            "decision": final_decision["action"],
            "safe": final_decision["action"] == ActionType.ALLOW,
            "confidence": final_decision["confidence"],
            "explanation": final_decision["explanation"],
            "strictness": strictness.value,
            "applied_rules": final_decision.get("applied_rules", []),
            "category_scores": self._calculate_category_scores(
                word_filter_results,
                ml_filter_results
            ),
            "processing_time_ms": (time.time() - start_time) * 1000
        }

        return result

    def _evaluate_word_filter(
        self,
        results: Dict[str, Any],
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """Evaluate word filter results.

        Args:
            results: Word filter results
            thresholds: Action thresholds

        Returns:
            Decision based on word filter
        """
        action = ActionType.ALLOW
        confidence = 1.0

        if results.get("action") == "block":
            action = ActionType.BLOCK
            confidence = 0.95
        elif results.get("action") == "flag":
            action = ActionType.FLAG
            confidence = 0.8
        elif results.get("action") == "warn":
            if thresholds["warn"] < 0.6:
                action = ActionType.FLAG
            else:
                action = ActionType.WARN
            confidence = 0.7

        return {
            "action": action,
            "confidence": confidence,
            "severity": results.get("highest_severity"),
            "match_count": len(results.get("matches", []))
        }

    def _evaluate_ml_filter(
        self,
        results: Dict[str, Any],
        thresholds: Dict[str, float],
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate ML filter results.

        Args:
            results: ML filter results
            thresholds: Action thresholds
            categories: Categories to check

        Returns:
            Decision based on ML filter
        """
        harm_prob = results.get("harm_probability", 0.0)
        category_scores = results.get("category_scores", {})

        # Filter to requested categories
        if categories:
            category_scores = {
                k: v for k, v in category_scores.items()
                if k in categories
            }

        # Find highest score among categories
        max_score = 0.0
        max_category = None
        for category, score in category_scores.items():
            weighted_score = score * self.category_weights.get(category, 0.5)
            if weighted_score > max_score:
                max_score = weighted_score
                max_category = category

        # Determine action
        action = ActionType.ALLOW
        confidence = 1.0 - harm_prob

        if max_score >= thresholds["block"]:
            action = ActionType.BLOCK
            confidence = max_score
        elif max_score >= thresholds["flag"]:
            action = ActionType.FLAG
            confidence = max_score
        elif max_score >= thresholds["warn"]:
            action = ActionType.WARN
            confidence = max_score

        return {
            "action": action,
            "confidence": confidence,
            "harm_probability": harm_prob,
            "top_category": max_category,
            "category_scores": category_scores
        }

    def _apply_rules(
        self,
        content: str,
        word_results: Dict[str, Any],
        ml_results: Dict[str, Any],
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Apply policy rules to content.

        Args:
            content: Content to check
            word_results: Word filter results
            ml_results: ML filter results
            categories: Categories to check

        Returns:
            List of triggered rules
        """
        triggered = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check category
            if categories and rule.category not in categories:
                continue

            # Check conditions
            if not self._check_conditions(rule, content, word_results, ml_results):
                continue

            # Check threshold
            score = self._get_rule_score(rule, word_results, ml_results)
            if score >= rule.threshold:
                triggered.append({
                    "name": rule.name,
                    "action": rule.action,
                    "category": rule.category,
                    "score": score,
                    "threshold": rule.threshold
                })

        return triggered

    def _check_conditions(
        self,
        rule: PolicyRule,
        content: str,
        word_results: Dict[str, Any],
        ml_results: Dict[str, Any]
    ) -> bool:
        """Check if rule conditions are met.

        Args:
            rule: Rule to check
            content: Content being evaluated
            word_results: Word filter results
            ml_results: ML filter results

        Returns:
            True if conditions are met
        """
        conditions = rule.conditions

        # Check min severity
        if "min_severity" in conditions:
            severity = word_results.get("highest_severity", "mild")
            severity_order = {"mild": 1, "medium": 2, "severe": 3, "custom": 4}
            if severity_order.get(severity, 0) < severity_order.get(conditions["min_severity"], 0):
                return False

        # Check min match count
        if "min_matches" in conditions:
            match_count = len(word_results.get("matches", []))
            if match_count < conditions["min_matches"]:
                return False

        # Check content length
        if "min_length" in conditions:
            if len(content) < conditions["min_length"]:
                return False

        return True

    def _get_rule_score(
        self,
        rule: PolicyRule,
        word_results: Dict[str, Any],
        ml_results: Dict[str, Any]
    ) -> float:
        """Get score for a rule based on filter results.

        Args:
            rule: Rule to score
            word_results: Word filter results
            ml_results: ML filter results

        Returns:
            Score for the rule
        """
        # Get ML score for category
        category_scores = ml_results.get("category_scores", {})
        ml_score = category_scores.get(rule.category, 0.0)

        # Get word filter score
        word_score = 0.0
        for match in word_results.get("matches", []):
            if match["category"] == rule.category:
                word_score = max(word_score, 0.8)

        # Combine scores
        return max(ml_score, word_score)

    def _combine_decisions(
        self,
        word_decision: Dict[str, Any],
        ml_decision: Dict[str, Any],
        rule_decisions: List[Dict[str, Any]],
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """Combine decisions from all sources.

        Args:
            word_decision: Word filter decision
            ml_decision: ML filter decision
            rule_decisions: Triggered rules
            thresholds: Action thresholds

        Returns:
            Combined final decision
        """
        # Action priority: block > flag > warn > allow
        actions = [ActionType.BLOCK, ActionType.FLAG, ActionType.WARN, ActionType.ALLOW]
        action_priority = {a: i for i, a in enumerate(actions)}

        # Collect all actions
        all_actions = [word_decision["action"], ml_decision["action"]]
        for rule in rule_decisions:
            all_actions.append(ActionType(rule["action"]))

        # Find highest priority action
        final_action = min(all_actions, key=lambda a: action_priority.get(a, 99))

        # Calculate confidence
        confidences = [
            word_decision.get("confidence", 0.5),
            ml_decision.get("confidence", 0.5)
        ]
        for rule in rule_decisions:
            confidences.append(rule.get("score", 0.5))

        final_confidence = max(confidences) if final_action != ActionType.ALLOW else min(confidences)

        # Build explanation
        explanation_parts = []
        applied_rules = []

        if word_decision["action"] != ActionType.ALLOW:
            explanation_parts.append(f"Word filter: {word_decision['action'].value}")
        if ml_decision["action"] != ActionType.ALLOW:
            explanation_parts.append(f"ML filter: {ml_decision['action'].value} (category: {ml_decision.get('top_category', 'unknown')})")
        for rule in rule_decisions:
            explanation_parts.append(f"Rule '{rule['name']}' triggered")
            applied_rules.append(rule["name"])

        explanation = ", ".join(explanation_parts) if explanation_parts else "Content passed all safety checks"

        return {
            "action": final_action,
            "confidence": final_confidence,
            "explanation": explanation,
            "applied_rules": applied_rules
        }

    def _calculate_category_scores(
        self,
        word_results: Dict[str, Any],
        ml_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate category scores from filter results.

        Args:
            word_results: Word filter results
            ml_results: ML filter results

        Returns:
            List of category score dictionaries
        """
        scores = []

        # Get category results from word filter
        for category, result in word_results.get("category_results", {}).items():
            score = {
                "category": category,
                "score": result.get("severity_level", 0) / 4.0,  # Normalize to 0-1
                "flagged": len(result.get("matches", [])) > 0,
                "matched_terms": [m["text"] for m in result.get("matches", [])]
            }
            scores.append(score)

        # Add ML category scores
        ml_scores = ml_results.get("category_scores", {})
        for category, score_value in ml_scores.items():
            # Check if we already have this category from word filter
            existing = next((s for s in scores if s["category"] == category), None)
            if existing:
                # Take max of word and ML scores
                existing["score"] = max(existing["score"], score_value)
                existing["flagged"] = existing["flagged"] or score_value > 0.5
            else:
                scores.append({
                    "category": category,
                    "score": score_value,
                    "flagged": score_value > 0.5,
                    "matched_terms": []
                })

        return scores

    def get_policies(self) -> Dict[str, Any]:
        """Get current policies.

        Returns:
            Dictionary with policy information
        """
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "default_action": self.default_action,
            "default_strictness": self.default_strictness.value,
            "category_weights": self.category_weights,
            "active_rule_count": sum(1 for r in self.rules if r.enabled)
        }

    def update_policies(self, rules: List[Dict[str, Any]], default_action: Optional[str] = None):
        """Update policies.

        Args:
            rules: List of rule dictionaries
            default_action: New default action (optional)
        """
        self.rules = [PolicyRule.from_dict(r) for r in rules]
        if default_action:
            self.default_action = default_action
