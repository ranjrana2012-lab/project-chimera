# TRD #007: Production Monitoring and Alerting

**Date:** 2026-03-07
**Status:** Draft
**Priority:** HIGH (Production Readiness)

## Overview

Define the complete monitoring, alerting, and observability strategy for Project Chimera production deployments.

## Current State Analysis

### Existing Infrastructure

**✅ Has Prometheus Config:**
- `infrastructure/kubernetes/prometheus/configmap.yaml`
  - Service discovery for all agents
  - Scrape configs for pods
  - AlertManager integration
  - Missing: actual deployment manifest

**✅ Has AlertManager Config:**
- `infrastructure/kubernetes/alertmanager/configmap.yaml`
  - Configuration exists
  - Missing: deployment manifest, receiver setup

**✅ Service-Level Metrics:**
- All services expose `/metrics` endpoint
- Prometheus annotations in existing k8s manifests

**❌ Missing:**
- Prometheus deployment manifest
- Grafana deployment and dashboards
- AlertManager deployment
- Alert rules (critical, SLO, anomaly)
- Grafana dashboard definitions
- Notification integrations (Slack, email, PagerDuty)

## Proposed Architecture

### Components

1. **Prometheus** - Metrics collection and storage
2. **Grafana** - Visualization and dashboards
3. **AlertManager** - Alert routing and deduplication
4. **Node Exporter** - Host-level metrics
5. **cAdvisor** - Container metrics
6. **Jaeger** - Distributed tracing (already exists)

### Data Flow

```
Services (via /metrics)
    ↓
Prometheus (scrape every 15s)
    ↓
Prometheus TSDB (50Gi retention)
    ↓
├─→ Grafana Dashboards (visualization)
├─→ AlertManager (alert evaluation)
    └─→ Notifications (Slack, email, PagerDuty)
```

## Alert Hierarchy

### Critical Alerts (P0 - Immediate Action)

1. **Service Down**
   - Condition: `up{job="scenespeak-agent"} == 0`
   - Duration: 1m
   - Severity: critical
   - Action: Page on-call engineer

2. **GPU Not Available**
   - Condition: `nvidia_gpu_available < 1`
   - Duration: 5m
   - Severity: critical
   - Action: Page infrastructure team

3. **Model Loading Failed**
   - Condition: `chimera_model_loaded_total{status="fail"} > 0`
   - Duration: 1m
   - Severity: critical
   - Action: Page ML team

4. **Show Workflow Stuck**
   - Condition: `chimera_show_active == 1` AND `chimera_show_progress == 0` for 10m
   - Severity: critical
   - Action: Page operations team

5. **Kafka Consumer Lag**
   - Condition: `kafka_consumer_lag > 10000`
   - Duration: 5m
   - Severity: critical
   - Action: Page streaming team

### SLO Alerts (P1 - Investigate Within Hour)

1. **High Error Rate**
   - Condition: `rate(http_requests_total{status=~"5.."}[5m]) > 0.01`
   - Duration: 5m
   - Severity: warning
   - Action: Create incident, investigate

2. **High Latency**
   - Condition: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1`
   - Duration: 10m
   - Severity: warning
   - Action: Check service health

3. **Low Sentiment Confidence**
   - Condition: `avg(chimera_sentiment_confidence) < 0.6`
   - Duration: 15m
   - Severity: warning
   - Action: Review model performance

4. **Audio Generation Failures**
   - Condition: `rate(chimera_audio_generation_failed_total[5m]) > 0.1`
   - Duration: 5m
   - Severity: warning
   - Action: Check music service health

### Anomaly Alerts (P2 - Review Daily)

1. **Unusual Traffic Pattern**
   - Condition: Traffic deviates >3σ from baseline
   - Duration: 30m
   - Severity: info
   - Action: Review in daily standup

2. **GPU Memory Leak**
   - Condition: `nvidia_gpu_memory_used` increasing >10% per hour
   - Duration: 2h
   - Severity: warning
   - Action: Schedule maintenance window

3. **Disk Space Low**
   - Condition: `node_filesystem_avail_bytes < 10Gi`
   - Duration: 1h
   - Severity: warning
   - Action: Plan cleanup or expansion

## Dashboard Requirements

### Grafana Dashboards

1. **Show Operations Dashboard** (Real-time)
   - Show status (active/inactive)
   - Audience sentiment gauge
   - Dialogue generation rate
   - Scene progress timeline
   - Active agents status
   - Upcoming show countdown

2. **Service Health Dashboard**
   - 9 service status panels
   - Request rate (per service)
   - Error rate (per service)
   - Latency (p50, p95, p99)
   - CPU/memory usage
   - GPU utilization
   - Uptime percentage

3. **Infrastructure Dashboard**
   - Node health
   - GPU status (temperature, memory, utilization)
   - Kafka consumer lag
   - Redis hit rate
   - Milvus query performance
   - Network I/O
   - Disk I/O

4. **ML Model Performance Dashboard**
   - Model loading time
   - Inference latency (per model)
   - Sentiment confidence distribution
   - Audio generation success rate
   - GPU memory per model
   - Model cache hit rate

5. **Business Metrics Dashboard**
   - Shows performed today
   - Average show duration
   - Audience engagement score
   - Content moderation flags
   - Caption accuracy rate
   - BSL gloss accuracy

6. **Incident Response Dashboard**
   - Active alerts
   - Alert history (last 24h)
   - Mean time to acknowledge (MTTA)
   - Mean time to resolve (MTTR)
   - Error budget remaining
   - SLO attainment

## Prometheus Deployment

### Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: project-chimera
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.48.0
        args:
          - '--config.file=/etc/prometheus/prometheus.yaml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=30d'
          - '--web.console.libraries=/usr/share/prometheus/console_libraries'
          - '--web.console.templates=/usr/share/prometheus/consoles'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            cpu: "2000m"
            memory: "4Gi"
          limits:
            cpu: "4000m"
            memory: "8Gi"
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-storage
```

### Alert Rules Files

**infrastructure/kubernetes/prometheus/rules/critical.yaml:**
```yaml
groups:
- name: critical
  interval: 30s
  rules:
  - alert: ServiceDown
    expr: up{job=~".*-agent"} == 0
    for: 1m
    labels:
      severity: critical
      team: operations
    annotations:
      summary: "Service {{ $labels.job }} is down"
      description: "{{ $labels.job }} has been down for more than 1 minute"

  - alert: GPUNotAvailable
    expr: nvidia_gpu_available < 1
    for: 5m
    labels:
      severity: critical
      team: infrastructure
    annotations:
      summary: "GPU not available"
      description: "Less than 1 GPU available for 5 minutes"

  # ... more critical alerts
```

**infrastructure/kubernetes/prometheus/rules/slo.yaml:**
```yaml
groups:
- name: slo
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    labels:
      severity: warning
      team: operations
    annotations:
      summary: "High error rate on {{ $labels.job }}"
      description: "Error rate is {{ $value }} (threshold: 0.01)"

  # ... more SLO alerts
```

**infrastructure/kubernetes/prometheus/rules/anomaly.yaml:**
```yaml
groups:
- name: anomaly
  interval: 1m
  rules:
  - alert: DiskSpaceLow
    expr: node_filesystem_avail_bytes{mountpoint="/"} < 10737418240
    for: 1h
    labels:
      severity: warning
      team: infrastructure
    annotations:
      summary: "Low disk space on {{ $labels.instance }}"
      description: "Less than 10Gi available"

  # ... more anomaly alerts
```

## Grafana Deployment

### Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: project-chimera
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.2.2
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secrets
              key: admin-password
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel"
        volumeMounts:
        - name: storage
          mountPath: /var/lib/grafana
        - name: provisioning
          mountPath: /etc/grafana/provisioning
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: grafana-storage
      - name: provisioning
        configMap:
          name: grafana-provisioning
```

### Dashboard Provisioning

**infrastructure/kubernetes/grafana/provisioning/dashboards/dashboard.yaml:**
```yaml
apiVersion: 1

providers:
  - name: 'Project Chimera'
    orgId: 1
    folder: 'Project Chimera'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

## AlertManager Deployment

### Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: project-chimera
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
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
      - name: storage
        persistentVolumeClaim:
          claimName: alertmanager-storage
```

### Notification Routes

**infrastructure/kubernetes/alertmanager/config.yaml:**
```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
  - match:
      severity: critical
    receiver: 'pagerduty'
    continue: true

  - match:
      severity: critical
    receiver: 'slack-critical'
    continue: false

  - match:
      severity: warning
    receiver: 'slack-warnings'
    continue: false

receivers:
- name: 'pagerduty'
  pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_KEY'
    description: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'slack-critical'
  slack_configs:
  - channel: '#chimera-critical'
    title: '🚨 {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    color: 'danger'

- name: 'slack-warnings'
  slack_configs:
  - channel: '#chimera-alerts'
    title: '⚠️ {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    color: 'warning'
```

## Implementation Plan

### Phase 1: Core Monitoring (Week 1)
1. Deploy Prometheus with existing config
2. Deploy Grafana with default dashboards
3. Deploy AlertManager with Slack integration
4. Create critical alert rules
5. Test alert delivery

### Phase 2: Dashboard Development (Week 2)
1. Create Show Operations dashboard
2. Create Service Health dashboard
3. Create Infrastructure dashboard
4. Create ML Model Performance dashboard

### Phase 3: Advanced Features (Week 3)
1. Implement SLO tracking
2. Create Business Metrics dashboard
3. Set up anomaly detection
4. Configure PagerDuty integration
5. Create Incident Response dashboard

### Phase 4: Validation (Week 4)
1. Load test monitoring
2. Alert fatigue review
3. Dashboard usability testing
4. Documentation completion

## Success Criteria

- [ ] Prometheus scraping all 9 services
- [ ] Grafana accessible with 6 dashboards
- [ ] AlertManager routing to Slack/PagerDuty
- [ ] Critical alerts fire within 1m
- [ ] Warning alerts fire within 5m
- [ ] All dashboards show real-time data
- [ ] Mobile-friendly dashboards
- [ ] Alert documentation complete
- [ ] On-call rotation established

## Open Questions

1. **Slack Workspace:** Do we have a Slack workspace for alerts?
2. **PagerDuty Account:** Do we have PagerDuty for critical alerts?
3. **Retention:** 30-day retention enough for Prometheus?
4. **Backup:** How to backup Grafana dashboards and Prometheus data?

## Next Steps

1. Set up notification channels (Slack, PagerDuty)
2. Create Kubernetes deployment manifests
3. Write alert rules (critical, SLO, anomaly)
4. Design and implement Grafana dashboards
5. Create monitoring runbook
6. Train on-call team

---

**TRD Owner:** SRE Team
**Review Date:** 2026-03-07
**Target Completion:** 2026-03-21
