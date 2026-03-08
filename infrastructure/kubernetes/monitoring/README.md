# Monitoring and Alerting Setup

This directory contains the complete monitoring and alerting infrastructure for Project Chimera, including Prometheus, Grafana, and AlertManager configurations.

## Overview

The monitoring stack consists of:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and deduplication
- **Node Exporter**: Host-level metrics
- **cAdvisor**: Container metrics (built into Kubelet)

## Architecture

```
Services (via /metrics)
    ↓
Prometheus (scrape every 15s)
    ↓
Prometheus TSDB (50Gi retention, 30 days)
    ↓
├─→ Grafana Dashboards (visualization)
├─→ AlertManager (alert evaluation)
    └─→ Notifications (Slack, email, PagerDuty)
```

## Directory Structure

```
infrastructure/kubernetes/
├── prometheus/
│   ├── configmap.yaml           # Prometheus configuration
│   ├── deployment.yaml          # Prometheus deployment with PVC
│   └── rules/
│       ├── critical/critical.yaml    # P0 alerts (page immediately)
│       ├── slo/slo.yaml              # P1 alerts (investigate within hour)
│       └── anomaly/anomaly.yaml      # P2 alerts (review daily)
├── grafana/
│   ├── deployment.yaml          # Grafana deployment with PVC
│   ├── provisioning/
│   │   ├── dashboards/dashboard.yaml   # Dashboard provisioning
│   │   └── datasources/prometheus.yaml  # Datasource provisioning
│   ├── dashboards/
│   │   ├── show-operations.json       # Real-time show status
│   │   ├── service-health.json        # 9 services health
│   │   ├── infrastructure.json        # Nodes, GPU, Kafka, Redis
│   │   ├── ml-performance.json        # Model metrics
│   │   ├── business-metrics.json      # Shows, engagement, moderation
│   │   └── incident-response.json     # Alerts, MTTA, MTTR
│   └── secrets.example.yaml      # Example secrets file
└── alertmanager/
    ├── configmap.yaml           # AlertManager configuration
    ├── deployment.yaml          # AlertManager deployment with PVC
    ├── config.yaml              # AlertManager config (routes, receivers)
    └── secrets.example.yaml     # Example secrets file
```

## Alert Hierarchy

### Critical Alerts (P0 - Immediate Action)

1. **Service Down**: `up{job=~".*-agent"} == 0` for 1m
2. **GPU Not Available**: `nvidia_gpu_available < 1` for 5m
3. **Model Loading Failed**: `chimera_model_loaded_total{status="fail"} > 0` for 1m
4. **Show Workflow Stuck**: `chimera_show_active == 1` AND `chimera_show_progress == 0` for 10m
5. **Kafka Consumer Lag**: `kafka_consumer_lag > 10000` for 5m

### SLO Alerts (P1 - Investigate Within Hour)

1. **High Error Rate**: `rate(http_requests_total{status=~"5.."}[5m]) > 0.01` for 5m
2. **High Latency**: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1` for 10m
3. **Low Sentiment Confidence**: `avg(chimera_sentiment_confidence) < 0.6` for 15m
4. **Audio Generation Failures**: `rate(chimera_audio_generation_failed_total[5m]) > 0.1` for 5m

### Anomaly Alerts (P2 - Review Daily)

1. **Disk Space Low**: `node_filesystem_avail_bytes < 10Gi` for 1h
2. **GPU Memory Leak**: `nvidia_gpu_memory_used` increasing >10% per hour for 2h
3. **Unusual Traffic Pattern**: Traffic deviates >3σ from baseline for 30m

## Deployment Instructions

### 1. Create Namespace

```bash
kubectl create namespace project-chimera
```

### 2. Create Secrets

```bash
# Copy example secrets files
cp infrastructure/kubernetes/grafana/secrets.example.yaml infrastructure/kubernetes/grafana/secrets.yaml
cp infrastructure/kubernetes/alertmanager/secrets.example.yaml infrastructure/kubernetes/alertmanager/secrets.yaml

# Edit with actual values
nano infrastructure/kubernetes/grafana/secrets.yaml
nano infrastructure/kubernetes/alertmanager/secrets.yaml

# Apply secrets
kubectl apply -f infrastructure/kubernetes/grafana/secrets.yaml
kubectl apply -f infrastructure/kubernetes/alertmanager/secrets.yaml
```

### 3. Deploy Prometheus

```bash
kubectl apply -f infrastructure/kubernetes/prometheus/configmap.yaml
kubectl apply -f infrastructure/kubernetes/prometheus/deployment.yaml
```

### 4. Deploy AlertManager

```bash
kubectl apply -f infrastructure/kubernetes/alertmanager/configmap.yaml
kubectl apply -f infrastructure/kubernetes/alertmanager/deployment.yaml
kubectl apply -f infrastructure/kubernetes/alertmanager/service.yaml
```

### 5. Deploy Grafana

```bash
kubectl apply -f infrastructure/kubernetes/grafana/deployment.yaml
kubectl apply -f infrastructure/kubernetes/grafana/provisioning/dashboards/dashboard.yaml
kubectl apply -f infrastructure/kubernetes/grafana/provisioning/datasources/prometheus.yaml
```

### 6. Create ConfigMaps for Dashboards

```bash
kubectl create configmap grafana-dashboards \
  --from-file=infrastructure/kubernetes/grafana/dashboards/ \
  --namespace=project-chimera
```

### 7. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n project-chimera

# Port-forward to access services
kubectl port-forward -n project-chimera svc/prometheus 9090:9090
kubectl port-forward -n project-chimera svc/grafana 3000:3000
kubectl port-forward -n project-chimera svc/alertmanager 9093:9093
```

## Accessing the Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin / password from secrets)
- **AlertManager**: http://localhost:9093

## Grafana Dashboards

1. **Show Operations Dashboard** (`show-operations.json`)
   - Real-time show status
   - Audience sentiment gauge
   - Dialogue generation rate
   - Scene progress timeline
   - Active agents status
   - Upcoming show countdown

2. **Service Health Dashboard** (`service-health.json`)
   - 9 service status panels
   - Request rate per service
   - Error rate per service
   - Latency (p50, p95, p99)
   - CPU/memory usage
   - GPU utilization
   - Uptime percentage

3. **Infrastructure Dashboard** (`infrastructure.json`)
   - Node health
   - GPU status (temperature, memory, utilization)
   - Kafka consumer lag
   - Redis hit rate
   - Milvus query performance
   - Network I/O
   - Disk I/O

4. **ML Performance Dashboard** (`ml-performance.json`)
   - Model loading time
   - Inference latency per model
   - Sentiment confidence distribution
   - Audio generation success rate
   - GPU memory per model
   - Model cache hit rate

5. **Business Metrics Dashboard** (`business-metrics.json`)
   - Shows performed today
   - Average show duration
   - Audience engagement score
   - Content moderation flags
   - Caption accuracy rate
   - BSL gloss accuracy

6. **Incident Response Dashboard** (`incident-response.json`)
   - Active alerts
   - Alert history (last 24h)
   - Mean time to acknowledge (MTTA)
   - Mean time to resolve (MTTR)
   - Error budget remaining
   - SLO attainment

## Configuration Details

### Prometheus Configuration

- **Scrape Interval**: 15s
- **Evaluation Interval**: 15s
- **Retention Period**: 30 days
- **Storage**: 50Gi PVC
- **Resources**: 2-4 CPU cores, 4-8Gi memory

### Grafana Configuration

- **Version**: 10.2.2
- **Storage**: 10Gi PVC
- **Resources**: 500m-1 CPU core, 1-2Gi memory
- **Admin Password**: Set via secret
- **Dashboards**: Auto-provisioned from ConfigMaps

### AlertManager Configuration

- **Version**: v0.26.0
- **Storage**: 5Gi PVC
- **Resources**: 500m-1 CPU core, 1-2Gi memory
- **Notification Channels**: Slack (required), PagerDuty (optional)

## Maintenance

### Updating Alert Rules

1. Edit rule files in `infrastructure/kubernetes/prometheus/rules/`
2. Update ConfigMaps:
   ```bash
   kubectl create configmap prometheus-rules-critical \
     --from-file=infrastructure/kubernetes/prometheus/rules/critical/critical.yaml \
     --namespace=project-chimera --dry-run=client -o yaml | kubectl apply -f -
   ```
3. Prometheus will automatically reload rules

### Updating Dashboards

1. Edit dashboard JSON files in `infrastructure/kubernetes/grafana/dashboards/`
2. Update ConfigMap:
   ```bash
   kubectl create configmap grafana-dashboards \
     --from-file=infrastructure/kubernetes/grafana/dashboards/ \
     --namespace=project-chimera --dry-run=client -o yaml | kubectl apply -f -
   ```
3. Restart Grafana pods to load new dashboards:
   ```bash
   kubectl rollout restart deployment/grafana -n project-chimera
   ```

### Checking Logs

```bash
# Prometheus logs
kubectl logs -n project-chimera deployment/prometheus -f

# Grafana logs
kubectl logs -n project-chimera deployment/grafana -f

# AlertManager logs
kubectl logs -n project-chimera deployment/alertmanager -f
```

## Troubleshooting

### Prometheus Not Scraping Metrics

1. Check if pods have `prometheus.io/scrape: "true"` annotation
2. Verify Prometheus can reach the pods: `kubectl exec -n project-chimera deployment/prometheus -- wget -O- http://<pod-ip>:<port>/metrics`
3. Check Prometheus targets page: http://localhost:9090/targets

### AlertManager Not Sending Alerts

1. Verify secrets are configured: `kubectl get secret -n project-chimera alertmanager-secrets -o yaml`
2. Check AlertManager logs for errors
3. Test Slack webhook URL manually
4. Verify alert rules are firing: http://localhost:9090/alerts

### Grafana Dashboards Not Loading

1. Check dashboard ConfigMap exists: `kubectl get configmap -n project-chimera grafana-dashboards`
2. Verify provisioning configs are mounted: `kubectl describe pod -n project-chimera -l app=grafana`
3. Check Grafana logs for provisioning errors
4. Ensure datasource is configured: http://localhost:3000/datasources

## Security Best Practices

1. **Never commit secrets to git** - Use `.gitignore` to exclude `secrets.yaml` files
2. **Rotate credentials regularly** - Update secrets monthly
3. **Use strong passwords** - Generate with `openssl rand -base64 32`
4. **Limit access** - Use RBAC to restrict who can view/edit monitoring
5. **Enable TLS** - Use ingress with TLS termination for production
6. **Audit logs** - Regularly review access logs and alert history

## Performance Tuning

### High Traffic Scenarios

- Increase Prometheus CPU/memory limits
- Add Prometheus remote write for long-term storage
- Use recording rules for pre-computed metrics
- Enable Prometheus compression

### Large Number of Time Series

- Use metric relabeling to drop unnecessary labels
- Implement metric cardinality limits
- Use `honor_labels` carefully
- Monitor target scrape duration

## Support and Documentation

- **TRD Spec**: `/docs/trd/TRD-007-monitoring-alerting.md`
- **Runbooks**: `/docs/runbooks/` (to be created)
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **AlertManager Docs**: https://prometheus.io/docs/alerting/latest/alertmanager/

## Next Steps

1. Set up notification channels (Slack, PagerDuty)
2. Create on-call rotation schedule
3. Document runbooks for common alerts
4. Configure alert silences for maintenance windows
5. Set up alert summary reports
6. Integrate with incident management system
