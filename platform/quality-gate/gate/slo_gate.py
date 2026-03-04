"""
SLO-based quality gate for deployment blocking.

This module provides a quality gate that evaluates service deployment readiness
based on Service Level Objective (SLO) compliance and error budget remaining.
"""

from dataclasses import dataclass
from typing import Optional
import requests
import logging

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """Result of SLO quality gate evaluation.

    Attributes:
        action: The gate action - "allow" or "block"
        reason: Human-readable explanation of the decision
        slo_compliance: Current SLO compliance rate (0-1)
        error_budget_remaining: Remaining error budget (0-1)
    """
    action: str  # "allow", "block"
    reason: str
    slo_compliance: Optional[float] = None
    error_budget_remaining: Optional[float] = None


class SloQualityGate:
    """SLO-based quality gate for deployment blocking.

    This gate evaluates whether a service is ready for deployment by checking:
    1. SLO compliance meets the required threshold
    2. Error budget remaining is above the minimum threshold

    Example:
        >>> gate = SloQualityGate()
        >>> result = gate.check_deployment_readiness("scenespeak-agent")
        >>> if result.action == "allow":
        ...     print("Service is ready for deployment")
        ... else:
        ...     print(f"Deployment blocked: {result.reason}")
    """

    SLO_THRESHOLDS = {
        "openclaw-orchestrator": {"slo": 0.999, "budget": 0.10},
        "scenespeak-agent": {"slo": 0.995, "budget": 0.10},
        "captioning-agent": {"slo": 0.995, "budget": 0.10},
        "bsl-agent": {"slo": 0.99, "budget": 0.10},
        "safety-filter": {"slo": 0.999, "budget": 0.10},
        "operator-console": {"slo": 0.995, "budget": 0.10},
    }

    def __init__(self, prometheus_url: str = "http://prometheus.shared.svc.cluster.local:9090"):
        """Initialize the SLO quality gate.

        Args:
            prometheus_url: URL of the Prometheus server for querying SLO metrics
        """
        self.prometheus_url = prometheus_url

    def check_deployment_readiness(self, service: str) -> GateResult:
        """Check if service is ready for deployment based on SLO compliance.

        Args:
            service: The service name to evaluate (e.g., "scenespeak-agent")

        Returns:
            GateResult with action ("allow" or "block"), reason, and metrics
        """
        # Get SLO compliance from Prometheus
        slo_compliance = self._get_slo_compliance(service)

        # Get error budget remaining
        error_budget = self._get_error_budget(service)

        # Get thresholds for this service
        thresholds = self.SLO_THRESHOLDS.get(
            service,
            {"slo": 0.99, "budget": 0.10}  # Default thresholds
        )

        # Check SLO compliance
        if slo_compliance < thresholds["slo"]:
            logger.warning(
                f"Deployment blocked for {service}: "
                f"SLO compliance {slo_compliance:.3%} < {thresholds['slo']:.3%}"
            )
            return GateResult(
                action="block",
                reason=(
                    f"SLO compliance at {slo_compliance:.1%}, "
                    f"below {thresholds['slo']:.1%} threshold"
                ),
                slo_compliance=slo_compliance,
                error_budget_remaining=error_budget
            )

        # Check error budget
        if error_budget < thresholds["budget"]:
            logger.warning(
                f"Deployment blocked for {service}: "
                f"Error budget {error_budget:.3%} < {thresholds['budget']:.3%}"
            )
            return GateResult(
                action="block",
                reason=(
                    f"Error budget at {error_budget:.1%}, "
                    f"below {thresholds['budget']:.1%} threshold"
                ),
                slo_compliance=slo_compliance,
                error_budget_remaining=error_budget
            )

        logger.info(
            f"Deployment allowed for {service}: "
            f"SLO {slo_compliance:.3%}, budget {error_budget:.3%}"
        )
        return GateResult(
            action="allow",
            reason=(
                f"SLO compliance ({slo_compliance:.1%}) "
                f"and budget ({error_budget:.1%}) are healthy"
            ),
            slo_compliance=slo_compliance,
            error_budget_remaining=error_budget
        )

    def _get_slo_compliance(self, service: str) -> float:
        """Get current SLO compliance from Prometheus.

        Args:
            service: The service name

        Returns:
            SLO compliance rate (0-1)
        """
        # Convert service name to metric format (replace hyphens with underscores)
        service_metric = service.replace("-", "_")
        query = f'slo:{service_metric}_success_rate:30d'

        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data["data"]["result"]:
                value = float(data["data"]["result"][0]["value"][1])
                logger.debug(f"SLO compliance for {service}: {value:.3%}")
                return value
            else:
                logger.warning(f"No SLO compliance data found for {service}")
                return 1.0  # Assume full compliance if no data

        except requests.RequestException as e:
            logger.error(f"Failed to query SLO compliance for {service}: {e}")
            return 1.0  # Fail open for safety during deployment

    def _get_error_budget(self, service: str) -> float:
        """Get remaining error budget from Prometheus.

        Args:
            service: The service name

        Returns:
            Remaining error budget (0-1)
        """
        query = f'slo:error_budget_remaining:30d{{service="{service}"}}'

        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data["data"]["result"]:
                value = float(data["data"]["result"][0]["value"][1])
                logger.debug(f"Error budget for {service}: {value:.3%}")
                return value
            else:
                logger.warning(f"No error budget data found for {service}")
                return 1.0  # Assume full budget if no data

        except requests.RequestException as e:
            logger.error(f"Failed to query error budget for {service}: {e}")
            return 1.0  # Fail open for safety during deployment
