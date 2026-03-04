# Production Observability Enhancement Design

**Date:** 2026-03-04
**Version:** 1.0
**Status:** Approved
**Author:** Claude (with user input)

---

## Executive Summary

This design outlines a 4-phase rollout to transform Project Chimera's monitoring from development-focused to production-ready observability. The implementation will deliver production alerting, business metrics dashboards, SLO-based reliability enforcement, and deep distributed tracing capabilities.

**Timeline:** 4 weeks
**Approach:** Phased rollout with incremental value delivery

---

## Goals

1. **Production Alerting:** Intelligent alert routing with on-call integration
2. **Business Visibility:** Real-time dashboards for live theatre operations
3. **Reliability Framework:** SLOs, error budgets, and automated enforcement
4. **Deep Observability:** Service mapping, trace analysis, and anomaly detection

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Production Observability Stack                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Phase 1: Alerting Foundation                   │  │
│  │  Prometheus ──► AlertManager ──► Slack/PagerDuty/Email/Webhook    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   Phase 2: Business Visibility                    │  │
│  │  Service Metrics ──► Grafana Dashboards (Show, Dialogue, Audience)│  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Phase 3: Reliability Framework                  │  │
│  │  SLIs ──► SLOs ──► Error Budget ──► Burn Rate Alerts             │  │
│  │                └─► Quality Gate Enforcement                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   Phase 4: Deep Observability                     │  │
│  │  OpenTelemetry ──► Jaeger ──► Service Maps + Trace Analysis        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Alerting Foundation (Week 1)

### Components

**AlertManager Configuration**
- Route alerts by severity (critical → Slack, future: PagerDuty)
- Silence windows for maintenance
- Inhibition rules to prevent alert storms
- Notification templates with runbook links

**Critical Alert Rules**
```yaml
# Service down (1 minute)
- alert: ServiceDown
  expr: up{job="chimera-services"} == 0
  for: 1m
  severity: critical

# High error rate (5% threshold)
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.05
  for: 5m
  severity: critical

# Pod crash looping
- alert: PodCrashLooping
  expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
  severity: critical

# High memory usage
- alert: HighMemoryUsage
  expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
  for: 5m
  severity: warning

# High CPU usage
- alert: HighCPUUsage
  expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
  for: 10m
  severity: warning
```

### On-Call Procedures
- On-call rotation documentation
- Escalation policies
- Handoff documentation
- "Hero mode" procedures during live shows

### Files
- `platform/monitoring/config/alertmanager.yaml`
- `platform/monitoring/config/alert-rules-critical.yaml`
- `platform/monitoring/config/alert-routes.yaml`
- `docs/runbooks/alerts.md` (update)
- `docs/runbooks/on-call.md` (new)
- `scripts/silence-alerts.sh`

### Success Criteria
- Critical alerts route to Slack within 10 seconds
- Alerts link to relevant runbooks
- On-call documentation complete
- Maintenance windows can be silenced

---

## Phase 2: Business Visibility (Week 2)

### Business Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `show_state` | Gauge | Current show state (0=idle, 1=active) | - |
| `dialogue_quality_score` | Gauge | Average coherence score (0-1) | >0.8 |
| `audience_sentiment` | Gauge | Current sentiment (-1 to 1) | >0.3 |
| `lines_per_minute` | Counter | Dialogue generation rate | 10-20 |
| `caption_latency_ms` | Histogram | Time from speech to caption | <2000ms p95 |
| `bsl_active_sessions` | Gauge | Number of active BSL sessions | - |
| `safety_blocks_per_hour` | Counter | Content moderation blocks | <5 |

### Dashboards

**1. Show Overview Dashboard**
- Show state and timer
- Service health grid
- Audience sentiment (last 5 min)
- Recent alerts count
- Active issues

**2. Dialogue Quality Dashboard**
- Lines generated per minute
- Average token count per line
- Adapter performance comparison
- Cache hit rate
- Dialogue diversity score

**3. Audience Engagement Dashboard**
- Sentiment trend over show duration
- Peak engagement moments
- Caption usage rate
- BSL avatar active sessions

### Service Instrumentation

```python
# SceneSpeak Agent
dialogue_quality = Gauge('scenespeak_dialogue_quality',
                         'Dialogue coherence score',
                         ['adapter'])
lines_generated = Counter('scenespeak_lines_generated_total',
                         'Total lines generated',
                         ['show_id'])

# Sentiment Agent
audience_sentiment = Gauge('sentiment_audience_avg',
                           'Average audience sentiment',
                           ['show_id', 'time_window'])

# Captioning Agent
caption_latency = Histogram('captioning_latency_seconds',
                           'Time from speech to caption')
```

### Files
- `services/*/src/metrics.py` (per service)
- `platform/monitoring/config/grafana-dashboards/show-overview.json`
- `platform/monitoring/config/grafana-dashboards/dialogue-quality.json`
- `platform/monitoring/config/grafana-dashboards/audience-engagement.json`
- `docs/runbooks/business-metrics.md`

### Success Criteria
- Show overview dashboard updates in real-time (<5s)
- All services export business metrics
- Dashboards accessible via Grafana
- Metrics documented in runbook

---

## Phase 3: Reliability Framework (Week 3)

### SLO Definitions

**Core Services**

| Service | SLO | SLI | Window | Error Budget |
|---------|-----|-----|--------|--------------|
| OpenClaw | 99.9% | Successful orchestrations / total | 30d rolling | 43.2min/month |
| SceneSpeak | 99.5% | Successful generations / total | 30d rolling | 3.6hrs/month |
| Captioning | 99.5% | Captions delivered / speech | 30d rolling | 3.6hrs/month |
| BSL | 99% | Successful translations / total | 30d rolling | 7.2hrs/month |
| Safety | 99.9% | Requests processed / total | 30d rolling | 43.2min/month |
| Console | 99.5% | Dashboard loads / requests | 30d rolling | 3.6hrs/month |

### Error Budget & Burn Rate

```
Burn Rate = (Current Error Rate) / (Allowed Error Rate)

Burn Rate 1x = On track
Burn Rate 2x = Warning (5m threshold)
Burn Rate 10x = Critical (1m threshold)
```

### SLO Quality Gate

```python
class SloQualityGate:
    def check_deployment_readiness(self, service: str) -> GateResult:
        slo_compliance = self.get_slo_compliance(service)
        error_budget_remaining = self.get_error_budget(service)

        if slo_compliance < 0.95:
            return GateResult(
                action="block",
                reason=f"SLO compliance at {slo_compliance:.1%}"
            )

        if error_budget_remaining < 0.10:
            return GateResult(
                action="block",
                reason=f"Error budget at {error_budget_remaining:.1%}"
            )

        return GateResult(action="allow")
```

### Files
- `platform/monitoring/config/slo-recording-rules.yaml`
- `platform/monitoring/config/slo-alerting-rules.yaml`
- `platform/monitoring/config/slo-dashboard.json`
- `platform/quality-gate/slo_gate.py`
- `docs/runbooks/slo-handbook.md`
- `docs/runbooks/slo-response.md`
- `scripts/calculate-error-budget.py`
- `scripts/slo-compliance-report.sh`

### Success Criteria
- All core services have defined SLOs
- SLI recording rules deployed
- Error budget alerts configured
- Quality gate enforces SLO compliance
- Weekly SLO compliance report automated

---

## Phase 4: Deep Observability (Week 4)

### Enhanced Tracing

**Service Dependency Mapping**
- Auto-generated service topology
- Request flow visualization
- Latency heatmap between services
- Error rate overlay

**Span Enrichment**
```python
span.set_attributes({
    "show.id": show_id,
    "scene.number": scene_number,
    "cache.hit": cache_hit,
    "adapter.name": adapter_name,
    "tokens.input": input_tokens,
    "tokens.output": output_tokens,
    "dialogue.lines_count": len(lines),
    "safety.action": safety_action,
    "sentiment.score": sentiment_score
})
```

**Anomaly Detection**
```yaml
# Latency anomaly - sudden spike
- alert: LatencyAnomalyDetected
  expr: |
    (rate(request_duration_seconds_sum{service="scenespeak"}[5m]) /
     rate(request_duration_seconds_count{service="scenespeak"}[5m])) >
    (avg_over_time(
      rate(request_duration_seconds_sum[1h]) /
      rate(request_duration_seconds_count[1h])) * 2)
```

**Trace Analysis Service**
```python
class TraceAnalyzer:
    def analyze_trace(self, trace_id: str) -> TraceReport:
        # Check for slow spans
        # Check for missing spans
        # Check error propagation
        # Calculate quality score
        return TraceReport(...)
```

### Files
- `services/*/src/tracing.py`
- `services/*/src/span_enrichment.py`
- `platform/monitoring/config/jaeger-sampling.yaml`
- `platform/monitoring/config/trace-analysis-rules.yaml`
- `docs/runbooks/distributed-tracing.md`
- `docs/runbooks/performance-analysis.md`
- `scripts/analyze-trace.py`
- `scripts/dependency-graph.py`
- `platform/monitoring/trace-analyzer/analyzer.py`

### Success Criteria
- All services emit spans with business context
- Service dependency map auto-generated
- Jaeger dashboards accessible
- Anomaly detection rules deployed
- Trace analysis tool operational

---

## Implementation Sequence

### Week 1: Alerting Foundation
1. Deploy AlertManager
2. Configure routing and silencing
3. Create critical alert rules
4. Document on-call procedures
5. Test alert flow

### Week 2: Business Visibility
1. Add business metrics to services
2. Create Grafana dashboards
3. Test metric collection
4. Document metrics

### Week 3: Reliability Framework
1. Define SLOs for each service
2. Create SLI recording rules
3. Set up error budget tracking
4. Configure SLO quality gate
5. Test deployment blocking

### Week 4: Deep Observability
1. Add OpenTelemetry instrumentation
2. Configure Jaeger sampling
3. Set up trace analysis
4. Create anomaly detection rules
5. Generate dependency maps

---

## Dependencies

**Required:**
- Prometheus 2.45+
- Grafana 10.0+
- Jaeger 1.50+
- AlertManager 0.26+

**Services:**
- All core services running
- Platform services deployed
- Basic monitoring operational

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alert fatigue | High | Start with critical alerts only, tune thresholds |
| Business metric accuracy | Medium | Validate metrics against show logs |
| SLO targets too aggressive | High | Use 30-day rolling windows, adjust as needed |
| Trace overhead | Low | Sampling strategy, async export |
| On-call burnout | Medium | Clear escalation, rotation limits |

---

## Rollout Plan

1. **Staging Environment First** - Test all phases in staging
2. **Phased Service Rollout** - Start with 2-3 core services
3. **Gradual Alert Enablement** - Start with monitoring-only, then enable actions
4. **SLO Calibration Period** - 2 weeks to tune targets before enforcement
5. **On-Call Training** - Ensure team familiar with procedures before go-live

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| MTTD (Mean Time To Detect) | < 2 minutes | Alert to acknowledgment |
| MTTR (Mean Time To Resolve) | < 15 minutes | Acknowledgment to resolution |
| False alert rate | < 10% | Alerts that don't require action |
| Dashboard accuracy | > 95% | Show state matches reality |
| SLO compliance | All services | 30-day rolling SLOs met |

---

## Next Steps

Upon approval:
1. Create detailed implementation plan using `superpowers:writing-plans`
2. Set up staging environment for testing
3. Begin Phase 1 implementation
4. Weekly progress reviews

---

**Design Status:** Approved
**Ready for Implementation Planning:** Yes

---

*Production Observability Enhancement Design*
*Project Chimera v3.0.0*
*March 2026*
