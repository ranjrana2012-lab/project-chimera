"""
Tests for SLO-based quality gate for deployment blocking.
"""

import pytest
from unittest.mock import Mock, patch
from gate.slo_gate import SloQualityGate, GateResult


class TestSloQualityGate:
    """Test suite for SLO Quality Gate."""

    def test_slo_gate_allows_when_slo_met(self):
        """Test that gate allows when SLO compliance > 95%"""
        gate = SloQualityGate()

        with patch.object(gate, '_get_slo_compliance', return_value=0.997), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "allow"
        assert "healthy" in result.reason.lower()
        assert result.slo_compliance == 0.997
        assert result.error_budget_remaining == 0.45

    def test_slo_gate_blocks_when_slo_not_met(self):
        """Test that gate blocks when SLO compliance < threshold"""
        gate = SloQualityGate()

        with patch.object(gate, '_get_slo_compliance', return_value=0.90), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "block"
        assert "SLO compliance" in result.reason
        assert result.slo_compliance == 0.90
        assert result.error_budget_remaining == 0.45

    def test_slo_gate_blocks_when_budget_exhausted(self):
        """Test that gate blocks when error budget < 10%"""
        gate = SloQualityGate()

        with patch.object(gate, '_get_slo_compliance', return_value=0.997), \
             patch.object(gate, '_get_error_budget', return_value=0.05):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "block"
        assert "Error budget" in result.reason
        assert result.slo_compliance == 0.997
        assert result.error_budget_remaining == 0.05

    def test_slo_gate_blocks_on_both_conditions(self):
        """Test that gate blocks when both SLO and budget are breached"""
        gate = SloQualityGate()

        with patch.object(gate, '_get_slo_compliance', return_value=0.90), \
             patch.object(gate, '_get_error_budget', return_value=0.05):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "block"
        # Should report SLO compliance first (checked first)
        assert "SLO compliance" in result.reason

    def test_slo_gate_different_thresholds_per_service(self):
        """Test that different services have different SLO thresholds"""
        gate = SloQualityGate()

        # openclaw-orchestrator has 99.9% threshold
        with patch.object(gate, '_get_slo_compliance', return_value=0.995), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("openclaw-orchestrator")

        assert result.action == "block"  # 0.995 < 0.999
        assert "SLO compliance" in result.reason

        # bsl-agent has 99% threshold, should pass
        with patch.object(gate, '_get_slo_compliance', return_value=0.995), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("bsl-agent")

        assert result.action == "allow"  # 0.995 > 0.99

    def test_slo_gate_unknown_service_uses_default_threshold(self):
        """Test that unknown services use default threshold of 99%"""
        gate = SloQualityGate()

        # Should block when below default threshold
        with patch.object(gate, '_get_slo_compliance', return_value=0.985), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("unknown-service")

        assert result.action == "block"  # 0.985 < 0.99 (default)

        # Should allow when above default threshold
        with patch.object(gate, '_get_slo_compliance', return_value=0.995), \
             patch.object(gate, '_get_error_budget', return_value=0.45):
            result = gate.check_deployment_readiness("unknown-service")

        assert result.action == "allow"  # 0.995 > 0.99 (default)

    def test_slo_gate_at_exact_threshold(self):
        """Test behavior at exact threshold boundary"""
        gate = SloQualityGate()

        # At exact threshold (0.995), should pass (>= comparison)
        with patch.object(gate, '_get_slo_compliance', return_value=0.995), \
             patch.object(gate, '_get_error_budget', return_value=0.15):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "allow"

        # At exact budget threshold (0.10), should pass (>= comparison)
        with patch.object(gate, '_get_slo_compliance', return_value=0.997), \
             patch.object(gate, '_get_error_budget', return_value=0.10):
            result = gate.check_deployment_readiness("scenespeak-agent")

        assert result.action == "allow"

    def test_gate_result_dataclass(self):
        """Test GateResult dataclass structure"""
        result = GateResult(
            action="allow",
            reason="All checks passed",
            slo_compliance=0.997,
            error_budget_remaining=0.45
        )

        assert result.action == "allow"
        assert result.reason == "All checks passed"
        assert result.slo_compliance == 0.997
        assert result.error_budget_remaining == 0.45

    def test_gate_result_optional_fields(self):
        """Test GateResult with optional fields"""
        result = GateResult(
            action="block",
            reason="SLO not met"
        )

        assert result.action == "block"
        assert result.reason == "SLO not met"
        assert result.slo_compliance is None
        assert result.error_budget_remaining is None

    def test_slo_thresholds_configuration(self):
        """Test that SLO thresholds are properly configured"""
        gate = SloQualityGate()

        expected_thresholds = {
            "openclaw-orchestrator": {"slo": 0.999, "budget": 0.10},
            "scenespeak-agent": {"slo": 0.995, "budget": 0.10},
            "captioning-agent": {"slo": 0.995, "budget": 0.10},
            "bsl-agent": {"slo": 0.99, "budget": 0.10},
            "safety-filter": {"slo": 0.999, "budget": 0.10},
            "operator-console": {"slo": 0.995, "budget": 0.10},
        }

        assert gate.SLO_THRESHOLDS == expected_thresholds

    @patch('gate.slo_gate.requests.get')
    def test_get_slo_compliance_queries_prometheus(self, mock_get):
        """Test that _get_slo_compliance queries Prometheus"""
        gate = SloQualityGate()

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "result": [
                    {"value": ["1234567890", "0.997"]}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = gate._get_slo_compliance("scenespeak-agent")

        assert result == 0.997
        mock_get.assert_called_once()

    @patch('gate.slo_gate.requests.get')
    def test_get_error_budget_queries_prometheus(self, mock_get):
        """Test that _get_error_budget queries Prometheus"""
        gate = SloQualityGate()

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "result": [
                    {"value": ["1234567890", "0.45"]}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = gate._get_error_budget("scenespeak-agent")

        assert result == 0.45
        mock_get.assert_called_once()

    def test_custom_prometheus_url(self):
        """Test that custom Prometheus URL can be set"""
        custom_url = "http://custom-prometheus:9090"
        gate = SloQualityGate(prometheus_url=custom_url)

        assert gate.prometheus_url == custom_url
