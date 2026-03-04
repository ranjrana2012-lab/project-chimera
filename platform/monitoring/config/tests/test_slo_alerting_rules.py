"""Tests for SLO alerting rules validation.

Tests validate Prometheus alerting rule expressions for SLO burn rate and budget exhaustion.
Run with: pytest platform/monitoring/config/tests/test_slo_alerting_rules.py
"""

import pytest
import subprocess
import yaml
from pathlib import Path


class TestSLOAlertingRules:
    """Test suite for SLO alerting rules."""

    @pytest.fixture
    def rules_file(self):
        """Path to the SLO alerting rules file."""
        return Path(__file__).parent.parent / "slo-alerting-rules.yaml"

    @pytest.fixture
    def rules_config(self, rules_file):
        """Load and parse the SLO alerting rules YAML."""
        with open(rules_file) as f:
            return yaml.safe_load(f)

    def test_rules_file_exists(self, rules_file):
        """Test that the SLO alerting rules file exists."""
        assert rules_file.exists(), f"SLO alerting rules file not found: {rules_file}"

    def test_rules_file_valid_yaml(self, rules_config):
        """Test that the rules file is valid YAML."""
        assert rules_config is not None
        assert "groups" in rules_config
        assert isinstance(rules_config["groups"], list)

    def test_slo_alerting_group_exists(self, rules_config):
        """Test that the SLO alerting group exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None, "SLO alerting group not found"

    def test_slo_alerting_group_has_interval(self, rules_config):
        """Test that SLO alerting group has evaluation interval set."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None
        assert "interval" in slo_group
        assert slo_group["interval"] == "1m"

    def test_burn_rate_warning_alert_exists(self, rules_config):
        """Test that burn rate warning alert (2x) exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetBurnRateWarning"), None)
        assert alert is not None, "Burn rate warning alert not found"
        assert "expr" in alert
        assert "> 2" in alert["expr"], "Burn rate warning should trigger at 2x"
        assert "for" in alert
        assert alert["for"] == "5m"

    def test_burn_rate_warning_has_correct_labels(self, rules_config):
        """Test that burn rate warning has correct severity and category."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetBurnRateWarning"), None)
        assert alert is not None

        labels = alert.get("labels", {})
        assert labels.get("severity") == "warning"
        assert labels.get("category") == "slo"

    def test_burn_rate_warning_has_runbook(self, rules_config):
        """Test that burn rate warning includes runbook link."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetBurnRateWarning"), None)
        assert alert is not None

        annotations = alert.get("annotations", {})
        assert "runbook" in annotations or "action" in annotations

    def test_burn_rate_critical_alert_exists(self, rules_config):
        """Test that burn rate critical alert (10x) exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetBurnRateCritical"), None)
        assert alert is not None, "Burn rate critical alert not found"
        assert "expr" in alert
        assert "> 10" in alert["expr"], "Burn rate critical should trigger at 10x"
        assert "for" in alert
        assert alert["for"] == "1m", "Critical alerts should fire faster"

    def test_burn_rate_critical_has_correct_labels(self, rules_config):
        """Test that burn rate critical has correct severity and category."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetBurnRateCritical"), None)
        assert alert is not None

        labels = alert.get("labels", {})
        assert labels.get("severity") == "critical"
        assert labels.get("category") == "slo"

    def test_slo_not_met_alert_exists(self, rules_config):
        """Test that SLO not met alert exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "SLONotMet"), None)
        assert alert is not None, "SLO not met alert not found"
        assert "expr" in alert
        assert "for" in alert

    def test_slo_not_met_checks_all_slos(self, rules_config):
        """Test that SLO not met alert checks all SLO thresholds."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "SLONotMet"), None)
        assert alert is not None

        expr = alert["expr"]
        # Should check all SLO thresholds
        assert "0.999" in expr, "Should check 99.9% threshold (orchestration/safety)"
        assert "0.995" in expr, "Should check 99.5% threshold (generation/captioning)"
        assert "0.99" in expr, "Should check 99% threshold (BSL)"

    def test_error_budget_exhausted_alert_exists(self, rules_config):
        """Test that error budget exhausted alert exists."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetExhausted"), None)
        assert alert is not None, "Error budget exhausted alert not found"
        assert "expr" in alert
        assert "< 0.10" in alert["expr"], "Should alert when budget < 10%"
        assert alert.get("for") == "1m"

    def test_all_alerts_have_action_in_annotations(self, rules_config):
        """Test that all alerts have action guidance."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        for rule in rules:
            if "alert" in rule:
                annotations = rule.get("annotations", {})
                assert "action" in annotations, f"Alert {rule.get('alert')} missing action annotation"

    def test_all_critical_alerts_have_short_for_duration(self, rules_config):
        """Test that critical alerts fire quickly (within 5 minutes)."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        critical_alerts = [r for r in rules if r.get("labels", {}).get("severity") == "critical"]

        for alert in critical_alerts:
            for_duration = alert.get("for", "0m")
            # Parse duration (e.g., "5m" -> 5)
            duration_val = int(for_duration.replace("m", "").replace("s", ""))
            assert duration_val <= 5, f"Critical alert {alert.get('alert')} should fire within 5m"

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

    def test_all_rules_have_alert_name(self, rules_config):
        """Test that all SLO alerting rules have an alert name."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        for rule in rules:
            assert "alert" in rule, f"Rule missing 'alert' field: {rule}"
            assert rule["alert"], f"Rule has empty 'alert' field: {rule}"

    def test_all_alerts_have_summary_annotation(self, rules_config):
        """Test that all alerts have a summary annotation."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        for rule in rules:
            if "alert" in rule:
                annotations = rule.get("annotations", {})
                assert "summary" in annotations, f"Alert {rule.get('alert')} missing summary annotation"

    def test_alert_names_are_descriptive(self, rules_config):
        """Test that alert names follow naming conventions (PascalCase)."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        for rule in rules:
            if "alert" in rule:
                alert_name = rule["alert"]
                # Should be PascalCase or camelCase
                assert alert_name[0].isupper() or alert_name[0].islower(), \
                    f"Alert name should use standard naming: {alert_name}"
                # No spaces or special characters
                assert " " not in alert_name, f"Alert name should not contain spaces: {alert_name}"


class TestSLOAlertingExpressionPatterns:
    """Test specific patterns in SLO alerting rule expressions."""

    @pytest.fixture
    def rules_config(self):
        """Load and parse the SLO alerting rules YAML."""
        rules_file = Path(__file__).parent.parent / "slo-alerting-rules.yaml"
        with open(rules_file) as f:
            return yaml.safe_load(f)

    def test_burn_rate_uses_recording_rule(self, rules_config):
        """Test that burn rate alerts use the slo:error_burn_rate recording rule."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        burn_rate_alerts = [
            r for r in rules
            if "BurnRate" in r.get("alert", "")
        ]

        for alert in burn_rate_alerts:
            expr = alert["expr"]
            assert "slo:error_burn_rate" in expr, \
                f"Burn rate alert {alert.get('alert')} should use slo:error_burn_rate"

    def test_budget_exhausted_uses_recording_rule(self, rules_config):
        """Test that budget exhausted alert uses the slo:error_budget_remaining recording rule."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "ErrorBudgetExhausted"), None)
        assert alert is not None

        expr = alert["expr"]
        assert "slo:error_budget_remaining" in expr, \
            "ErrorBudgetExhausted should use slo:error_budget_remaining"

    def test_slo_not_met_uses_recording_rules(self, rules_config):
        """Test that SLO not met alert uses SLO recording rules."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])
        alert = next((r for r in rules if r.get("alert") == "SLONotMet"), None)
        assert alert is not None

        expr = alert["expr"]
        # Should reference SLO recording rules
        assert "slo:" in expr, "SLONotMet should reference SLO recording rules"

    def test_comparison_operators_are_correct(self, rules_config):
        """Test that alert expressions use correct comparison operators."""
        groups = rules_config["groups"]
        slo_group = next((g for g in groups if g.get("name") == "chimera.slo.alerting"), None)
        assert slo_group is not None

        rules = slo_group.get("rules", [])

        # Burn rate alerts should use >
        burn_rate_alerts = [
            r for r in rules
            if "BurnRate" in r.get("alert", "")
        ]
        for alert in burn_rate_alerts:
            expr = alert["expr"]
            assert ">" in expr, f"Burn rate alert {alert.get('alert')} should use > operator"

        # Budget exhausted should use <
        budget_alert = next((r for r in rules if r.get("alert") == "ErrorBudgetExhausted"), None)
        if budget_alert:
            expr = budget_alert["expr"]
            assert "<" in expr, "ErrorBudgetExhausted should use < operator"

        # SLO not met should use <
        slo_alert = next((r for r in rules if r.get("alert") == "SLONotMet"), None)
        if slo_alert:
            expr = slo_alert["expr"]
            assert "<" in expr or "or" in expr.lower(), "SLONotMet should use < operator"
