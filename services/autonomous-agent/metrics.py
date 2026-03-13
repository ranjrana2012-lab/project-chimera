"""Prometheus metrics for autonomous-agent service."""

from prometheus_client import Counter, Histogram, Gauge, Info
import os


def init_service_info(service_name: str, version: str):
    """Initialize service info metric."""
    service_info = Info(
        'autonomous_agent_service',
        'Autonomous Agent Service information'
    )
    service_info.info({
        'service_name': service_name,
        'version': version,
        'hostname': os.uname().nodename
    })
    return service_info


# Task execution metrics
task_executions = Counter(
    'autonomous_agent_task_executions_total',
    'Total number of task executions',
    ['task_type', 'status']
)

task_duration = Histogram(
    'autonomous_agent_task_duration_seconds',
    'Task execution duration in seconds',
    ['task_type']
)

retry_count = Counter(
    'autonomous_agent_retries_total',
    'Total number of retry attempts',
    ['task_id']
)

active_tasks = Gauge(
    'autonomous_agent_active_tasks',
    'Number of currently active tasks'
)

context_tokens = Gauge(
    'autonomous_agent_context_tokens',
    'Current context token count'
)

gsd_phase_duration = Histogram(
    'autonomous_agent_gsd_phase_duration_seconds',
    'GSD phase duration in seconds',
    ['phase']  # discuss, plan, execute, verify
)


def record_task_execution(task_type: str, status: str):
    """Record a task execution."""
    task_executions.labels(task_type=task_type, status=status).inc()


def record_task_duration(task_type: str, duration: float):
    """Record task execution duration."""
    task_duration.labels(task_type=task_type).observe(duration)


def record_retry(task_id: str):
    """Record a retry attempt."""
    retry_count.labels(task_id=task_id).inc()


def increment_active_tasks():
    """Increment active task count."""
    active_tasks.inc()


def decrement_active_tasks():
    """Decrement active task count."""
    active_tasks.dec()


def update_context_tokens(count: int):
    """Update context token count."""
    context_tokens.set(count)


def record_gsd_phase(phase: str, duration: float):
    """Record GSD phase duration."""
    gsd_phase_duration.labels(phase=phase).observe(duration)
