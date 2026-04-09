# Project Chimera - Monitoring and Observability

**Phase 2 Complete Monitoring Stack**

This directory contains the complete monitoring and observability infrastructure for Project Chimera Phase 2 services.

## Overview

The monitoring stack provides:

- **Metrics Collection**: Prometheus for scraping and storing metrics
- **Visualization**: Grafana dashboards for real-time monitoring
- **Alerting**: AlertManager for proactive notifications
- **Distributed Tracing**: Jaeger for end-to-end request tracing
- **System Monitoring**: Node Exporter and cAdvisor for infrastructure metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 2 Services                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ DMX Ctrl    │  │ Audio Ctrl  │  │ BSL Avatar  │          │
│  │ :8001/metrics│  │ :8002/metrics│ │ :8003/metrics│          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌─────────────────────────────────────────────────┐
    │              Prometheus (9090)                  │
    │     - Scrape metrics every 15s                 │
    │     - Evaluate alerting rules                 │
    │     - 30-day data retention                    │
    └────────────────────┬────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌──────────┐
    │ Grafana │    │AlertMgr │    │  Jaeger  │
    │  :3000  │    │  :9093  │    │  :16686  │
    └─────────┘    └─────────┘    └──────────┘
```

## Quick Start

### 1. Install Monitoring Stack

```bash
./monitoring/setup-monitoring.sh --action install
```

### 2. Start Services

```bash
./monitoring/setup-monitoring.sh --action start
```

### 3. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/chimera)
- **AlertManager**: http://localhost:9093
- **Jaeger**: http://localhost:16686

## Components

### Prometheus

Metrics collection and storage:

- Scrape interval: 15 seconds
- Data retention: 30 days
- Port: 9090

**Key Queries:**

```promql
# Service uptime
up{job="dmx-controller"}

# Request rate
rate(chimera_dmx_requests_total[5m])

# P99 latency
chimera_dmx_request_duration_seconds{quantile="0.99"}

# Error rate
rate(chimera_dmx_requests_total{status="error"}[5m]) / rate(chimera_dmx_requests_total[5m])
```

### Grafana

Visualization dashboards:

- **Admin credentials**: admin / chimera
- **Port**: 3000
- **Auto-provisioned dashboards**:
  - Phase 2 Service Overview
  - Performance Metrics
  - Business KPIs

### AlertManager

Alert routing and management:

- **Port**: 9093
- **Configuration**: `alertmanager/alertmanager.yml`
- **Default behavior**: Logs alerts (can be configured for webhooks)

### Jaeger

Distributed tracing:

- **Port**: 16686 (UI)
- **Agent**: 6831 (UDP)
- See `distributed-tracing/README.md` for details

## Metrics Reference

### DMX Controller Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `chimera_dmx_requests_total` | Counter | Total requests |
| `chimera_dmx_request_duration_seconds` | Histogram | Request latency |
| `chimera_dmx_scene_activations_total` | Counter | Scene activations |
| `chimera_dmx_active_fixtures` | Gauge | Active fixtures |
| `chimera_dmx_emergency_stop_active` | Gauge | Emergency stop state |

### Audio Controller Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `chimera_audio_requests_total` | Counter | Total requests |
| `chimera_audio_request_duration_seconds` | Histogram | Request latency |
| `chimera_audio_playing_tracks` | Gauge | Playing tracks |
| `chimera_audio_emergency_mute_active` | Gauge | Emergency mute state |

### BSL Avatar Service Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `chimera_bsl_requests_total` | Counter | Total requests |
| `chimera_bsl_request_duration_seconds` | Histogram | Request latency |
| `chimera_bsl_library_hit_rate` | Gauge | Translation cache hit rate |
| `chimera_bsl_words_translated_total` | Counter | Words translated |

## Alerting Rules

### Critical Alerts

- **Service Down**: Any service unreachable for >1 minute
- **Emergency State**: Emergency stop/mute active

### Warning Alerts

- **High Latency**: P99 > 1 second for >5 minutes
- **High Error Rate**: Error rate > 5% for >5 minutes

### Info Alerts

- **Low Activity**: Scene activation rate drops below threshold
- **Translation Quality**: BSL library hit rate drops

## Configuration Files

### Prometheus

- **Config**: `prometheus/prometheus.yml`
- **Rules**: `prometheus/rules/alerts.yml`
- **Data**: Docker volume `prometheus-data`

### Grafana

- **Datasources**: `grafana/provisioning/datasources/`
- **Dashboards**: `grafana/dashboards/`
- **Data**: Docker volume `grafana-data`

### AlertManager

- **Config**: `alertmanager/alertmanager.yml`
- **Data**: Docker volume `alertmanager-data`

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f monitoring/docker-compose.monitoring.yml logs

# Check network
docker network inspect chimera-network

# Restart services
./monitoring/setup-monitoring.sh --action stop
./monitoring/setup-monitoring.sh --action start
```

### No Metrics Appearing

1. Verify services are running:
   ```bash
   curl http://localhost:8001/metrics
   curl http://localhost:8002/metrics
   curl http://localhost:8003/metrics
   ```

2. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Verify all targets are "UP"

3. Check network connectivity:
   ```bash
   docker network inspect chimera-network
   ```

### Alerts Not Firing

1. Check rule syntax:
   ```bash
   docker exec chimera-prometheus promtool check rules /etc/prometheus/rules/alerts.yml
   ```

2. Verify AlertManager is configured:
   ```bash
   curl http://localhost:9093/api/v1/status
   ```

## Maintenance

### Backup Data

```bash
# Backup Prometheus data
docker run --rm \
  -v chimera_prometheus-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-data-$(date +%Y%m%d).tar.gz /data

# Backup Grafana data
docker run --rm \
  -v chimera_grafana-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/grafana-data-$(date +%Y%m%d).tar.gz /data
```

### Clean Old Data

Prometheus automatically retains 30 days of data. To change retention:

Edit `docker-compose.monitoring.yml`:
```yaml
command:
  - '--storage.tsdb.retention.time=60d'  # Change to 60 days
```

### Update Dashboards

1. Edit dashboard JSON files in `grafana/dashboards/`
2. Restart Grafana:
   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml restart grafana
   ```

## Performance Tuning

### High Traffic Volumes

For high traffic scenarios, adjust Prometheus scrape interval:

```yaml
scrape_configs:
  - job_name: 'dmx-controller'
    scrape_interval: 30s  # Reduce from 15s
    scrape_timeout: 10s
```

### Memory Optimization

If Prometheus uses too much memory:

```yaml
command:
  - '--storage.tsdb.retention.time=15d'  # Reduce retention
  - '--query.max-samples=10000000'  # Limit query samples
```

## Integration with Services

### Adding Metrics to Your Service

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
request_counter = Counter(
    'my_service_requests_total',
    'Total requests',
    ['method', 'status']
)

request_duration = Histogram(
    'my_service_request_duration_seconds',
    'Request latency'
)

# Start metrics server
start_http_server(8000)
```

### Exposing Metrics Endpoint

Your service should expose metrics at `/metrics`:

```python
from prometheus_client import generate_latest

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

## Security Considerations

### Production Deployment

1. **Change default passwords** in Grafana
2. **Enable authentication** for Prometheus
3. **Use TLS** for all endpoints
4. **Restrict network access** with firewalls
5. **Secure AlertManager webhooks**

### Firewall Rules

```bash
# Allow monitoring from internal network only
ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
ufw allow from 10.0.0.0/8 to any port 3000  # Grafana
```

## Next Steps

1. **Configure alert notifications**: Edit `alertmanager/alertmanager.yml`
2. **Create custom dashboards**: Import JSON to Grafana
3. **Set up alert routing**: Configure webhook endpoints
4. **Tune alert thresholds**: Adjust `prometheus/rules/alerts.yml`

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)

## License

MIT License - See Project Chimera LICENSE file for details.
