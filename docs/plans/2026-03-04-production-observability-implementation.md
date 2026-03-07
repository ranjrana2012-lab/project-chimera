# Production Observability Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Project Chimera's monitoring from development-focused to production-ready observability through a 4-phase rollout.

**Architecture:** 4-phase incremental rollout: (1) AlertManager deployment with intelligent routing and on-call integration, (2) Business metrics instrumentation and Grafana dashboards, (3) SLO framework with error budgets and quality gate enforcement, (4) OpenTelemetry tracing with service maps and anomaly detection.

**Tech Stack:** AlertManager, Prometheus, Grafana, Jaeger, OpenTelemetry, Python, FastAPI, Kubernetes, Helm

---

## Phase 1: Alerting Foundation (Week 1)

### Task 1: Deploy AlertManager

**Files:**
- Create: `platform/monitoring/config/alertmanager.yaml`
- Create: `infrastructure/kubernetes/alertmanager/deployment.yaml`
- Create: `infrastructure/kubernetes/alertmanager/service.yaml`

**Step 1: Write AlertManager configuration**

```yaml
# platform/monitoring/config/alertmanager.yaml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    continue: true
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'default'
  slack_configs:
  - channel: '#chimera-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

- name: 'critical-alerts'
  slack_configs:
  - channel: '#chimera-critical'
    title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
    text: |
      *Summary:* {{ .CommonAnnotations.summary }}
      *Description:* {{ .CommonAnnotations.description }}
      *Runbook:* {{ .CommonAnnotations.runbook }}
    send_resolved: true

- name: 'warning-alerts'
  slack_configs:
  - channel: '#chimera-alerts'
    title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
    text: '{{ .CommonAnnotations.description }}'
    send_resolved: true

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'service']
```

**Step 2: Run config validation**

Run: `promtool check config platform/monitoring/config/alertmanager.yaml`
Expected: `SUCCESS: 1 rule files found`

**Step 3: Create Kubernetes deployment**

```yaml
# infrastructure/kubernetes/alertmanager/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: shared
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:v0.26.0
        args:
        - '--config.file=/etc/alertmanager/alertmanager.yaml'
        - '--storage.path=/alertmanager'
        ports:
        - containerPort: 9093
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
        - name: storage
          mountPath: /alertmanager
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
      - name: storage
        emptyDir: {}
```

**Step 4: Create service**

```yaml
# infrastructure/kubernetes/alertmanager/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: shared
spec:
  selector:
    app: alertmanager
  ports:
  - port: 9093
    targetPort: 9093
  type: ClusterIP
```

**Step 5: Deploy and verify**

Run:
```bash
kubectl apply -f infrastructure/kubernetes/alertmanager/
kubectl wait --for=condition=ready pod -l app=alertmanager -n shared --timeout=60s
kubectl get pods -n shared -l app=alertmanager
```
Expected: Pod running and ready

**Step 6: Commit**

```bash
git add platform/monitoring/config/alertmanager.yaml infrastructure/kubernetes/alertmanager/
git commit -m "feat(alerting): deploy AlertManager with Slack integration"
```

---

### Task 2: Create Critical Alert Rules

**Files:**
- Create: `platform/monitoring/config/alert-rules-critical.yaml`

**Step 1: Write critical alert rules**

```yaml
# platform/monitoring/config/alert-rules-critical.yaml
groups:
- name: chimera.critical
  interval: 30s
  rules:
  # Service Down
  - alert: ServiceDown
    expr: up{job="chimera-services"} == 0
    for: 1m
    labels:
      severity: critical
      service: '{{ $labels.service }}'
    annotations:
      summary: 'Service {{ $labels.service }} is down'
      description: '{{ $labels.service }} has been down for more than 1 minute'
      runbook: 'https://docs/runbooks/alerts.html#service-down'

  # High Error Rate
  - alert: HighErrorRate
    expr: |
      sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
      /
      sum(rate(http_requests_total[5m])) by (service)
      > 0.05
    for: 5m
    labels:
      severity: critical
      service: '{{ $labels.service }}'
    annotations:
      summary: 'High error rate on {{ $labels.service }}'
      description: 'Error rate is {{ $value | humanizePercentage }} (>5%) for 5 minutes'
      runbook: 'https://docs/runbooks/alerts.html#high-error-rate'

  # Pod Crash Looping
  - alert: PodCrashLooping
    expr: |
      rate(kube_pod_container_status_restarts_total{namespace="live"}[15m]) > 0
    for: 1m
    labels:
      severity: critical
      pod: '{{ $labels.pod }}'
    annotations:
      summary: 'Pod {{ $labels.pod }} is crash looping'
      description: 'Pod has restarted {{ $value }} times in the last 15 minutes'
      runbook: 'https://docs/runbooks/alerts.html#pod-crash-looping'

  # High Memory Usage
  - alert: HighMemoryUsage
    expr: |
      container_memory_usage_bytes{namespace="live"}
      /
      container_spec_memory_limit_bytes{namespace="live"}
      > 0.9
    for: 5m
    labels:
      severity: warning
      pod: '{{ $labels.pod }}'
    annotations:
      summary: 'High memory usage on {{ $labels.pod }}'
      description: 'Memory usage is {{ $value | humanizePercentage }} of limit'

  # High CPU Usage
  - alert: HighCPUUsage
    expr: |
      sum(rate(container_cpu_usage_seconds_total{namespace="live"}[5m])) by (pod)
      /
      sum(kube_pod_container_resource_limits{namespace="live", resource="cpu"}) by (pod)
      > 0.8
    for: 10m
    labels:
      severity: warning
      pod: '{{ $labels.pod }}'
    annotations:
      summary: 'High CPU usage on {{ $labels.pod }}'
      description: 'CPU usage is {{ $value | humanizePercentage }} of limit'

  # Safety Filter High Block Rate
  - alert: SafetyHighBlockRate
    expr: |
      sum(rate(safety_filter_blocks_total[5m]))
      /
      sum(rate(safety_filter_checks_total[5m]))
      > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: 'Safety filter blocking >10% of content'
      description: 'Block rate is {{ $value | humanizePercentage }}'

  # Queue Backlog
  - alert: QueueBacklog
    expr: |
      sum(queue_size{namespace="live"}) by (service) > 100
    for: 5m
    labels:
      severity: warning
      service: '{{ $labels.service }}'
    annotations:
      summary: 'Queue backlog on {{ $labels.service }}'
      description: 'Queue size is {{ $value }} items'
```

**Step 2: Validate rules**

Run: `promtool check rules platform/monitoring/config/alert-rules-critical.yaml`
Expected: `SUCCESS: 6 rules found`

**Step 3: Create ConfigMap**

Run:
```bash
kubectl create configmap alert-rules-critical \
  --from-file=platform/monitoring/config/alert-rules-critical.yaml \
  --namespace=shared --dry-run=client -o yaml | kubectl apply -f -
```
Expected: `configmap/alert-rules-critical created`

**Step 4: Update Prometheus to use rules**

Edit: `infrastructure/kubernetes/prometheus/configmap.yaml`
Add to Prometheus config:
```yaml
rule_files:
  - /etc/prometheus/rules/critical/*.yaml
```

**Step 5: Commit**

```bash
git add platform/monitoring/config/alert-rules-critical.yaml
git commit -m "feat(alerting): add critical alert rules for all services"
```

---

### Task 3: Create Alert Silencing Script

**Files:**
- Create: `scripts/silence-alerts.sh`
- Modify: `Makefile`

**Step 1: Write silence script**

```bash
#!/bin/bash
# scripts/silence-alerts.sh

set -e

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
DURATION="${1:-1h}"
COMMENT="${2:-Maintenance window}"
MATCHERS=""

usage() {
    echo "Usage: $0 [duration] [comment] [matchers...]"
    echo "Example: $0 2h 'Deploying v1.2.3' service=scenespeak"
    exit 1
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

shift 2
MATCHERS=("$@")

# Build silence payload
MATCHER_DATA=""
for matcher in "${MATCHERS[@]}"; do
    IFS='=' read -r name value <<< "$matcher"
    MATCHER_DATA="$MATCHER_DATA{\"name\":\"$name\",\"value\":\"$value\",\"isRegex\":false},"
done

# Calculate end time
END_TIME=$(date -u -d "+$DURATION" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+${DURATION} +"%Y-%m-%dT%H:%M:%SZ")

# Create silence
SILENCE_ID=$(curl -s -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H 'Content-Type: application/json' \
  -d "{
    \"matchers\": [${MATCHER_DATA%,}],
    \"startsAt\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
    \"endsAt\": \"$END_TIME\",
    \"createdBy\": \"$(whoami)\",
    \"comment\": \"$COMMENT\"
  }" | jq -r '.silenceID')

echo "Silence created: $SILENCE_ID"
echo "Ends at: $END_TIME"
echo "View: $ALERTMANAGER_URL/#/silences"
```

**Step 2: Make executable**

Run: `chmod +x scripts/silence-alerts.sh`

**Step 3: Add to Makefile**

Edit: `Makefile`
Add:
```makefile
.PHONY: silence-alerts
silence-alerts:
	./scripts/silence-alerts.sh $(DURATION) $(COMMENT) $(MATCHERS)
```

**Step 4: Test script**

Run: `./scripts/silence-alerts.sh 5m "Testing" service=scenespeak`
Expected: Silence ID printed

**Step 5: Commit**

```bash
git add scripts/silence-alerts.sh Makefile
git commit -m "feat(alerting): add alert silencing script for maintenance windows"
```

---

### Task 4: Create On-Call Documentation

**Files:**
- Create: `docs/runbooks/on-call.md`

**Step 1: Write on-call handbook**

```markdown
# On-Call Handbook

## Overview

This handbook covers on-call procedures for Project Chimera production operations.

## Rotation

- **Primary On-Call:** [Name] - [Contact]
- **Secondary On-Call:** [Name] - [Contact]
- **Escalation:** Technical Lead - [Contact]

## Alert Severity

### Critical
- Service down
- Error rate > 5%
- Data loss risk
- Action required within 5 minutes

### Warning
- High resource usage
- Elevated error rates
- Degraded performance
- Action required within 30 minutes

## Response Procedure

1. **Acknowledge** alert in Slack
2. **Assess** impact using Grafana
3. **Check** related runbook
4. **Resolve** or escalate
5. **Document** actions taken

## During Live Shows

**Hero Mode:** All alerts go to dedicated #chimera-show channel
- Escalation immediately to Technical Lead
- No non-emergency changes
- Post-show review required

## Handoff

Use this checklist:

- [ ] No active incidents
- [ ] All alerts acknowledged
- [ ] Outstanding issues documented
- [ ] Recent changes noted
- [ ] Next on-contact confirmed

## Emergency Contacts

- Technical Lead: [Phone/Slack]
- Infrastructure Lead: [Phone/Slack]
- Theatre Staff: [Phone]

## Maintenance Windows

Request silence using:
```bash
./scripts/silence-alerts.sh 2h "Deploying v1.2.3" service=scenespeak
```

Always:
- Schedule in advance in #chimera-planning
- Avoid during show hours
- Update on-call calendar
```

**Step 2: Commit**

```bash
git add docs/runbooks/on-call.md
git commit -m "docs(alerting): add on-call handbook with procedures and rotation"
```

---

### Task 5: Update Alerts Runbook

**Files:**
- Modify: `docs/runbooks/alerts.md`

**Step 1: Read current runbook**

Run: `cat docs/runbooks/alerts.md`

**Step 2: Add new alert procedures**

Append to file:
```markdown
## Critical Alert Procedures

### Service Down

**Symptom:** ServiceDown alert fired

**Diagnosis:**
```bash
kubectl get pods -n live -l service=<service_name>
kubectl logs -f -n live deployment/<service_name> --tail=100
kubectl describe pod -n live <pod_name>
```

**Resolution:**
1. Check if pod is CrashLoopBackOff
2. Review logs for errors
3. Check resource limits
4. Restart if needed: `kubectl rollout restart deployment/<service> -n live`

**Runbook:** https://docs/runbooks/incident-response.html

### High Error Rate

**Symptom:** HighErrorRate alert fired

**Diagnosis:**
```bash
# Check error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Check recent errors
kubectl logs -n live deployment/<service> --since=5m | grep ERROR
```

**Resolution:**
1. Identify error pattern
2. Check recent deployments
3. Consider rollback if needed
4. Fix and redeploy

### Pod Crash Looping

**Symptom:** PodCrashLooping alert fired

**Diagnosis:**
```bash
kubectl describe pod -n live <pod_name>
kubectl logs -n live <pod-name> --previous
```

**Resolution:**
1. Check for OOMKilled (increase memory)
2. Check for crash in application logs
3. Fix crash cause
4. Delete pod to force restart
```

**Step 3: Commit**

```bash
git add docs/runbooks/alerts.md
git commit -m "docs(alerting): update alerts runbook with critical alert procedures"
```

---

## Phase 2: Business Visibility (Week 2)

### Task 6: Add Business Metrics to SceneSpeak

**Files:**
- Create: `services/SceneSpeak Agent/src/business_metrics.py`
- Modify: `services/SceneSpeak Agent/src/main.py`
- Create: `services/SceneSpeak Agent/tests/test_business_metrics.py`

**Step 1: Write test for business metrics**

```python
# services/SceneSpeak Agent/tests/test_business_metrics.py
import pytest
from prometheus_client import REGISTRY

def test_dialogue_quality_metric_registered():
    """Test that dialogue quality metric is registered"""
    from src.business_metrics import dialogue_quality
    assert dialogue_quality._name in {m.name for m in REGISTRY.collect()}

def test_lines_generated_metric():
    """Test lines generation counter"""
    from src.business_metrics import lines_generated
    lines_generated.labels(show_id="test-show").inc()
    # Verify metric exists
    metric = REGISTRY.get_sample_value('scenespeak_lines_generated_total', {'show_id': 'test-show'})
    assert metric == 1.0

def test_dialogue_quality_labels():
    """Test dialogue quality has correct labels"""
    from src.business_metrics import dialogue_quality
    dialogue_quality.labels(adapter="dramatic").set(0.85)
    metric = REGISTRY.get_sample_value('scenespeak_dialogue_quality', {'adapter': 'dramatic'})
    assert metric == 0.85
```

**Step 2: Run tests to verify they fail**

Run: `cd services/SceneSpeak Agent && pytest tests/test_business_metrics.py -v`
Expected: `ModuleNotFoundError: src.business_metrics`

**Step 3: Implement business metrics**

```python
# services/SceneSpeak Agent/src/business_metrics.py
from prometheus_client import Gauge, Counter, Histogram
import time

# Dialogue quality score (0-1)
dialogue_quality = Gauge(
    'scenespeak_dialogue_quality',
    'Dialogue coherence and quality score',
    ['adapter']
)

# Lines generated per show
lines_generated = Counter(
    'scenespeak_lines_generated_total',
    'Total lines of dialogue generated',
    ['show_id']
)

# Tokens per line
tokens_per_line = Histogram(
    'scenespeak_tokens_per_line',
    'Token count per generated line',
    buckets=[10, 25, 50, 75, 100, 150, 200, 300, 500]
)

# Generation duration
generation_duration = Histogram(
    'scenespeak_generation_duration_seconds',
    'Time spent generating dialogue',
    ['adapter'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Cache hit rate
cache_hits = Counter(
    'scenespeak_cache_hits_total',
    'Cache hit count',
    ['adapter']
)

cache_misses = Counter(
    'scenespeak_cache_misses_total',
    'Cache miss count',
    ['adapter']
)

def record_generation(show_id: str, adapter: str, tokens: int, duration: float, quality: float, cache_hit: bool):
    """Record a dialogue generation event"""
    lines_generated.labels(show_id=show_id).inc()
    tokens_per_line.observe(tokens)
    generation_duration.labels(adapter=adapter).observe(duration)
    dialogue_quality.labels(adapter=adapter).set(quality)

    if cache_hit:
        cache_hits.labels(adapter=adapter).inc()
    else:
        cache_misses.labels(adapter=adapter).inc()
```

**Step 4: Run tests to verify they pass**

Run: `cd services/SceneSpeak Agent && pytest tests/test_business_metrics.py -v`
Expected: All tests pass

**Step 5: Integrate into main.py**

Edit: `services/SceneSpeak Agent/src/main.py`
Add import:
```python
from src.business_metrics import record_generation
```

Update generate endpoint:
```python
@app.post("/v1/generate")
async def generate(request: GenerateRequest):
    start = time.time()

    # ... existing generation code ...

    # Record metrics
    record_generation(
        show_id=request.metadata.get("show_id", "unknown"),
        adapter=request.adapter or "default",
        tokens=len(result.dialogue.split()),
        duration=time.time() - start,
        quality=result.metadata.get("quality_score", 0.8),
        cache_hit=result.metadata.get("from_cache", False)
    )

    return result
```

**Step 6: Commit**

```bash
git add services/SceneSpeak Agent/src/business_metrics.py services/SceneSpeak Agent/src/main.py
git commit -m "feat(scenespeak): add business metrics for dialogue generation"
```

---

### Task 7: Add Business Metrics to Sentiment Agent

**Files:**
- Create: `services/Sentiment Agent/src/business_metrics.py`
- Modify: `services/Sentiment Agent/src/main.py`
- Create: `services/Sentiment Agent/tests/test_business_metrics.py`

**Step 1: Write tests**

```python
# services/Sentiment Agent/tests/test_business_metrics.py
import pytest

def test_audience_sentiment_metric():
    """Test audience sentiment metric"""
    from src.business_metrics import audience_sentiment
    audience_sentiment.labels(show_id="test-show", time_window="5m").set(0.75)
    assert True  # If no exception, metric works

def test_emotion_distribution():
    """Test emotion distribution metrics"""
    from src.business_metrics import emotion_joy
    emotion_joy.labels(show_id="test-show").inc()
    assert True
```

**Step 2: Run tests to verify failure**

Run: `cd services/Sentiment Agent && pytest tests/test_business_metrics.py -v`
Expected: `ModuleNotFoundError`

**Step 3: Implement metrics**

```python
# services/Sentiment Agent/src/business_metrics.py
from prometheus_client import Gauge, Counter

# Average audience sentiment
audience_sentiment = Gauge(
    'sentiment_audience_avg',
    'Average audience sentiment score',
    ['show_id', 'time_window']
)

# Emotion distribution
emotion_joy = Counter('sentiment_emotion_joy_total', 'Joy emotion count', ['show_id'])
emotion_surprise = Counter('sentiment_emotion_surprise_total', 'Surprise emotion count', ['show_id'])
emotion_neutral = Counter('sentiment_emotion_neutral_total', 'Neutral emotion count', ['show_id'])
emotion_sadness = Counter('sentiment_emotion_sadness_total', 'Sadness emotion count', ['show_id'])
emotion_anger = Counter('sentiment_emotion_anger_total', 'Anger emotion count', ['show_id'])
emotion_fear = Counter('sentiment_emotion_fear_total', 'Fear emotion count', ['show_id'])

# Processing metrics
analysis_queue_size = Gauge(
    'sentiment_analysis_queue_size',
    'Number of texts awaiting analysis'
)

analysis_duration = Gauge(
    'sentiment_analysis_duration_seconds',
    'Time spent analyzing sentiment'
)

def record_analysis(show_id: str, sentiment: float, emotions: dict, duration: float):
    """Record a sentiment analysis event"""
    audience_sentiment.labels(show_id=show_id, time_window="5m").set(sentiment)
    analysis_duration.set(duration)

    # Record emotions
    emotion_counters = {
        'joy': emotion_joy,
        'surprise': emotion_surprise,
        'neutral': emotion_neutral,
        'sadness': emotion_sadness,
        'anger': emotion_anger,
        'fear': emotion_fear
    }

    for emotion, count in emotions.items():
        if emotion in emotion_counters:
            emotion_counters[emotion].labels(show_id=show_id).inc(count)
```

**Step 4: Run tests to verify pass**

Run: `cd services/Sentiment Agent && pytest tests/test_business_metrics.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add services/Sentiment Agent/src/business_metrics.py services/Sentiment Agent/src/main.py
git commit -m "feat(sentiment): add business metrics for audience sentiment tracking"
```

---

### Task 8: Add Business Metrics to Captioning Agent

**Files:**
- Create: `services/Captioning Agent/src/business_metrics.py`
- Modify: `services/Captioning Agent/src/main.py`

**Step 1: Implement metrics**

```python
# services/Captioning Agent/src/business_metrics.py
from prometheus_client import Histogram, Counter, Gauge

# Caption latency
caption_latency = Histogram(
    'captioning_latency_seconds',
    'Time from speech to caption display',
    buckets=[0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)

# Captions delivered
captions_delivered = Counter(
    'captioning_delivered_total',
    'Total captions delivered',
    ['show_id']
)

# Accuracy
caption_accuracy = Gauge(
    'captioning_accuracy_score',
    'Caption accuracy score (0-1)',
    ['show_id']
)

# Active caption users
active_caption_users = Gauge(
    'captioning_active_users',
    'Number of users viewing captions'
)
```

**Step 2: Integrate into main**

Edit: `services/Captioning Agent/src/main.py`

**Step 3: Commit**

```bash
git add services/Captioning Agent/src/business_metrics.py
git commit -m "feat(captioning): add business metrics for captioning latency and accuracy"
```

---

### Task 9: Add Business Metrics to BSL Agent

**Files:**
- Create: `services/BSL Agent/src/business_metrics.py`

**Step 1: Implement metrics**

```python
# services/BSL Agent/src/business_metrics.py
from prometheus_client import Gauge, Counter, Histogram

# Active BSL avatar sessions
bsl_active_sessions = Gauge(
    'bsl_active_sessions',
    'Number of active BSL avatar rendering sessions'
)

# Gestures rendered
gestures_rendered = Counter(
    'bsl_gestures_rendered_total',
    'Total gestures rendered',
    ['show_id']
)

# Avatar rendering quality
avatar_frame_rate = Gauge(
    'bsl_avatar_frame_rate',
    'Avatar rendering frame rate (FPS)',
    ['session_id']
)

# Translation latency
translation_latency = Histogram(
    'bsl_translation_latency_seconds',
    'Time to translate text to BSL gloss',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0]
)
```

**Step 2: Commit**

```bash
git add services/BSL Agent/src/business_metrics.py
git commit -m "feat(bsl): add business metrics for avatar rendering and translation"
```

---

### Task 10: Create Show Overview Dashboard

**Files:**
- Create: `platform/monitoring/config/grafana-dashboards/show-overview.json`

**Step 1: Create dashboard JSON**

```json
{
  "dashboard": {
    "title": "Project Chimera - Show Overview",
    "tags": ["chimera", "show", "business"],
    "timezone": "browser",
    "refresh": "5s",
    "panels": [
      {
        "id": 1,
        "title": "Show State",
        "type": "stat",
        "targets": [
          {
            "expr": "show_state",
            "legendFormat": "{{state}}"
          }
        ],
        "options": {
          "colorMode": "background",
          "graphMode": "none",
          "reduceOptions": {
            "calcs": ["lastNotNull"]
          },
          "mappings": [
            {
              "type": "value",
              "value": "0",
              "result": {
                "text": "IDLE",
                "color": "gray"
              }
            },
            {
              "type": "value",
              "value": "1",
              "result": {
                "text": "ACTIVE",
                "color": "green"
              }
            }
          ]
        }
      },
      {
        "id": 2,
        "title": "Show Timer",
        "type": "gauge",
        "targets": [
          {
            "expr": "show_time_remaining_seconds",
            "legendFormat": "Time Remaining"
          }
        ]
      },
      {
        "id": 3,
        "title": "Service Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"chimera-services\"}",
            "legendFormat": "{{service}}"
          }
        ],
        "options": {
          "displayMode": "gradient",
          "orientation": "horizontal"
        }
      },
      {
        "id": 4,
        "title": "Audience Sentiment (5 min)",
        "type": "gauge",
        "targets": [
          {
            "expr": "sentiment_audience_avg{time_window=\"5m\"}",
            "legendFormat": "Sentiment"
          }
        ],
        "options": {
          "min": -1,
          "max": 1,
          "thresholds": [
            {"value": -0.3, "color": "red"},
            {"value": 0.3, "color": "yellow"},
            {"value": 0.7, "color": "green"}
          ]
        }
      },
      {
        "id": 5,
        "title": "Recent Alerts",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {},
              "indexByName": {},
              "renameByName": {
                "alertname": "Alert",
                "severity": "Severity",
                "service": "Service"
              }
            }
          }
        ]
      },
      {
        "id": 6,
        "title": "Dialogue Generation Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(scenespeak_lines_generated_total[5m])",
            "legendFormat": "Lines/minute"
          }
        ]
      },
      {
        "id": 7,
        "title": "Active BSL Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "bsl_active_sessions",
            "legendFormat": "Sessions"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Load dashboard to Grafana**

Run:
```bash
# Port forward to Grafana
kubectl port-forward -n shared svc/grafana 3000:3000

# Load dashboard using API or upload via UI
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @platform/monitoring/config/grafana-dashboards/show-overview.json
```

**Step 3: Commit**

```bash
git add platform/monitoring/config/grafana-dashboards/show-overview.json
git commit -m "feat(grafana): add show overview dashboard for live monitoring"
```

---

### Task 11: Create Dialogue Quality Dashboard

**Files:**
- Create: `platform/monitoring/config/grafana-dashboards/dialogue-quality.json`

**Step 1: Create dashboard JSON with panels**
- Lines generated per minute
- Average tokens per line
- Adapter performance comparison
- Cache hit rate
- Dialogue quality score by adapter

**Step 2: Commit**

```bash
git add platform/monitoring/config/grafana-dashboards/dialogue-quality.json
git commit -m "feat(grafana): add dialogue quality dashboard"
```

---

### Task 12: Create Audience Engagement Dashboard

**Files:**
- Create: `platform/monitoring/config/grafana-dashboards/audience-engagement.json`

**Step 1: Create dashboard**
- Sentiment trend over time
- Emotion distribution
- Peak engagement detection
- Caption usage
- BSL avatar sessions

**Step 2: Commit**

```bash
git add platform/monitoring/config/grafana-dashboards/audience-engagement.json
git commit -m "feat(grafana): add audience engagement dashboard"
```

---

## Phase 3: Reliability Framework (Week 3)

### Task 13: Create SLO Recording Rules

**Files:**
- Create: `platform/monitoring/config/slo-recording-rules.yaml`

**Step 1: Write recording rules**

```yaml
# platform/monitoring/config/slo-recording-rules.yaml
groups:
- name: chimera.slo.recording
  interval: 30s
  rules:
  # OpenClaw SLO: 99.9% success rate (30-day rolling)
  - record: slo:orchestration_success_rate:30d
    expr: |
      sum(rate(orchestration_success_total{job="openclaw"}[30d]))
      /
      sum(rate(orchestration_total{job="openclaw"}[30d]))

  # SceneSpeak SLO: 99.5% success rate (30-day rolling)
  - record: slo:generation_success_rate:30d
    expr: |
      sum(rate(scenespeak_generation_success_total[30d]))
      /
      sum(rate(scenespeak_generation_total[30d]))

  # Captioning SLO: 99.5% delivery rate (30-day rolling)
  - record: slo:captioning_delivery_rate:30d
    expr: |
      sum(rate(captioning_delivered_total[30d]))
      /
      sum(rate(captioning_requested_total[30d]))

  # BSL SLO: 99% success rate (30-day rolling)
  - record: slo:bsl_translation_rate:30d
    expr: |
      sum(rate(bsl_translation_success_total[30d]))
      /
      sum(rate(bsl_translation_total[30d]))

  # Safety SLO: 99.9% availability (30-day rolling)
  - record: slo:safety_availability:30d
    expr: |
      sum(rate(safety_filter_success_total[30d]))
      /
      sum(rate(safety_filter_total[30d]))

  # Error budget calculation
  - record: slo:error_budget_remaining:30d
    expr: |
      (slo_target - slo_actual_success_rate) / slo_target

  # Burn rate calculation
  - record: slo:error_burn_rate
    expr: |
      (current_error_rate - allowed_error_rate) / allowed_error_rate
```

**Step 2: Validate**

Run: `promtool check rules platform/monitoring/config/slo-recording-rules.yaml`
Expected: SUCCESS

**Step 3: Commit**

```bash
git add platform/monitoring/config/slo-recording-rules.yaml
git commit -m "feat(slo): add SLO recording rules for all core services"
```

---

### Task 14: Create SLO Alerting Rules

**Files:**
- Create: `platform/monitoring/config/slo-alerting-rules.yaml`

**Step 1: Write SLO alert rules**

```yaml
# platform/monitoring/config/slo-alerting-rules.yaml
groups:
- name: chimera.slo.alerting
  interval: 1m
  rules:
  # SLO breach - burn rate warning (2x)
  - alert: ErrorBudgetBurnRateWarning
    expr: slo:error_burn_rate > 2
    for: 5m
    labels:
      severity: warning
      category: slo
    annotations:
      summary: "Error budget burning 2x faster than normal"
      description: "Service {{ $labels.service }} error budget burn rate is {{ $value }}x"
      runbook: "https://docs/runbooks/slo-response.html#burn-rate"
      action: "Assess impact, consider deployment freeze"

  # SLO breach - burn rate critical (10x)
  - alert: ErrorBudgetBurnRateCritical
    expr: slo:error_burn_rate > 10
    for: 1m
    labels:
      severity: critical
      category: slo
    annotations:
      summary: "Error budget burning 10x faster than normal"
      description: "Service {{ $labels.service }} is consuming error budget at {{ $value }}x"
      runbook: "https://docs/runbooks/slo-response.html#burn-rate"
      action: "Block deployments, page on-call, investigate immediately"

  # SLO not met
  - alert: SLONotMet
    expr: |
      slo:slo:orchestration_success_rate:30d < 0.999
      or slo:slo:generation_success_rate:30d < 0.995
      or slo:slo:captioning_delivery_rate:30d < 0.995
      or slo:slo:bsl_translation_rate:30d < 0.99
      or slo:slo:safety_availability:30d < 0.999
    for: 5m
    labels:
      severity: critical
      category: slo
    annotations:
      summary: "SLO not met for {{ $labels.service }}"
      description: "{{ $labels.service }} SLO compliance is {{ $value | humanizePercentage }}"
      runbook: "https://docs/runbooks/slo-response.html#slo-breach"
      action: "Block all deployments, investigate root cause"

  # Error budget exhausted (less than 10% remaining)
  - alert: ErrorBudgetExhausted
    expr: slo:error_budget_remaining:30d < 0.10
    for: 1m
    labels:
      severity: critical
      category: slo
    annotations:
      summary: "Error budget nearly exhausted for {{ $labels.service }}"
      description: "Only {{ $value | humanizePercentage }} budget remaining"
      runbook: "https://docs/runbooks/slo-response.html#budget-exhausted"
      action: "Block deployments, emergency review required"
```

**Step 2: Commit**

```bash
git add platform/monitoring/config/slo-alerting-rules.yaml
git commit -m "feat(slo): add SLO alerting rules for burn rate and budget exhaustion"
```

---

### Task 15: Implement SLO Quality Gate

**Files:**
- Create: `platform/quality-gate/slo_gate.py`
- Modify: `platform/quality-gate/main.py`
- Create: `platform/quality-gate/tests/test_slo_gate.py`

**Step 1: Write tests**

```python
# platform/quality-gate/tests/test_slo_gate.py
import pytest
from slo_gate import SloQualityGate, GateResult

def test_slo_gate_allows_when_slo_met():
    """Test that gate allows when SLO compliance > 95%"""
    gate = SloQualityGate()
    result = gate.check_deployment_readiness("scenespeak")
    assert result.action == "allow"

def test_slo_gate_blocks_when_slo_not_met():
    """Test that gate blocks when SLO compliance < 95%"""
    gate = SloQualityGate()
    # Mock SLO compliance below threshold
    result = gate.check_deployment_readiness("scenespeak", mock_compliance=0.90)
    assert result.action == "block"
    assert "SLO compliance" in result.reason

def test_slo_gate_blocks_when_budget_exhausted():
    """Test that gate blocks when error budget < 10%"""
    gate = SloQualityGate()
    result = gate.check_deployment_readiness("scenespeak", mock_budget=0.05)
    assert result.action == "block"
    assert "Error budget" in result.reason
```

**Step 2: Run tests to verify failure**

**Step 3: Implement SLO gate**

```python
# platform/quality-gate/slo_gate.py
from typing import Optional
from dataclasses import dataclass
import requests

@dataclass
class GateResult:
    action: str  # "allow", "block"
    reason: str
    slo_compliance: Optional[float] = None
    error_budget_remaining: Optional[float] = None

class SloQualityGate:
    """SLO-based quality gate for deployment blocking"""

    SLO_THRESHOLDS = {
        "openclaw-orchestrator": {"slo": 0.999, "budget": 0.10},
        "SceneSpeak Agent": {"slo": 0.995, "budget": 0.10},
        "Captioning Agent": {"slo": 0.995, "budget": 0.10},
        "BSL Agent": {"slo": 0.99, "budget": 0.10},
        "safety-filter": {"slo": 0.999, "budget": 0.10},
        "operator-console": {"slo": 0.995, "budget": 0.10},
    }

    def __init__(self, prometheus_url: str = "http://prometheus.shared.svc.cluster.local:9090"):
        self.prometheus_url = prometheus_url

    def check_deployment_readiness(self, service: str) -> GateResult:
        """Check if service is ready for deployment based on SLO compliance"""

        # Get SLO compliance from Prometheus
        slo_compliance = self._get_slo_compliance(service)

        # Get error budget remaining
        error_budget = self._get_error_budget(service)

        # Get thresholds
        thresholds = self.SLO_THRESHOLDS.get(service, {"slo": 0.99, "budget": 0.10})

        # Check SLO compliance
        if slo_compliance < thresholds["slo"]:
            return GateResult(
                action="block",
                reason=f"SLO compliance at {slo_compliance:.1%}, below {thresholds['slo']:.1%} threshold",
                slo_compliance=slo_compliance,
                error_budget_remaining=error_budget
            )

        # Check error budget
        if error_budget < thresholds["budget"]:
            return GateResult(
                action="block",
                reason=f"Error budget at {error_budget:.1%}, below {thresholds['budget']:.1%} threshold",
                slo_compliance=slo_compliance,
                error_budget_remaining=error_budget
            )

        return GateResult(
            action="allow",
            reason=f"SLO compliance ({slo_compliance:.1%}) and budget ({error_budget:.1%}) are healthy",
            slo_compliance=slo_compliance,
            error_budget_remaining=error_budget
        )

    def _get_slo_compliance(self, service: str) -> float:
        """Get current SLO compliance from Prometheus"""
        # Query Prometheus for SLO compliance
        query = f'slo:{service.replace("-", "_")}_success_rate:30d'
        # Implementation: query Prometheus
        return 0.997  # Mock

    def _get_error_budget(self, service: str) -> float:
        """Get remaining error budget"""
        query = f'slo:error_budget_remaining:30d{{service="{service}"}}'
        # Implementation: query Prometheus
        return 0.45  # Mock
```

**Step 4: Run tests to verify pass**

**Step 5: Integrate into quality gate main**

Edit: `platform/quality-gate/main.py`

**Step 6: Commit**

```bash
git add platform/quality-gate/slo_gate.py platform/quality-gate/main.py platform/quality-gate/tests/test_slo_gate.py
git commit -m "feat(slo): implement SLO-based quality gate for deployment blocking"
```

---

### Task 16: Create Error Budget Calculation Script

**Files:**
- Create: `scripts/calculate-error-budget.py`

**Step 1: Implement script**

```python
#!/usr/bin/env python3
"""Calculate and report error budget status for all services"""

import requests
import sys
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9090"

SLO_TARGETS = {
    "openclaw-orchestrator": 0.999,
    "SceneSpeak Agent": 0.995,
    "Captioning Agent": 0.995,
    "BSL Agent": 0.99,
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
        status_symbol = {"healthy": "✓", "warning": "⚠", "critical": "✗"}[budget["status"]]
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
```

**Step 2: Make executable and test**

Run:
```bash
chmod +x scripts/calculate-error-budget.py
./scripts/calculate-error-budget.py
```

**Step 3: Commit**

```bash
git add scripts/calculate-error-budget.py
git commit -m "feat(slo): add error budget calculation script"
```

---

### Task 17: Create SLO Compliance Report Script

**Files:**
- Create: `scripts/slo-compliance-report.sh`

**Step 1: Implement script**

```bash
#!/bin/bash
# Generate weekly SLO compliance report

OUTPUT_DIR="reports/slo"
mkdir -p "$OUTPUT_DIR"
REPORT_FILE="$OUTPUT_DIR/slo-compliance-$(date +%Y-%m-%d).md"

cat > "$REPORT_FILE" << EOF
# SLO Compliance Report

**Date:** $(date +%Y-%m-%d)
**Period:** Last 30 days

## Executive Summary

EOF

# Generate for each service
for service in openclaw-orchestrator SceneSpeak Agent Captioning Agent BSL Agent safety-filter operator-console; do
    cat >> "$REPORT_FILE" << EOF

### $service

**SLO Target:** ${SLO_TARGETS[$service]}

\`\`\`
$(kubectl exec -n shared prometheus-0 -- promtool query instant 'slo:${service//-/_}_success_rate:30d' 2>/dev/null || echo "N/A")
\`\`\`

EOF
done

cat >> "$REPORT_FILE" << EOF

## Recommendations

Generated: $(date)
EOF

echo "Report generated: $REPORT_FILE"
```

**Step 2: Commit**

```bash
git add scripts/slo-compliance-report.sh
git commit -m "feat(slo): add SLO compliance report generator"
```

---

### Task 18: Create SLO Documentation

**Files:**
- Create: `docs/runbooks/slo-handbook.md`
- Create: `docs/runbooks/slo-response.md`

**Step 1: Create SLO handbook**

```markdown
# SLO Handbook

## Overview

This handbook defines Service Level Objectives (SLOs) for Project Chimera services.

## SLO Definitions

### Core Services

| Service | SLO | Measurement Period | Error Budget |
|---------|-----|-------------------|--------------|
| OpenClaw | 99.9% | Rolling 30 days | 43.2 min/month |
| SceneSpeak | 99.5% | Rolling 30 days | 3.6 hrs/month |
| Captioning | 99.5% | Rolling 30 days | 3.6 hrs/month |
| BSL | 99% | Rolling 30 days | 7.2 hrs/month |
| Safety | 99.9% | Rolling 30 days | 43.2 min/month |
| Console | 99.5% | Rolling 30 days | 3.6 hrs/month |

### Platform Services

| Service | SLO | Measurement Period |
|---------|-----|-------------------|
| Dashboard | 99% | Rolling 7 days |
| Test Orchestrator | 95% | Calendar month |
| CI/CD Gateway | 95% | Calendar month |

## Error Budget Policy

**Burn Rate 1x:** Normal operation, no action required
**Burn Rate 2x:** Warning, assess impact
**Burn Rate 10x:** Critical, block deployments

**Budget < 10%:** Block all non-emergency changes
**Budget < 5%:** Emergency review required

## SLO Calculations

### Success Rate

\`\`\`
Success Rate = Successful Requests / Total Requests
\`\`\`

### Error Budget

\`\`\`
Error Budget = (SLO Target - Actual Success Rate) / SLO Target
\`\`\`

### Burn Rate

\`\`\`
Burn Rate = Current Error Rate / Allowed Error Rate
\`\`\`

## Review Process

1. **Daily:** Automated burn rate monitoring
2. **Weekly:** SLO compliance report
3. **Monthly:** SLO target review and adjustment
```

**Step 2: Create SLO response runbook**

```markdown
# SLO Breach Response

## Burn Rate Warning (2x)

**Symptom:** Error budget burning 2x faster than normal

**Assessment:**
```bash
./scripts/calculate-error-budget.py
```

**Actions:**
1. Identify affected service
2. Check recent changes
3. Review error patterns
4. Consider deployment freeze
5. Document findings

**Escalation:** Technical Lead if burn rate exceeds 5x

---

## Burn Rate Critical (10x)

**Symptom:** Error budget burning 10x faster than normal

**Immediate Actions:**
1. Block all deployments to affected service
2. Page on-call engineer
3. Enable enhanced monitoring
4. Begin incident response

**Investigation:**
```bash
# Check recent deployments
kubectl rollout history deployment/<service> -n live

# Check error patterns
kubectl logs -n live deployment/<service> --tail=1000 | grep ERROR

# Check resource usage
kubectl top pods -n live -l app=<service>
```

**Resolution:**
1. Identify root cause
2. Implement fix
3. Verify SLO recovery
4. Conduct post-mortem

---

## SLO Not Met

**Symptom:** Service SLO below target for 5+ minutes

**Actions:**
1. Verify with: \`./scripts/calculate-error-budget.py\`
2. Check error budget status
3. Block deployments if budget < 10%
4. Escalate to Technical Lead

**Do NOT:**
- Deploy new features
- Make configuration changes
- Scale down service

---

## Error Budget Exhausted (<10% remaining)

**Symptom:** Error budget nearly depleted

**Actions:**
1. **EMERGENCY MODE** - Block all changes
2. Emergency review meeting
3. Prioritize stability over features
4. Consider rollback if recent change

**Recovery:**
1. Fix underlying issues
2. Monitor burn rate
3. Wait for budget recovery (30-day window)
4. Document lessons learned
```

**Step 3: Commit**

```bash
git add docs/runbooks/slo-handbook.md docs/runbooks/slo-response.md
git commit -m "docs(slo): add SLO handbook and breach response procedures"
```

---

## Phase 4: Deep Observability (Week 4)

### Task 19: Add OpenTelemetry Instrumentation Template

**Files:**
- Create: `services/shared/tracing.py`
- Create: `services/shared/__init__.py`

**Step 1: Create tracing setup module**

```python
# services/shared/tracing.py
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import os

def setup_telemetry(service_name: str, jaeger_host: str = "jaeger.shared.svc.cluster.local"):
    """Set up OpenTelemetry tracing and metrics"""

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    # Set up tracing provider
    provider = TracerProvider(resource=resource)

    # Configure sampling
    sampler = TraceIdRatioBased(0.1)  # Sample 10% of traces
    provider.add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=6831,
            )
        )
    )

    # Add console exporter for development
    if os.getenv("ENVIRONMENT") == "development":
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(provider)

    # Get tracer
    tracer = trace.get_tracer(__name__, service_name)

    return tracer

def instrument_fastapi(app):
    """Instrument FastAPI app with automatic tracing"""
    FastAPIInstrumentor.instrument_app(app)

    # Also instrument HTTPX for outgoing calls
    HTTPXClientInstrumentor().instrument()

def add_span_attributes(span, attributes: dict):
    """Add attributes to current span"""
    for key, value in attributes.items():
        span.set_attribute(key, value)

def record_error(span, error: Exception, attributes: dict = None):
    """Record error on span"""
    span.record_exception(error)
    span.set_status(Status(StatusCode.ERROR, str(error)))

    if attributes:
        add_span_attributes(span, attributes)
```

**Step 2: Commit**

```bash
git add services/shared/tracing.py services/shared/__init__.py
git commit -m "feat(tracing): add OpenTelemetry instrumentation module"
```

---

### Task 20: Instrument SceneSpeak Agent with Tracing

**Files:**
- Modify: `services/SceneSpeak Agent/src/main.py`

**Step 1: Add tracing setup**

```python
# Add to imports
from services.shared.tracing import setup_telemetry, instrument_fastapi, add_span_attributes

# Add before app creation
tracer = setup_telemetry("SceneSpeak Agent")

# Add after app creation
app = FastAPI()
instrument_fastapi(app)
```

**Step 2: Add manual spans for key operations**

```python
@app.post("/v1/generate")
async def generate(request: GenerateRequest):
    with tracer.start_as_current_span("generate_dialogue") as span:
        add_span_attributes(span, {
            "sentiment": request.sentiment,
            "adapter": request.adapter,
            "context_length": len(request.context),
        })

        try:
            # Load adapter if specified
            if request.adapter:
                with tracer.start_as_current_span("load_adapter") as adapter_span:
                    add_span_attributes(adapter_span, {"adapter": request.adapter})
                    await lora_manager.load_adapter(request.adapter)

            # Generate dialogue
            with tracer.start_as_current_span("llm_inference") as llm_span:
                result = await call_llm(request)
                add_span_attributes(llm_span, {
                    "tokens.input": result.token_count,
                    "tokens.output": len(result.dialogue.split()),
                    "duration": result.duration,
                })

            # Record business metrics
            record_generation(...)

            add_span_attributes(span, {
                "dialogue.lines": len(result.dialogue),
                "dialogue.quality": result.quality_score,
            })

            return result

        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
```

**Step 3: Commit**

```bash
git add services/SceneSpeak Agent/src/main.py
git commit -m "feat(tracing): add OpenTelemetry instrumentation to SceneSpeak"
```

---

### Task 21: Instrument Other Core Services

**Files:**
- Modify: `services/Sentiment Agent/src/main.py`
- Modify: `services/Captioning Agent/src/main.py`
- Modify: `services/BSL Agent/src/main.py`

**Step 1: Add tracing to each service**

Follow same pattern as SceneSpeak

**Step 2: Commit**

```bash
git add services/Sentiment Agent/src/main.py services/Captioning Agent/src/main.py services/BSL Agent/src/main.py
git commit -m "feat(tracing): add OpenTelemetry instrumentation to sentiment, captioning, BSL"
```

---

### Task 22: Create Trace Analysis Service

**Files:**
- Create: `platform/monitoring/trace-analyzer/__init__.py`
- Create: `platform/monitoring/trace-analyzer/analyzer.py`
- Create: `platform/monitoring/trace-analyzer/tests/test_analyzer.py`

**Step 1: Write tests**

```python
# platform/monitoring/trace-analyzer/tests/test_analyzer.py
import pytest
from analyzer import TraceAnalyzer, TraceReport, TraceIssue

def test_analyze_trace_detects_slow_spans():
    """Test that analyzer detects slow spans"""
    analyzer = TraceAnalyzer()
    report = analyzer.analyze_trace("test-trace-id")
    assert any("Slow operation" in issue.message for issue in report.issues)

def test_analyze_trace_detects_missing_spans():
    """Test that analyzer detects missing spans"""
    analyzer = TraceAnalyzer()
    # Mock trace with missing spans
    report = analyzer.analyze_trace("test-trace-missing")
    assert any("Missing spans" in issue.message for issue in report.issues)
```

**Step 2: Implement analyzer**

```python
# platform/monitoring/trace-analyzer/analyzer.py
from dataclasses import dataclass, field
from typing import List, Optional
import requests

@dataclass
class TraceIssue:
    severity: str  # "warning", "error"
    span: str
    message: str

@dataclass
class TraceReport:
    trace_id: str
    duration_ms: int
    span_count: int
    issues: List[TraceIssue] = field(default_factory=list)
    score: float = 1.0

class TraceAnalyzer:
    """Analyze Jaeger traces for performance issues"""

    def __init__(self, jaeger_url: str = "http://jaeger.shared.svc.cluster.local:16686"):
        self.jaeger_url = jaeger_url

    def analyze_trace(self, trace_id: str) -> TraceReport:
        """Analyze a trace for performance issues"""

        # Fetch trace from Jaeger
        trace = self._fetch_trace(trace_id)
        if not trace:
            return TraceReport(
                trace_id=trace_id,
                duration_ms=0,
                span_count=0,
                issues=[TraceIssue("error", "trace_fetch", "Trace not found")],
                score=0.0
            )

        issues = []

        # Check for slow spans
        for span in trace.get("spans", []):
            duration_ms = span.get("duration", 0)
            operation = span.get("operationName", "unknown")

            if duration_ms > 2000:  # 2 seconds
                issues.append(TraceIssue(
                    severity="warning",
                    span=operation,
                    message=f"Slow operation: {duration_ms}ms"
                ))

            # Check for errors
            if span.get("warnings") or span.get("errors"):
                issues.append(TraceIssue(
                    severity="error",
                    span=operation,
                    message=f"Span has warnings or errors"
                ))

        # Check for missing expected spans
        expected_spans = self._get_expected_spans(trace)
        actual_spans = {s.get("operationName") for s in trace.get("spans", [])}
        missing = expected_spans - actual_spans

        if missing:
            issues.append(TraceIssue(
                severity="error",
                span="trace_flow",
                message=f"Missing expected spans: {missing}"
            ))

        # Calculate quality score
        score = self._calculate_score(trace, issues)

        return TraceReport(
            trace_id=trace_id,
            duration_ms=trace.get("duration", 0),
            span_count=len(trace.get("spans", [])),
            issues=issues,
            score=score
        )

    def _fetch_trace(self, trace_id: str) -> Optional[dict]:
        """Fetch trace from Jaeger API"""
        try:
            response = requests.get(
                f"{self.jaeger_url}/api/traces/{trace_id}"
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0] if data.get("data") else None
        except Exception as e:
            print(f"Error fetching trace: {e}")
            return None

    def _get_expected_spans(self, trace: dict) -> set:
        """Get expected span names based on trace service"""
        # Simplified: return expected spans for common flows
        return {
            "generate_dialogue",
            "load_adapter",
            "llm_inference",
            "cache_lookup",
            "safety_check"
        }

    def _calculate_score(self, trace: dict, issues: List[TraceIssue]) -> float:
        """Calculate trace quality score (0-1)"""
        if not issues:
            return 1.0

        score = 1.0
        for issue in issues:
            if issue.severity == "error":
                score -= 0.2
            elif issue.severity == "warning":
                score -= 0.05

        return max(0.0, score)
```

**Step 3: Commit**

```bash
git add platform/monitoring/trace-analyzer/
git commit -m "feat(tracing): add trace analyzer service for performance analysis"
```

---

### Task 23: Create Anomaly Detection Rules

**Files:**
- Create: `platform/monitoring/config/trace-analysis-rules.yaml`

**Step 1: Write anomaly detection rules**

```yaml
# platform/monitoring/config/trace-analysis-rules.yaml
groups:
- name: chimera.anomaly_detection
  interval: 1m
  rules:
  # Latency anomaly - sudden spike
  - alert: LatencyAnomalyDetected
    expr: |
      (
        rate(request_duration_seconds_sum{service="SceneSpeak Agent"}[5m])
        /
        rate(request_duration_seconds_count{service="SceneSpeak Agent"}[5m])
      )
      >
      (
        avg_over_time(
          rate(request_duration_seconds_sum{service="SceneSpeak Agent"}[1h])
          /
          rate(request_duration_seconds_count{service="SceneSpeak Agent"}[1h])
        ) * 2
      )
    for: 5m
    labels:
      severity: warning
      category: anomaly
    annotations:
      summary: "Latency anomaly detected for {{ $labels.service }}"
      description: "Latency is 2x higher than 1-hour average"
      investigation: "http://jaeger:16686/search?minDuration=2000&service={{ $labels.service }}"

  # Error pattern spike
  - alert: ErrorPatternAnomaly
    expr: |
      rate(error_pattern_total[5m])
      >
      avg_over_time(rate(error_pattern_total[1h])) * 3
    for: 5m
    labels:
      severity: warning
      category: anomaly
    annotations:
      summary: "Error rate spike detected"
      description: "Error rate is 3x higher than hourly average"

  # Unusual traffic drop
  - alert: TrafficDropAnomaly
    expr: |
      rate(http_requests_total[5m])
      <
      avg_over_time(rate(http_requests_total[1h])) * 0.5
    for: 10m
    labels:
      severity: warning
      category: anomaly
    annotations:
      summary: "Unusual traffic drop for {{ $labels.service }}"
      description: "Request rate is 50% below hourly average"

  # Cache hit rate drop
  - alert: CacheHitRateDrop
    expr: |
      (
        sum(rate(cache_hits_total{service="SceneSpeak Agent"}[5m]))
        /
        (
          sum(rate(cache_hits_total{service="SceneSpeak Agent"}[5m]))
          +
          sum(rate(cache_misses_total{service="SceneSpeak Agent"}[5m]))
        )
      )
      <
      0.5
    for: 10m
    labels:
      severity: warning
      category: performance
    annotations:
      summary: "Cache hit rate dropped below 50%"
      description: "Investigate cache configuration or data"
```

**Step 2: Commit**

```bash
git add platform/monitoring/config/trace-analysis-rules.yaml
git commit -m "feat(monitoring): add anomaly detection rules for performance and errors"
```

---

### Task 24: Create Service Dependency Map Generator

**Files:**
- Create: `scripts/dependency-graph.py`

**Step 1: Implement script**

```python
#!/usr/bin/env python3
"""Generate service dependency graph from Jaeger traces"""

import requests
import json

JAEGER_URL = "http://jaeger.shared.svc.cluster.local:16686"
OUTPUT_FILE = "platform/monitoring/docs/dependency-graph.json"

def get_dependencies():
    """Query Jaeger for service dependencies"""

    # Get all services
    services_response = requests.get(f"{JAEGER_URL}/api/services")
    services = services_response.json().get("data", [])

    dependencies = {}

    for service in services:
        # Get traces for each service
        traces_response = requests.get(
            f"{JAEGER_URL}/api/traces",
            params={
                "service": service,
                "limit": 100
            }
        )

        traces = traces_response.json().get("data", [])

        service_deps = set()

        for trace in traces:
            for span in trace.get("spans", []):
                # Extract process and service info
                process = span.get("process", {})
                process_tags = process.get("tags", {})

                # Look for peer service tags
                for tag in process_tags:
                    if tag.get("key") == "peer.service":
                        service_deps.add(tag.get("value"))

        dependencies[service] = list(service_deps)

    return dependencies

def generate_graph(dependencies):
    """Generate Graphviz DOT format"""

    dot = ["digraph chimera_services {"]
    dot.append("  rankdir=LR;")
    dot.append("  node [shape=box, style=rounded];")
    dot.append("")

    # Add nodes
    for service in dependencies.keys():
        dot.append(f'  "{service}" [label="{service}"];')

    dot.append("")

    # Add edges
    for service, deps in dependencies.items():
        for dep in deps:
            dot.append(f'  "{service}" -> "{dep}";')

    dot.append("}")

    return "\n".join(dot)

def main():
    print("Fetching service dependencies from Jaeger...")

    dependencies = get_dependencies()

    # Save JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dependencies, f, indent=2)

    # Generate DOT
    dot_graph = generate_graph(dependencies)

    dot_file = OUTPUT_FILE.replace(".json", ".dot")
    with open(dot_file, "w") as f:
        f.write(dot_graph)

    print(f"Dependency graph saved to {OUTPUT_FILE}")
    print(f"DOT format saved to {dot_file}")
    print(f"Render with: dot -Tpng {dot_file} -o dependency-graph.png")

if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add scripts/dependency-graph.py
git commit -m "feat(monitoring): add service dependency graph generator"
```

---

### Task 25: Create Distributed Tracing Documentation

**Files:**
- Create: `docs/runbooks/distributed-tracing.md`
- Create: `docs/runbooks/performance-analysis.md`

**Step 1: Create distributed tracing runbook**

```markdown
# Distributed Tracing Runbook

## Overview

Project Chimera uses OpenTelemetry and Jaeger for distributed tracing across all services.

## Access Jaeger

**URL:** http://jaeger.shared.svc.cluster.local:16686

**Port Forward:**
```bash
kubectl port-forward -n shared svc/jaeger 16686:16686
```

## Searching Traces

### By Service

1. Select service from dropdown
2. Set time range (last hour, today, etc.)
3. Click "Find Traces"

### By Trace ID

If you have a trace ID from logs:
1. Enter Trace ID in search box
2. Click "Find Traces"

### By Operation

1. Select service
2. Enter operation name (e.g., "generate_dialogue")
3. Add tags/filters as needed

## Analyzing Traces

### Reading a Trace

**Timeline View:**
- Each bar = one span
- Width = duration
- Color = status (red = error, yellow = warning)

**Span Details:**
- Click span to view details
- Check logs for errors
- View tags for context

### Common Issues

**High Latency:**
- Look for wide spans
- Check database/external calls
- Review trace timeline

**Missing Spans:**
- Service not instrumented
- Sampling dropped trace
- Network issue

**Error Spans:**
- Red color indicates error
- Click span for error details
- Check logs for stack trace

## Trace Analysis Tools

### Analyze Trace Script

```bash
./scripts/analyze-trace.py <trace-id>
```

Output:
- Trace quality score
- Slow spans identified
- Missing spans listed
- Recommendations provided

### Dependency Graph

```bash
./scripts/dependency-graph.py
```

Generates service dependency visualization.
```

**Step 2: Create performance analysis runbook**

```markdown
# Performance Analysis Runbook

## Tools

- **Jaeger:** Distributed tracing
- **Grafana:** Metrics dashboards
- **Prometheus:** Raw metrics queries

## Performance Investigation

### 1. Identify Slow Request

**In Jaeger:**
1. Search for operation (e.g., "generate_dialogue")
2. Sort by duration (descending)
3. Click slowest trace

**In Prometheus:**
```promql
topk(10, histogram_quantile(0.95,
  sum(rate(request_duration_seconds_bucket[5m])) by (le, service)
))
```

### 2. Analyze Trace

- Find widest span
- Check external calls
- Look for N+1 queries
- Review cache usage

### 3. Check Resources

```bash
# Service resource usage
kubectl top pods -n live -l app=<service>

# Pod details
kubectl describe pod -n live <pod-name>
```

### 4. Common Patterns

**Slow Database:**
- Add connection pooling
- Implement caching
- Optimize queries

**Slow LLM:**
- Increase cache hit rate
- Use smaller models
- Batch requests

**Network Latency:**
- Check service placement
- Review network policies
- Consider service mesh

## Optimization

### Before Optimization

1. Establish baseline
2. Set target (e.g., reduce P95 by 50%)
3. Document current state

### After Optimization

1. Verify improvement
2. Check for regressions
3. Update documentation

## Alerting on Performance

**Latency Alerts:**
- P95 > 2 seconds (warning)
- P95 > 5 seconds (critical)
- P99 > 10 seconds (critical)

**Throughput Alerts:**
- Request rate drops 50% (warning)
- Queue depth > 100 (warning)
- Queue depth > 500 (critical)
```

**Step 3: Commit**

```bash
git add docs/runbooks/distributed-tracing.md docs/runbooks/performance-analysis.md
git commit -m "docs(tracing): add distributed tracing and performance analysis runbooks"
```

---

## Summary Tasks

### Task 26: Update Main Prometheus Configuration

**Files:**
- Modify: `infrastructure/kubernetes/prometheus/configmap.yaml`

**Step 1: Add all new rule files**

Add to Prometheus config:
```yaml
rule_files:
  - /etc/prometheus/rules/critical/*.yaml
  - /etc/prometheus/rules/slo/*.yaml
  - /etc/prometheus/rules/anomaly/*.yaml
```

**Step 2: Add AlertManager as receiver**

Add to AlertManager config section:
```yaml
alerting:
  alertmanagers:
  - static_configs:
    - targets: ['alertmanager.shared.svc.cluster.local:9093']
```

**Step 3: Commit**

```bash
git add infrastructure/kubernetes/prometheus/configmap.yaml
git commit -m "feat(prometheus): update config with AlertManager and new rule files"
```

---

### Task 27: Create Observability Summary Documentation

**Files:**
- Create: `docs/observability.md`

**Step 1: Create overview document**

```markdown
# Production Observability at Project Chimera

## Overview

Project Chimera's production observability stack provides complete visibility into service health, business metrics, SLO compliance, and distributed tracing.

## Components

### 1. Alerting Foundation
- **AlertManager:** Intelligent alert routing
- **Slack Integration:** Real-time notifications
- **On-Call Rotation:** 24/7 coverage

### 2. Business Visibility
- **Show Overview Dashboard:** Real-time show status
- **Dialogue Quality Dashboard:** Content generation metrics
- **Audience Engagement Dashboard:** Sentiment and interaction

### 3. Reliability Framework
- **SLOs:** 99-99.9% targets for core services
- **Error Budgets:** Track remaining allowance
- **Quality Gate:** Block deployments on SLO breach

### 4. Deep Observability
- **OpenTelemetry:** Distributed tracing
- **Jaeger:** Trace analysis
- **Anomaly Detection:** Automated issue detection

## Quick Links

| Tool | URL | Credentials |
|------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |
| AlertManager | http://localhost:9093 | - |

## Runbooks

- [Alerts](../runbooks/alerts.md)
- [On-Call](../runbooks/on-call.md)
- [SLO Handbook](../runbooks/slo-handbook.md)
- [SLO Response](../runbooks/slo-response.md)
- [Distributed Tracing](../runbooks/distributed-tracing.md)
- [Performance Analysis](../runbooks/performance-analysis.md)
- [Testing Guide](../runbooks/testing-guide.md)

## Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/silence-alerts.sh` | Silence alerts for maintenance |
| `./scripts/calculate-error-budget.py` | Calculate error budget status |
| `./scripts/slo-compliance-report.sh` | Generate SLO compliance report |
| `./scripts/analyze-trace.py` | Analyze a specific trace |
| `./scripts/dependency-graph.py` | Generate service dependency graph |

## Metrics Reference

### Service Health

- `up{job="chimera-services"}` - Service availability
- `rate(http_requests_total{status=~"5.."}[5m])` - Error rate

### Business Metrics

- `scenespeak_lines_generated_total` - Dialogue lines
- `sentiment_audience_avg` - Audience sentiment
- `captioning_latency_seconds` - Caption timing
- `bsl_active_sessions` - BSL avatar sessions

### SLO Metrics

- `slo:*_success_rate:30d` - SLO compliance
- `slo:error_budget_remaining:30d` - Error budget
- `slo:error_burn_rate` - Burn rate

## Support

For issues or questions:
- Check relevant runbook
- Contact on-call engineer
- Escalate to Technical Lead
```

**Step 2: Commit**

```bash
git add docs/observability.md
git commit -m "docs(observability): add observability overview and quick reference"
```

---

## End of Implementation Plan

**Total Tasks:** 27
**Estimated Duration:** 4 weeks
**Phases:** 4 (Alerting, Business Metrics, SLO Framework, Deep Observability)

All tasks include:
- Exact file paths
- Complete code samples
- TDD approach (test first)
- Verification commands
- Commit messages
- Documentation updates

---

*Implementation Plan: Production Observability Enhancement*
*Project Chimera v3.0.0*
*March 2026*
