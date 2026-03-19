# services/nemoclaw-orchestrator/policy/engine.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    SANITIZE = "sanitize"
    ESCALATE = "escalate"

@dataclass
class PolicyResult:
    action: PolicyAction
    reason: str
    rule_name: Optional[str] = None
    sanitization_rules: Optional[Dict[str, Any]] = None

@dataclass
class PolicyRule:
    name: str
    agent: str
    action: PolicyAction
    conditions: Dict[str, Any]
    output_filter: bool = True

class PolicyEngine:
    def __init__(self, policies: List[PolicyRule]):
        self.policies = policies
        self._build_agent_index()

    def _build_agent_index(self):
        """Build index for fast agent lookup"""
        self._agent_policies: Dict[str, List[PolicyRule]] = {}
        for policy in self.policies:
            if policy.agent not in self._agent_policies:
                self._agent_policies[policy.agent] = []
            self._agent_policies[policy.agent].append(policy)

    def check_input(
        self,
        agent: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> PolicyResult:
        """Check if input complies with policy"""

        # Get applicable policies for this agent
        applicable = self._agent_policies.get(agent, [])

        if not applicable:
            # No specific policy - allow by default
            return PolicyResult(
                action=PolicyAction.ALLOW,
                reason="No specific policy applies"
            )

        # Check policies in priority order (assume already sorted)
        for policy in applicable:
            if self._conditions_match(policy.conditions, input_data):
                return PolicyResult(
                    action=policy.action,
                    reason=f"Policy '{policy.name}' matched",
                    rule_name=policy.name
                )

        # No policy matched - default to allow
        return PolicyResult(
            action=PolicyAction.ALLOW,
            reason="No policy conditions matched"
        )

    def _conditions_match(
        self,
        conditions: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> bool:
        """Check if input matches policy conditions"""
        # For now, empty conditions = always match
        if not conditions:
            return True

        # Simple key-value matching (extend for complex conditions)
        for key, value in conditions.items():
            if key == "command_contains":
                # Check if command contains dangerous strings
                command = input_data.get("command", "")
                if any(dangerous in command.lower() for dangerous in value):
                    return True
                return False
            elif key not in input_data:
                return False
            elif input_data[key] != value:
                return False

        return True

    async def sanitize_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sanitize input data"""
        from policy.filters import InputSanitizer
        sanitizer = InputSanitizer()
        return await sanitizer.sanitize(input_data)

    async def filter_output(
        self,
        agent: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter output through policy"""
        from policy.filters import OutputFilter
        filter = OutputFilter()
        return await filter.filter(response, agent)
