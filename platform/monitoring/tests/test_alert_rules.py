#!/usr/bin/env python3
"""
Test suite for critical alert rules.
Validates YAML structure, required fields, and rule expressions.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any


class AlertRuleTest:
    """Test class for alert rules validation"""

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

        if group['name'] != 'chimera.critical':
            self.errors.append(f"Group name should be 'chimera.critical', got '{group['name']}'")
            return False

        return True

    def test_required_alerts(self) -> bool:
        """Test that all required alerts are present"""
        required_alerts = {
            'ServiceDown',
            'HighErrorRate',
            'PodCrashLooping',
            'HighMemoryUsage',
            'HighCPUUsage'
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

            # Labels must include severity
            if 'severity' not in rule['labels']:
                self.errors.append(f"Alert '{rule['alert']}' missing severity label")
                return False

            # Annotations must include summary
            if 'summary' not in rule['annotations']:
                self.errors.append(f"Alert '{rule['alert']}' missing summary annotation")
                return False

            # Validate expr is a string
            if not isinstance(rule['expr'], str):
                self.errors.append(f"Alert '{rule['alert']}' expr must be a string")
                return False

        return True

    def test_specific_rules(self) -> bool:
        """Test specific alert rule configurations"""
        group = self.rules_data['groups'][0]
        rules_by_name = {rule['alert']: rule for rule in group.get('rules', [])}

        # Test ServiceDown
        if 'ServiceDown' in rules_by_name:
            rule = rules_by_name['ServiceDown']
            if rule['labels']['severity'] != 'critical':
                self.errors.append("ServiceDown should have severity 'critical'")
            if 'up{' not in rule['expr']:
                self.errors.append("ServiceDown expr should check 'up' metric")

        # Test HighErrorRate
        if 'HighErrorRate' in rules_by_name:
            rule = rules_by_name['HighErrorRate']
            if rule['labels']['severity'] != 'critical':
                self.errors.append("HighErrorRate should have severity 'critical'")
            if 'http_requests_total' not in rule['expr']:
                self.errors.append("HighErrorRate expr should check 'http_requests_total' metric")

        # Test PodCrashLooping
        if 'PodCrashLooping' in rules_by_name:
            rule = rules_by_name['PodCrashLooping']
            if rule['labels']['severity'] != 'critical':
                self.errors.append("PodCrashLooping should have severity 'critical'")
            if 'kube_pod_container_status_restarts_total' not in rule['expr']:
                self.errors.append("PodCrashLooping expr should check restarts")

        # Test HighMemoryUsage
        if 'HighMemoryUsage' in rules_by_name:
            rule = rules_by_name['HighMemoryUsage']
            if rule['labels']['severity'] not in ['warning', 'critical']:
                self.errors.append("HighMemoryUsage should have severity 'warning' or 'critical'")
            if 'container_memory_usage_bytes' not in rule['expr']:
                self.errors.append("HighMemoryUsage expr should check memory usage")

        # Test HighCPUUsage
        if 'HighCPUUsage' in rules_by_name:
            rule = rules_by_name['HighCPUUsage']
            if rule['labels']['severity'] not in ['warning', 'critical']:
                self.errors.append("HighCPUUsage should have severity 'warning' or 'critical'")
            if 'container_cpu_usage_seconds_total' not in rule['expr']:
                self.errors.append("HighCPUUsage expr should check CPU usage")

        return len(self.errors) == 0

    def run_all_tests(self) -> bool:
        """Run all tests and return True if all pass"""
        if not self.load_rules():
            return False

        self.test_file_structure()
        self.test_group_structure()
        self.test_required_alerts()
        self.test_alert_structure()
        self.test_specific_rules()

        return len(self.errors) == 0

    def print_results(self):
        """Print test results"""
        print("\n" + "="*60)
        print("ALERT RULES TEST RESULTS")
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
    rules_file = Path(__file__).parent.parent / 'config' / 'alert-rules-critical.yaml'
    tester = AlertRuleTest(rules_file)

    success = tester.run_all_tests()
    tester.print_results()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
