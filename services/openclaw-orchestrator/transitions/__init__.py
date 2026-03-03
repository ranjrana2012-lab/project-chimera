"""
Transition trigger system for OpenClaw Orchestrator.

This package provides time-based, event-based, and manual transition triggers
for scene management.
"""

from transitions.time_triggers import (
    TimeTriggerType,
    TransitionType,
    TimeTriggerConfig,
    TimeTrigger,
    TimeTriggerScheduler
)

from transitions.event_triggers import (
    EventType,
    EventCondition,
    EventTriggerConfig,
    EventTrigger,
    EventTriggerScheduler,
    TriggerState
)

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
    "TriggerState"
]
