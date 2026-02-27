"""Unit tests for Safety Filter Policy Engine module."""

import pytest
from services.safety_filter.src.core.policy_engine import (
    PolicyEngine,
    PolicyRule,
    StrictnessLevel,
    ActionType
)


@pytest.mark.unit
class TestPolicyRule:
    """Test cases for PolicyRule class."""

    def test_create_rule(self):
        """Test creating a policy rule."""
        rule = PolicyRule(
            name="test_rule",
            category="profanity",
            action="block",
            threshold=0.8
        )
        assert rule.name == "test_rule"
        assert rule.category == "profanity"
        assert rule.action == "block"
        assert rule.threshold == 0.8
        assert rule.enabled is True

    def test_rule_to_dict(self):
        """Test converting rule to dictionary."""
        rule = PolicyRule(
            name="test_rule",
            category="violence",
            action="flag",
            threshold=0.7,
            enabled=False
        )
        data = rule.to_dict()
        assert data["name"] == "test_rule"
        assert data["category"] == "violence"
        assert data["action"] == "flag"
        assert data["threshold"] == 0.7
        assert data["enabled"] is False

    def test_rule_from_dict(self):
        """Test creating rule from dictionary."""
        data = {
            "name": "test_rule",
            "category": "hate_speech",
            "action": "block",
            "threshold": 0.9,
            "enabled": True,
            "conditions": {"min_severity": "high"}
        }
        rule = PolicyRule.from_dict(data)
        assert rule.name == "test_rule"
        assert rule.conditions["min_severity"] == "high"


@pytest.mark.unit
class TestPolicyEngine:
    """Test cases for PolicyEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a PolicyEngine instance for testing."""
        return PolicyEngine()

    def test_initialization(self, engine):
        """Test that PolicyEngine initializes correctly."""
        assert engine.rules is not None
        assert engine.default_action is not None
        assert engine.category_weights is not None
        assert "hate_speech" in engine.category_weights

    def test_default_strictness(self, engine):
        """Test default strictness level."""
        assert engine.default_strictness == StrictnessLevel.MODERATE

    def test_strictness_thresholds(self, engine):
        """Test that strictness thresholds are defined."""
        thresholds = engine.STRICTNESS_THRESHOLDS
        assert StrictnessLevel.PERMISSIVE in thresholds
        assert StrictnessLevel.MODERATE in thresholds
        assert StrictnessLevel.STRICT in thresholds

        # Permissive should have higher thresholds than strict
        permissive = thresholds[StrictnessLevel.PERMISSIVE]
        strict = thresholds[StrictnessLevel.STRICT]
        assert permissive["block"] > strict["block"]

    def test_evaluate_word_filter_results(self, engine):
        """Test evaluating word filter results."""
        word_results = {
            "action": "block",
            "matches": [{"category": "profanity"}],
            "highest_severity": "severe"
        }
        thresholds = {
            "block": 0.8,
            "flag": 0.7,
            "warn": 0.5
        }
        decision = engine._evaluate_word_filter(word_results, thresholds)
        assert decision["action"] == ActionType.BLOCK

    def test_evaluate_ml_filter_results(self, engine):
        """Test evaluating ML filter results."""
        ml_results = {
            "harm_probability": 0.85,
            "category_scores": {
                "profanity": 0.9,
                "hate_speech": 0.1
            }
        }
        thresholds = {
            "block": 0.8,
            "flag": 0.7,
            "warn": 0.5
        }
        decision = engine._evaluate_ml_filter(ml_results, thresholds, None)
        assert decision["action"] in [ActionType.BLOCK, ActionType.FLAG]

    def test_evaluate_combined_results(self, engine):
        """Test evaluating combined filter results."""
        word_results = {
            "action": "flag",
            "matches": [],
            "category_results": {},
            "highest_severity": "medium"
        }
        ml_results = {
            "harm_probability": 0.3,
            "category_scores": {"safe": 0.7}
        }
        thresholds = {
            "block": 0.8,
            "flag": 0.7,
            "warn": 0.5
        }

        result = engine.evaluate(
            content="Test content",
            word_filter_results=word_results,
            ml_filter_results=ml_results,
            strictness=StrictnessLevel.MODERATE
        )
        assert "decision" in result
        assert "safe" in result
        assert "confidence" in result

    def test_add_rule(self, engine):
        """Test adding a policy rule."""
        rule = PolicyRule(
            name="new_rule",
            category="profanity",
            action="block",
            threshold=0.8
        )
        engine.add_rule(rule)
        assert engine.get_rule("new_rule") is not None
        assert len(engine.rules) > 0

    def test_remove_rule(self, engine):
        """Test removing a policy rule."""
        rule = PolicyRule(
            name="temp_rule",
            category="violence",
            action="flag",
            threshold=0.7
        )
        engine.add_rule(rule)
        assert engine.get_rule("temp_rule") is not None

        engine.remove_rule("temp_rule")
        assert engine.get_rule("temp_rule") is None

    def test_get_rule(self, engine):
        """Test getting a specific rule."""
        rule = PolicyRule(
            name="test_get",
            category="spam",
            action="block",
            threshold=0.9
        )
        engine.add_rule(rule)
        retrieved = engine.get_rule("test_get")
        assert retrieved is not None
        assert retrieved.name == "test_get"

    def test_get_policies(self, engine):
        """Test getting all policies."""
        policies = engine.get_policies()
        assert "rules" in policies
        assert "default_action" in policies
        assert "category_weights" in policies
        assert "active_rule_count" in policies

    def test_update_policies(self, engine):
        """Test updating policies."""
        new_rules = [
            {
                "name": "rule1",
                "category": "profanity",
                "action": "block",
                "threshold": 0.8,
                "enabled": True
            },
            {
                "name": "rule2",
                "category": "violence",
                "action": "flag",
                "threshold": 0.7,
                "enabled": True
            }
        ]
        engine.update_policies(new_rules, default_action="block")
        assert len(engine.rules) == 2
        assert engine.default_action == "block"

    def test_category_weights(self, engine):
        """Test category weights are properly set."""
        # Hate speech and self-harm should have highest weight
        assert engine.category_weights["hate_speech"] >= 0.9
        assert engine.category_weights["self_harm"] >= 0.9

        # Spam should have lower weight
        assert engine.category_weights["spam"] < 0.5

    def test_calculate_category_scores(self, engine):
        """Test calculating combined category scores."""
        word_results = {
            "category_results": {
                "profanity": {
                    "matches": [{"text": "damn"}],
                    "severity_level": 1
                }
            },
            "matches": []
        }
        ml_results = {
            "category_scores": {
                "profanity": 0.8,
                "violence": 0.2
            }
        }
        scores = engine._calculate_category_scores(word_results, ml_results)
        assert len(scores) > 0
        assert all("category" in s and "score" in s for s in scores)

    def test_check_conditions(self, engine):
        """Test rule condition checking."""
        rule = PolicyRule(
            name="conditional_rule",
            category="profanity",
            action="block",
            conditions={"min_severity": "high"}
        )

        word_results = {
            "highest_severity": "severe",
            "matches": []
        }
        ml_results = {"harm_probability": 0.5}

        # Should pass with severe
        assert engine._check_conditions(rule, "test", word_results, ml_results) is True

        # Should fail with mild
        word_results["highest_severity"] = "mild"
        assert engine._check_conditions(rule, "test", word_results, ml_results) is False

    def test_combine_decisions_block_priority(self, engine):
        """Test that block action has highest priority."""
        thresholds = {"block": 0.8, "flag": 0.7, "warn": 0.5}

        word_decision = {"action": ActionType.FLAG, "confidence": 0.7}
        ml_decision = {"action": ActionType.BLOCK, "confidence": 0.9}
        rule_decisions = []

        combined = engine._combine_decisions(word_decision, ml_decision, rule_decisions, thresholds)
        assert combined["action"] == ActionType.BLOCK

    def test_strictness_affects_decision(self, engine):
        """Test that strictness level affects decisions."""
        word_results = {
            "action": "flag",
            "matches": [{"category": "profanity"}],
            "category_results": {},
            "highest_severity": "medium"
        }
        ml_results = {
            "harm_probability": 0.6,
            "category_scores": {"profanity": 0.6}
        }

        # Permissive should be more lenient
        permissive_result = engine.evaluate(
            content="Test",
            word_filter_results=word_results,
            ml_filter_results=ml_results,
            strictness=StrictnessLevel.PERMISSIVE
        )

        # Strict should be more aggressive
        strict_result = engine.evaluate(
            content="Test",
            word_filter_results=word_results,
            ml_filter_results=ml_results,
            strictness=StrictnessLevel.STRICT
        )

        # Results should differ
        assert "decision" in permissive_result
        assert "decision" in strict_result
