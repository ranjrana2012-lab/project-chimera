"""Tests for PolicyEngine"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.core.policy_engine import PolicyEngine


@pytest.fixture
def temp_policy_file():
    """Create a temporary policy file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "policies.yaml"

        sample_policies = {
            "profanity": {"enabled": True, "auto_block": True},
            "hate_speech": {"enabled": True, "auto_block": True},
            "violence": {"enabled": True, "auto_block": False},
            "harassment": {"enabled": False, "auto_block": False},
        }

        with open(config_path, "w") as f:
            yaml.dump(sample_policies, f)

        yield config_path


@pytest.fixture
def empty_policy_file():
    """Create an empty temporary directory (no policy file)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "nonexistent_policies.yaml"


@pytest.mark.unit
class TestPolicyEngine:
    """Test cases for PolicyEngine."""

    def test_init_with_config_file(self, temp_policy_file):
        """Test initialization with a config file."""
        engine = PolicyEngine(config_path=str(temp_policy_file))

        assert engine.config_path == temp_policy_file
        assert engine.policies is not None
        assert "profanity" in engine.policies
        assert "hate_speech" in engine.policies
        assert "violence" in engine.policies
        assert "harassment" in engine.policies

    def test_init_without_config_file(self, empty_policy_file):
        """Test initialization without a config file (uses defaults)."""
        engine = PolicyEngine(config_path=str(empty_policy_file))

        assert engine.config_path == empty_policy_file
        assert engine.policies is not None
        # Should have default policies
        assert "profanity" in engine.policies
        assert "hate_speech" in engine.policies
        assert "violence" in engine.policies

    def test_init_default_path(self):
        """Test initialization with default path."""
        engine = PolicyEngine()

        assert engine.config_path == Path("/app/configs/policies.yaml")
        # Should load default policies since file doesn't exist
        assert engine.policies is not None
        assert "profanity" in engine.policies

    def test_default_policies(self):
        """Test that default policies are correctly defined."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")

        defaults = engine._default_policies()

        assert defaults["profanity"]["enabled"] is True
        assert defaults["profanity"]["auto_block"] is True
        assert defaults["hate_speech"]["enabled"] is True
        assert defaults["hate_speech"]["auto_block"] is True
        assert defaults["violence"]["enabled"] is True
        assert defaults["violence"]["auto_block"] is False

    def test_evaluate_returns_valid_structure(self):
        """Test that evaluate returns a valid result structure."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")
        result = engine.evaluate("This is a test content")

        assert "decision" in result
        assert "confidence" in result
        assert "categories" in result
        assert isinstance(result["decision"], str)
        assert isinstance(result["confidence"], (int, float))
        assert isinstance(result["categories"], dict)

    def test_evaluate_categories_structure(self):
        """Test that categories in evaluation result have correct structure."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")
        result = engine.evaluate("Test content")

        categories = result["categories"]
        assert "profanity" in categories
        assert "hate_speech" in categories
        assert "violence" in categories
        # Categories should be boolean values
        assert isinstance(categories["profanity"], bool)
        assert isinstance(categories["hate_speech"], bool)
        assert isinstance(categories["violence"], bool)

    def test_evaluate_approved_content(self):
        """Test evaluation of safe content returns approved."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")
        result = engine.evaluate("This is a safe and friendly message.")

        assert result["decision"] == "approved"
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    def test_load_policies_from_file(self, temp_policy_file):
        """Test loading policies from an existing file."""
        engine = PolicyEngine(config_path=str(temp_policy_file))

        assert engine.policies["profanity"]["enabled"] is True
        assert engine.policies["profanity"]["auto_block"] is True
        assert engine.policies["hate_speech"]["enabled"] is True
        assert engine.policies["hate_speech"]["auto_block"] is True
        assert engine.policies["violence"]["enabled"] is True
        assert engine.policies["violence"]["auto_block"] is False
        assert engine.policies["harassment"]["enabled"] is False
        assert engine.policies["harassment"]["auto_block"] is False

    def test_load_policies_nonexistent_file(self, empty_policy_file):
        """Test loading policies from a nonexistent file returns defaults."""
        engine = PolicyEngine(config_path=str(empty_policy_file))

        # Should return default policies
        policies = engine._load_policies()
        assert "profanity" in policies
        assert "hate_speech" in policies
        assert "violence" in policies

    def test_evaluate_empty_content(self):
        """Test evaluation of empty content."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")
        result = engine.evaluate("")

        assert "decision" in result
        assert "confidence" in result
        assert "categories" in result

    def test_evaluate_long_content(self):
        """Test evaluation of long content."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")
        long_content = "This is a test. " * 100
        result = engine.evaluate(long_content)

        assert "decision" in result
        assert "confidence" in result
        assert "categories" in result

    def test_policy_configuration_respected(self, temp_policy_file):
        """Test that policy configuration from file is respected."""
        engine = PolicyEngine(config_path=str(temp_policy_file))

        # Verify the custom policy is loaded
        assert "harassment" in engine.policies
        assert engine.policies["harassment"]["enabled"] is False
        assert engine.policies["harassment"]["auto_block"] is False

    def test_multiple_evaluate_calls(self):
        """Test that multiple evaluate calls work correctly."""
        engine = PolicyEngine(config_path="/nonexistent/path.yaml")

        result1 = engine.evaluate("First content")
        result2 = engine.evaluate("Second content")
        result3 = engine.evaluate("Third content")

        assert result1["decision"] == "approved"
        assert result2["decision"] == "approved"
        assert result3["decision"] == "approved"
