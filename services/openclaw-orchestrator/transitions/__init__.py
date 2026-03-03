"""
Transition trigger system for OpenClaw Orchestrator.

This package provides time-based, event-based, and manual transition triggers
for scene management.
"""

from transitions.time_triggers import (
    TimeTriggerType,
    TimeTriggerConfig,
    TimeTrigger,
    TimeTriggerScheduler
)

from transitions.event_triggers import (
    EventType,
    EventCondition,
    EventTriggerConfig,
    EventTrigger,
    EventTriggerScheduler
)

from transitions.manual_triggers import (
    ManualTransitionRequest,
    ManualTriggerConfig,
    ManualTrigger,
    ManualTriggerRegistry,
    TransitionRequestValidator,
    get_registry,
    create_manual_transition_request
)

from transitions.transition_effects import (
    TransitionEffectConfig,
    TransitionEffect,
    TransitionEffectExecutor,
    EffectState,
    get_executor
)

from transitions.agent_handoff import (
    AgentHandoffConfig,
    AgentHandoff,
    HandoffResult,
    HandoffState,
    AgentHandoffOrchestrator,
    AgentStateSnapshot
)

# Re-export TriggerState from manual_triggers
from transitions.manual_triggers import TriggerState

__all__ = [
    "TimeTriggerType",
    "TransitionType",
    "TimeTriggerConfig",
    "TimeTrigger",
    "TimeTriggerScheduler",
    "EventType",
    "EventCondition",
    "EventTriggerConfig",
    "EventTrigger",
    "EventTriggerScheduler",
    "ManualTransitionRequest",
    "ManualTriggerConfig",
    "ManualTrigger",
    "ManualTriggerRegistry",
    "TransitionRequestValidator",
    "get_registry",
    "create_manual_transition_request",
    "TransitionEffectConfig",
    "TransitionEffect",
    "TransitionEffectExecutor",
    "EffectState",
    "get_executor",
    "TriggerState",
    "AgentHandoffConfig",
    "AgentHandoff",
    "HandoffResult",
    "HandoffState",
    "AgentHandoffOrchestrator",
    "AgentStateSnapshot"
]
