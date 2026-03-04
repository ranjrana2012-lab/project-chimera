#!/usr/bin/env python3
"""Calculate and report error budget status for all services"""

import requests
import sys
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9090"

SLO_TARGETS = {
    "openclaw-orchestrator": 0.999,
    "scenespeak-agent": 0.995,
    "captioning-agent": 0.995,
    "bsl-agent": 0.99,
    "safety-filter": 0.999,
    "operator-console": 0.995,
}

def query_prometheus(query: str) -> float:
    """Query Prometheus and return value"""
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query}
    )
    response.raise_for_status()
    data = response.json()

    if data["data"]["result"]:
        return float(data["data"]["result"][0]["value"][1])
    return 0.0

def calculate_error_budget(service: str) -> dict:
    """Calculate error budget for a service"""
    slo_target = SLO_TARGETS[service]

    # Get actual success rate
    actual_success = query_prometheus(f'slo:{service.replace("-", "_")}_success_rate:30d')

    # Calculate error budget remaining
    error_budget = (slo_target - actual_success) / slo_target

    # Calculate burn rate
    allowed_error_rate = 1 - slo_target
    current_error_rate = 1 - actual_success
    burn_rate = current_error_rate / allowed_error_rate if allowed_error_rate > 0 else 0

    return {
        "service": service,
        "slo_target": slo_target,
        "actual_success": actual_success,
        "error_budget_remaining": error_budget,
        "burn_rate": burn_rate,
        "status": "healthy" if error_budget > 0.10 else ("warning" if error_budget > 0.05 else "critical")
    }

def main():
    """Main function"""
    print(f"Error Budget Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    budgets = []
    for service in SLO_TARGETS.keys():
        try:
            budget = calculate_error_budget(service)
            budgets.append(budget)
        except Exception as e:
            print(f"Error calculating budget for {service}: {e}")

    # Sort by burn rate (highest first)
    budgets.sort(key=lambda x: x["burn_rate"], reverse=True)

    # Print report
    print(f"{'Service':<25} {'SLO':>8} {'Actual':>8} {'Budget':>10} {'Burn':>8} {'Status':>10}")
    print("-" * 80)

    for budget in budgets:
        status_symbol = {"healthy": "OK", "warning": "WARN", "critical": "CRIT"}[budget["status"]]
        print(f"{budget['service']:<25} {budget['slo_target']:>8.1%} "
              f"{budget['actual_success']:>8.1%} {budget['error_budget_remaining']:>10.1%} "
              f"{budget['burn_rate']:>8.1f}x {status_symbol} {budget['status']}")

    print("\nSummary:")
    critical = [b for b in budgets if b["status"] == "critical"]
    warning = [b for b in budgets if b["status"] == "warning"]

    if critical:
        print(f"  CRITICAL: {len(critical)} services exhausted error budget")
    if warning:
        print(f"  WARNING: {len(warning)} services have low budget")
    if not critical and not warning:
        print(f"  All services healthy")

    return 0 if not critical else 1

if __name__ == "__main__":
    sys.exit(main())
