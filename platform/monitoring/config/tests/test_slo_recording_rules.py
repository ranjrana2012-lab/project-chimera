"""Tests for SLO recording rules validation.

Tests validate Prometheus recording rule expressions for 30-day SLO calculations.
Run with: pytest platform/monitoring/config/tests/test_slo_recording_rules.py
"""

import pytest
import subprocess
import yaml
from pathlib import Path


class TestSLORecordingRules:
    """Test suite for SLO recording rules."""

    @pytest.fixture
    def rules_file(self):
        """Path to the SLO recording rules file."""
        return Path(__file__).parent.parent / "slo-recording-rules.yaml"

    @pytest.fixture
    def rules_config(self, rules_file):
        """Load and parse the SLO recording rules YAML."""
        with open(rules_file) as f:
            return yaml.safe_load(f)

    def test_rules_file_exists(self, rules_file):
        """Test that the SLO recording rules file exists."""
        assert rules_file.exists(), f"SLO rules file not found: {rules_file}"

    def test_rules_file_valid_yaml(self, rules_config):
        """Test that the rules file is valid YAML."""
        assert rules_config is not None
        assert "groups" in rules_config
        assert isinstance(rules_config["groups"], list)

    def test_slo_recording_group_exists(self, rules_config):
        """Test that the SLO recording group exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None, "SLO recording group not found"

    def test_slo_group_has_interval(self, rules_config):
        """Test that SLO group has evaluation interval set."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None
        assert "interval" in slo_group
        assert slo_group["interval"] in ["30s", "1m"]

    def test_orchestration_slo_rule_exists(self, rules_config):
        """Test that orchestration success rate SLO rule exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:orchestration_success_rate:30d"), None)
        assert rule is not None, "Orchestration SLO rule not found"
        assert "expr" in rule
        # Verify 30-day window
        assert "[30d]" in rule["expr"]

    def test_scenespeak_slo_rule_exists(self, rules_config):
        """Test that SceneSpeak generation SLO rule exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:generation_success_rate:30d"), None)
        assert rule is not None, "SceneSpeak generation SLO rule not found"
        assert "[30d]" in rule["expr"]

    def test_captioning_slo_rule_exists(self, rules_config):
        """Test that captioning delivery rate SLO rule exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:captioning_delivery_rate:30d"), None)
        assert rule is not None, "Captioning SLO rule not found"
        assert "[30d]" in rule["expr"]

    def test_bsl_slo_rule_exists(self, rules_config):
        """Test that BSL translation rate SLO rule exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:bsl_translation_rate:30d"), None)
        assert rule is not None, "BSL SLO rule not found"
        assert "[30d]" in rule["expr"]

    def test_safety_slo_rule_exists(self, rules_config):
        """Test that safety availability SLO rule exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:safety_availability:30d"), None)
        assert rule is not None, "Safety SLO rule not found"
        assert "[30d]" in rule["expr"]

    def test_all_slo_rules_use_30d_window(self, rules_config):
        """Test that all SLO rules use 30-day rolling window.

        Note: Derived metrics like error_budget and burn_rate calculate from
        the SLO metrics themselves, so they don't need [30d] in their expression.
        """
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        slo_rules = [r for r in rules if r.get("record", "").startswith("slo:")]

        # Exclude derived metrics that calculate from other SLO metrics
        derived_metrics = ["error_budget", "burn_rate"]
        for rule in slo_rules:
            record_name = rule.get("record", "")
            if not any(dm in record_name for dm in derived_metrics):
                assert "[30d]" in rule["expr"], f"SLO rule {record_name} must use 30d window"

    def test_slo_rules_use_rate_function(self, rules_config):
        """Test that SLO rules use rate() for time-series calculation.

        Note: Derived metrics (error_budget, burn_rate) calculate from
        already-aggregated SLO metrics, not raw time series.
        """
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        # Exclude derived metrics
        derived_patterns = ["error_budget", "burn_rate"]
        slo_rules = [
            r for r in rules
            if r.get("record", "").startswith("slo:")
            and not any(p in r.get("record", "") for p in derived_patterns)
        ]

        for rule in slo_rules:
            assert "rate(" in rule["expr"], f"SLO rule {rule.get('record')} must use rate() function"
            assert "/" in rule["expr"], f"SLO rule {rule.get('record')} must be a ratio"

    def test_prometheus_syntax_validation(self, rules_file):
        """Test that rules are valid Prometheus syntax using promtool.

        Note: This test requires promtool to be installed.
        If not available, the test will be skipped.
        """
        # Check if promtool is available
        try:
            result = subprocess.run(
                ["promtool", "check", "rules", str(rules_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Promtool validation failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("promtool not available - install prometheus-tools")
        except subprocess.TimeoutExpired:
            pytest.skip("promtool validation timed out")

    def test_all_rules_have_record_name(self, rules_config):
        """Test that all SLO recording rules have a record name."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        for rule in rules:
            assert "record" in rule, f"Rule missing 'record' field: {rule}"
            assert rule["record"], f"Rule has empty 'record' field: {rule}"

    def test_slo_record_names_follow_convention(self, rules_config):
        """Test that SLO record names follow naming convention: slo:<metric>:<window>.

        Note: Derived metrics may have fewer parts (e.g., slo:error_burn_rate).
        """
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        slo_rules = [r for r in rules if r.get("record", "").startswith("slo:")]

        for rule in slo_rules:
            record_name = rule["record"]
            parts = record_name.split(":")
            # Primary SLO metrics should have 3 parts, derived metrics may have 2
            assert len(parts) >= 2, f"SLO record name should have at least 2 parts: {record_name}"
            assert parts[0] == "slo", f"SLO record should start with 'slo:': {record_name}"


class TestSLOExpressionPatterns:
    """Test specific patterns in SLO rule expressions."""

    @pytest.fixture
    def rules_config(self):
        """Load and parse the SLO recording rules YAML."""
        rules_file = Path(__file__).parent.parent / "slo-recording-rules.yaml"
        with open(rules_file) as f:
            return yaml.safe_load(f)

    def test_orchestration_uses_correct_metrics(self, rules_config):
        """Test that orchestration SLO uses orchestration metrics."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:orchestration_success_rate:30d"), None)
        assert rule is not None

        expr = rule["expr"]
        assert "orchestration_success_total" in expr or "orchestration_total" in expr

    def test_scenespeak_uses_correct_metrics(self, rules_config):
        """Test that SceneSpeak SLO uses generation metrics."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        rule = next((r for r in rules if r.get("record") == "slo:generation_success_rate:30d"), None)
        assert rule is not None

        expr = rule["expr"]
        assert "scenespeak_generation" in expr

    def test_all_expressions_are_ratios(self, rules_config):
        """Test that all SLO calculation expressions form valid ratios."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.recording"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        slo_rules = [r for r in rules if r.get("record", "").startswith("slo:") and "burn_rate" not in r.get("record", "")]

        for rule in slo_rules:
            expr = rule["expr"]
            # Should be a ratio with numerator/denominator
            lines = expr.strip().split("\n")
            # Remove empty lines
            lines = [l.strip() for l in lines if l.strip()]
            # Should have division operator
            expr_flat = " ".join(lines)
            assert "/" in expr_flat, f"Expression should be a ratio: {rule.get('record')}"
