# services/nemoclaw-orchestrator/policy/rules.py
from policy.engine import PolicyRule, PolicyAction

CHIMERA_POLICIES = [
    # Safety Filter - highest priority
    PolicyRule(
        name="safety-first",
        agent="safety-filter",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=True
    ),

    # Sentiment - free to run
    PolicyRule(
        name="sentiment-free",
        agent="sentiment-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),

    # SceneSpeak - sanitize long content
    PolicyRule(
        name="dialogue-safety",
        agent="scenespeak-agent",
        action=PolicyAction.SANITIZE,
        conditions={},
        output_filter=True
    ),

    # Autonomous - escalate dangerous commands
    PolicyRule(
        name="autonomous-danger",
        agent="autonomous-agent",
        action=PolicyAction.DENY,
        conditions={"command_contains": ["rm", "delete", "format"]},
        output_filter=True
    ),

    PolicyRule(
        name="autonomous-escalate",
        agent="autonomous-agent",
        action=PolicyAction.ESCALATE,
        conditions={"complexity": "high"},
        output_filter=True
    ),

    # Captioning - allow
    PolicyRule(
        name="captioning-allow",
        agent="captioning-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),

    # BSL - allow
    PolicyRule(
        name="bsl-allow",
        agent="bsl-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),
]
