"""Prometheus metrics for OpenClaw Orchestrator"""

from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry

# Create registry for custom metrics
registry = CollectorRegistry()

# Counters
skill_invocations_total = Counter(
    "openclaw_skill_invocations_total",
    "Total number of skill invocations",
    ["skill_name", "status"],
    registry=registry,
)

pipeline_executions_total = Counter(
    "openclaw_pipeline_executions_total",
    "Total number of pipeline executions",
    ["pipeline_id", "status"],
    registry=registry,
)

cache_hits_total = Counter(
    "openclaw_cache_hits_total",
    "Total number of cache hits",
    ["skill_name"],
    registry=registry,
)

cache_misses_total = Counter(
    "openclaw_cache_misses_total",
    "Total number of cache misses",
    ["skill_name"],
    registry=registry,
)

# Histograms
skill_invocation_duration_seconds = Histogram(
    "openclaw_skill_invocation_duration_seconds",
    "Skill invocation duration in seconds",
    ["skill_name"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry,
)

pipeline_execution_duration_seconds = Histogram(
    "openclaw_pipeline_execution_duration_seconds",
    "Pipeline execution duration in seconds",
    ["pipeline_id"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)

# Gauges
active_pipelines = Gauge(
    "openclaw_active_pipelines",
    "Number of currently active pipelines",
    registry=registry,
)

loaded_skills = Gauge(
    "openclaw_loaded_skills",
    "Number of loaded skills",
    registry=registry,
)

enabled_skills = Gauge(
    "openclaw_enabled_skills",
    "Number of enabled skills",
    registry=registry,
)

skill_cache_size = Gauge(
    "openclaw_skill_cache_size",
    "Number of items in skill cache",
    registry=registry,
)

# Summaries
skill_invocation_latency_summary = Summary(
    "openclaw_skill_invocation_latency_summary",
    "Summary of skill invocation latency",
    ["skill_name"],
    registry=registry,
)

# Expose metrics as a dictionary for easy access
metrics_registry = {
    "counters": {
        "skill_invocations_total": skill_invocations_total,
        "pipeline_executions_total": pipeline_executions_total,
        "cache_hits_total": cache_hits_total,
        "cache_misses_total": cache_misses_total,
    },
    "histograms": {
        "skill_invocation_duration_seconds": skill_invocation_duration_seconds,
        "pipeline_execution_duration_seconds": pipeline_execution_duration_seconds,
    },
    "gauges": {
        "active_pipelines": active_pipelines,
        "loaded_skills": loaded_skills,
        "enabled_skills": enabled_skills,
        "skill_cache_size": skill_cache_size,
    },
    "summaries": {
        "skill_invocation_latency_summary": skill_invocation_latency_summary,
    },
    "registry": registry,
}


def record_skill_invocation(skill_name: str, status: str, duration: float) -> None:
    """Record a skill invocation metric."""
    skill_invocations_total.labels(skill_name=skill_name, status=status).inc()
    skill_invocation_duration_seconds.labels(skill_name=skill_name).observe(duration)
    skill_invocation_latency_summary.labels(skill_name=skill_name).observe(duration)


def record_cache_hit(skill_name: str, hit: bool) -> None:
    """Record a cache access metric."""
    if hit:
        cache_hits_total.labels(skill_name=skill_name).inc()
    else:
        cache_misses_total.labels(skill_name=skill_name).inc()


def record_pipeline_execution(pipeline_id: str, status: str, duration: float) -> None:
    """Record a pipeline execution metric."""
    pipeline_executions_total.labels(pipeline_id=pipeline_id, status=status).inc()
    pipeline_execution_duration_seconds.labels(pipeline_id=pipeline_id).observe(duration)
