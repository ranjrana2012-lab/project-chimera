# services/nemoclaw-orchestrator/tests/unit/test_policy_engine.py
import pytest
from policy.engine import PolicyEngine, PolicyAction, PolicyRule, PolicyResult
from policy.rules import CHIMERA_POLICIES

class TestPolicyEngine:
    def test_engine_initializes_with_policies(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        assert len(engine.policies) > 0

    def test_check_input_returns_allow_for_safe_sentiment(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        result = engine.check_input(
            agent="sentiment-agent",
            skill="analyze_sentiment",
            input_data={"text": "happy message"}
        )
        assert result.action == PolicyAction.ALLOW

    def test_check_input_returns_deny_for_dangerous_command(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        result = engine.check_input(
            agent="autonomous-agent",
            skill="execute",
            input_data={"command": "rm -rf /"}
        )
        assert result.action == PolicyAction.DENY
