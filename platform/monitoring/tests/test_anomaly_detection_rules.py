#!/usr/bin/env python3
"""
Test suite for anomaly detection rules.
Validates YAML structure, required fields, and Prometheus rule expressions.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any


class AnomalyDetectionRuleTest:
    """Test class for anomaly detection rules validation"""

    def __init__(self, rules_file: str):
        self.rules_file = Path(rules_file)
        self.rules_data = None
        self.errors = []
        self.warnings = []

    def load_rules(self) -> bool:
        """Load and parse YAML file"""
        try:
            with open(self.rules_file, 'r') as f:
                self.rules_data = yaml.safe_load(f)
            return True
        except FileNotFoundError:
            self.errors.append(f"Rules file not found: {self.rules_file}")
            return False
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False

    def test_file_structure(self) -> bool:
        """Test basic file structure"""
        if not self.rules_data:
            self.errors.append("No data loaded")
            return False

        if 'groups' not in self.rules_data:
            self.errors.append("Missing 'groups' key")
            return False

        if not isinstance(self.rules_data['groups'], list):
            self.errors.append("'groups' must be a list")
            return False

        return True

    def test_group_structure(self) -> bool:
        """Test alert group structure"""
        groups = self.rules_data.get('groups', [])
        if len(groups) != 1:
            self.errors.append(f"Expected 1 group, found {len(groups)}")
            return False

        group = groups[0]
        required_keys = ['name', 'interval', 'rules']
        for key in required_keys:
            if key not in group:
                self.errors.append(f"Group missing required key: {key}")
                return False

        if group['name'] != 'chimera.anomaly_detection':
            self.errors.append(f"Group name should be 'chimera.anomaly_detection', got '{group['name']}'")
            return False

        # Validate interval format
        interval_pattern = r'^\d+[sm]$'
        if not re.match(interval_pattern, str(group['interval'])):
            self.errors.append(f"Group interval should be in format like '1m' or '30s', got '{group['interval']}'")
            return False

        return True

    def test_required_alerts(self) -> bool:
        """Test that all required anomaly detection alerts are present"""
        required_alerts = {
            'LatencyAnomalyDetected',
            'ErrorPatternAnomaly',
            'TrafficDropAnomaly',
            'CacheHitRateDrop'
        }

        group = self.rules_data['groups'][0]
        found_alerts = {rule['alert'] for rule in group.get('rules', [])}

        missing = required_alerts - found_alerts
        if missing:
            self.errors.append(f"Missing required alerts: {missing}")
            return False

        return True

    def test_alert_structure(self) -> bool:
        """Test individual alert structure"""
        group = self.rules_data['groups'][0]
        rules = group.get('rules', [])

        for rule in rules:
            # Required keys
            required_keys = ['alert', 'expr', 'for', 'labels', 'annotations']
            for key in required_keys:
                if key not in rule:
                    self.errors.append(f"Alert '{rule.get('alert', 'unknown')}' missing key: {key}")
                    return False

            # Labels must include severity and category
            if 'severity' not in rule['labels']:
                self.errors.append(f"Alert '{rule['alert']}' missing severity label")
                return False

            if 'category' not in rule['labels']:
                self.errors.append(f"Alert '{rule['alert']}' missing category label")
                return False

            # Validate severity values
            valid_severities = ['critical', 'warning', 'info']
            if rule['labels']['severity'] not in valid_severities:
                self.errors.append(f"Alert '{rule['alert']}' has invalid severity: {rule['labels']['severity']}")

            # Validate category values
            valid_categories = ['anomaly', 'performance', 'availability']
            if rule['labels']['category'] not in valid_categories:
                self.errors.append(f"Alert '{rule['alert']}' has invalid category: {rule['labels']['category']}")

            # Annotations must include summary and description
            if 'summary' not in rule['annotations']:
                self.errors.append(f"Alert '{rule['alert']}' missing summary annotation")
                return False

            if 'description' not in rule['annotations']:
                self.errors.append(f"Alert '{rule['alert']}' missing description annotation")
                return False

            # Validate expr is a string and not empty
            if not isinstance(rule['expr'], str):
                self.errors.append(f"Alert '{rule['alert']}' expr must be a string")
                return False

            if not rule['expr'].strip():
                self.errors.append(f"Alert '{rule['alert']}' expr cannot be empty")
                return False

            # Validate 'for' format
            for_pattern = r'^\d+[sm]$'
            if not re.match(for_pattern, str(rule['for'])):
                self.errors.append(f"Alert '{rule['alert']}' 'for' value should be in format like '5m' or '30s', got '{rule['for']}'")

        return len(self.errors) == 0

    def test_prometheus_expression_syntax(self) -> bool:
        """Test Prometheus expression syntax"""
        group = self.rules_data['groups'][0]
        rules = group.get('rules', [])

        for rule in rules:
            expr = rule['expr']

            # Check for balanced parentheses
            if expr.count('(') != expr.count(')'):
                self.errors.append(f"Alert '{rule['alert']}' has unbalanced parentheses in expr")

            # Check for balanced braces
            open_braces = expr.count('{')
            close_braces = expr.count('}')
            if open_braces != close_braces:
                self.errors.append(f"Alert '{rule['alert']}' has unbalanced braces in expr")

            # Check for valid Prometheus operators
            valid_operators = ['==', '!=', '>', '<', '>=', '<=', '=~', '!~']
            has_operator = any(op in expr for op in valid_operators)
            if not has_operator:
                self.errors.append(f"Alert '{rule['alert']}' expr should contain a comparison operator")

            # Check for rate() usage which is common in anomaly detection
            if 'rate(' not in expr and 'avg_over_time(' not in expr:
                self.warnings.append(f"Alert '{rule['alert']}' does not use rate() or avg_over_time() - may not detect anomalies properly")

        return len(self.errors) == 0

    def test_latency_anomaly_rule(self) -> bool:
        """Test LatencyAnomalyDetected rule specifically"""
        group = self.rules_data['groups'][0]
        rules_by_name = {rule['alert']: rule for rule in group.get('rules', [])}

        if 'LatencyAnomalyDetected' not in rules_by_name:
            self.errors.append("LatencyAnomalyDetected alert not found")
            return False

        rule = rules_by_name['LatencyAnomalyDetected']

        # Check severity
        if rule['labels']['severity'] != 'warning':
            self.errors.append("LatencyAnomalyDetected should have severity 'warning'")

        # Check category
        if rule['labels']['category'] != 'anomaly':
            self.errors.append("LatencyAnomalyDetected should have category 'anomaly'")

        # Check it uses request_duration_seconds
        if 'request_duration_seconds_sum' not in rule['expr']:
            self.errors.append("LatencyAnomalyDetected should use request_duration_seconds_sum metric")

        if 'request_duration_seconds_count' not in rule['expr']:
            self.errors.append("LatencyAnomalyDetected should use request_duration_seconds_count metric")

        # Check for comparison with 1-hour average
        if 'avg_over_time' not in rule['expr']:
            self.errors.append("LatencyAnomalyDetected should use avg_over_time for baseline comparison")

        if '1h' not in rule['expr']:
            self.errors.append("LatencyAnomalyDetected should compare against 1-hour average")

        # Check 'for' duration
        if rule['for'] != '5m':
            self.warnings.append(f"LatencyAnomalyDetected 'for' should be '5m', got '{rule['for']}'")

        # Check annotations
        if 'investigation' not in rule['annotations']:
            self.errors.append("LatencyAnomalyDetected should include 'investigation' annotation with Jaeger link")

        return len(self.errors) == 0

    def test_error_pattern_anomaly_rule(self) -> bool:
        """Test ErrorPatternAnomaly rule specifically"""
        group = self.rules_data['groups'][0]
        rules_by_name = {rule['alert']: rule for rule in group.get('rules', [])}

        if 'ErrorPatternAnomaly' not in rules_by_name:
            self.errors.append("ErrorPatternAnomaly alert not found")
            return False

        rule = rules_by_name['ErrorPatternAnomaly']

        # Check severity
        if rule['labels']['severity'] != 'warning':
            self.errors.append("ErrorPatternAnomaly should have severity 'warning'")

        # Check category
        if rule['labels']['category'] != 'anomaly':
            self.errors.append("ErrorPatternAnomaly should have category 'anomaly'")

        # Check it uses error_pattern_total metric
        if 'error_pattern_total' not in rule['expr']:
            self.errors.append("ErrorPatternAnomaly should use error_pattern_total metric")

        # Check for comparison with 1-hour average
        if 'avg_over_time' not in rule['expr']:
            self.errors.append("ErrorPatternAnomaly should use avg_over_time for baseline comparison")

        if '1h' not in rule['expr']:
            self.errors.append("ErrorPatternAnomaly should compare against 1-hour average")

        # Check multiplier is >= 3 (3x threshold)
        if '* 3' not in rule['expr']:
            self.warnings.append("ErrorPatternAnomaly should use 3x threshold for spike detection")

        return len(self.errors) == 0

    def test_traffic_drop_anomaly_rule(self) -> bool:
        """Test TrafficDropAnomaly rule specifically"""
        group = self.rules_data['groups'][0]
        rules_by_name = {rule['alert']: rule for rule in group.get('rules', [])}

        if 'TrafficDropAnomaly' not in rules_by_name:
            self.errors.append("TrafficDropAnomaly alert not found")
            return False

        rule = rules_by_name['TrafficDropAnomaly']

        # Check severity
        if rule['labels']['severity'] != 'warning':
            self.errors.append("TrafficDropAnomaly should have severity 'warning'")

        # Check category
        if rule['labels']['category'] != 'anomaly':
            self.errors.append("TrafficDropAnomaly should have category 'anomaly'")

        # Check it uses http_requests_total metric
        if 'http_requests_total' not in rule['expr']:
            self.errors.append("TrafficDropAnomaly should use http_requests_total metric")

        # Check for less-than operator (detecting drops)
        if '<' not in rule['expr']:
            self.errors.append("TrafficDropAnomaly should use '<' operator to detect drops")

        # Check for comparison with 1-hour average
        if 'avg_over_time' not in rule['expr']:
            self.errors.append("TrafficDropAnomaly should use avg_over_time for baseline comparison")

        if '1h' not in rule['expr']:
            self.errors.append("TrafficDropAnomaly should compare against 1-hour average")

        # Check threshold is 50% or similar
        if '* 0.5' not in rule['expr']:
            self.warnings.append("TrafficDropAnomaly should use 0.5 (50%) threshold for drop detection")

        # Check 'for' duration (should be longer to avoid false positives)
        if rule['for'] != '10m':
            self.warnings.append(f"TrafficDropAnomaly 'for' should be '10m', got '{rule['for']}'")

        return len(self.errors) == 0

    def test_cache_hit_rate_drop_rule(self) -> bool:
        """Test CacheHitRateDrop rule specifically"""
        group = self.rules_data['groups'][0]
        rules_by_name = {rule['alert']: rule for rule in group.get('rules', [])}

        if 'CacheHitRateDrop' not in rules_by_name:
            self.errors.append("CacheHitRateDrop alert not found")
            return False

        rule = rules_by_name['CacheHitRateDrop']

        # Check severity
        if rule['labels']['severity'] != 'warning':
            self.errors.append("CacheHitRateDrop should have severity 'warning'")

        # Check category
        if rule['labels']['category'] != 'performance':
            self.errors.append("CacheHitRateDrop should have category 'performance'")

        # Check it uses cache metrics
        if 'cache_hits_total' not in rule['expr']:
            self.errors.append("CacheHitRateDrop should use cache_hits_total metric")

        if 'cache_misses_total' not in rule['expr']:
            self.errors.append("CacheHitRateDrop should use cache_misses_total metric")

        # Check for hit rate calculation (hits / (hits + misses))
        if '/' not in rule['expr'] or '+' not in rule['expr']:
            self.errors.append("CacheHitRateDrop should calculate hit rate as hits / (hits + misses)")

        # Check threshold (should be < 0.5 or 50%)
        if '< 0.5' not in rule['expr'] and '<0.5' not in rule['expr']:
            self.warnings.append("CacheHitRateDrop threshold should be < 0.5 (50%)")

        # Check 'for' duration
        if rule['for'] != '10m':
            self.warnings.append(f"CacheHitRateDrop 'for' should be '10m', got '{rule['for']}'")

        # Check annotation mentions cache
        description = rule['annotations'].get('description', '')
        if 'cache' not in description.lower():
            self.warnings.append("CacheHitRateDrop description should mention cache")

        return len(self.errors) == 0

    def test_template_variables(self) -> bool:
        """Test that alerts use proper Prometheus template variables"""
        group = self.rules_data['groups'][0]
        rules = group.get('rules', [])

        for rule in rules:
            annotations = rule.get('annotations', {})
            labels = rule.get('labels', {})

            # Check annotations use template variables where appropriate
            for key, value in annotations.items():
                if isinstance(value, str):
                    # Check for proper template variable syntax
                    if '$labels.' in value and '{{ $labels.' not in value:
                        self.errors.append(f"Alert '{rule['alert']}' annotation '{key}' uses incorrect template syntax")

                    # Service label should be referenced in summary/description
                    if key in ['summary', 'description'] and 'service' in value.lower():
                        if '{{ $labels.service }}' not in value:
                            self.warnings.append(f"Alert '{rule['alert']}' {key} should use {{{{ $labels.service }}}} template variable")

        return len(self.errors) == 0

    def run_all_tests(self) -> bool:
        """Run all tests and return True if all pass"""
        if not self.load_rules():
            return False

        self.test_file_structure()
        self.test_group_structure()
        self.test_required_alerts()
        self.test_alert_structure()
        self.test_prometheus_expression_syntax()
        self.test_template_variables()
        self.test_latency_anomaly_rule()
        self.test_error_pattern_anomaly_rule()
        self.test_traffic_drop_anomaly_rule()
        self.test_cache_hit_rate_drop_rule()

        return len(self.errors) == 0

    def print_results(self):
        """Print test results"""
        print("\n" + "="*60)
        print("ANOMALY DETECTION RULES TEST RESULTS")
        print("="*60)

        if self.errors:
            print(f"\n❌ FAILED: {len(self.errors)} error(s)")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ PASSED: All tests passed!")

        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)} warning(s)")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("="*60 + "\n")


def main():
    """Main test runner"""
    rules_file = Path(__file__).parent.parent / 'config' / 'trace-analysis-rules.yaml'
    tester = AnomalyDetectionRuleTest(rules_file)

    success = tester.run_all_tests()
    tester.print_results()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
