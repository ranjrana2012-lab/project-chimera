# Netdata Monitoring - Runbook and Guide

**Last Updated**: March 30, 2026
**Version**: 1.0.0
**Status**: Development Environment

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Dashboard Navigation](#dashboard-navigation)
4. [Key Charts and Metrics](#key-charts-and-metrics)
5. [Alert Configuration](#alert-configuration)
6. [Integration with Prometheus/Grafana](#integration-with-prometheusgrafana)
7. [Troubleshooting](#troubleshooting)
8. [Common Workflows](#common-workflows)

---

## Overview

Netdata provides real-time infrastructure health monitoring for Project Chimera, complementing the existing Prometheus/Grafana stack.

### What Netdata Monitors

| Category | Metrics | Update Frequency |
|----------|---------|------------------|
| **System CPU** | Per-core usage, interrupts, context switches | 1 second |
| **Memory** | RAM, swap, slab, huge pages, fragmentation | 1 second |
| **Disk I/O** | Per-device IOPS, throughput, latency, queue depth | 1 second |
| **Network** | Interface bandwidth, errors, drops, TCP states | 1 second |
| **Processes** | Per-process CPU, memory, I/O, threads, FDs | 1 second |
| **GPU** | NVIDIA utilization, memory, temperature, power | 1 second |
| **Containers** | Per-container resource usage | 1 second |
| **Applications** | Redis, Kafka, PostgreSQL stats | 1 second |

### Netdata vs. Prometheus/Grafana

| Tool | Focus | Granularity | Use Case |
|------|-------|-------------|----------|
| **Netdata** | Infrastructure health | 1 second | Immediate troubleshooting |
| **Prometheus** | Application metrics | 15 seconds | Historical analysis, SLO tracking |
| **Grafana** | Business KPIs, dashboards | Variable | Visualization and reporting |

---

## Quick Start

### Access Netdata Dashboard

**Development Environment**:
```
http://localhost:19999
```

**Production (when deployed)**:
```
https://netdata.chimera.theatre
```

### Starting/Stopping Netdata

**Docker Compose**:
```bash
# Start Netdata
docker-compose up -d netdata

# Stop Netdata
docker-compose stop netdata

# View logs
docker-compose logs -f netdata
```

**Kubernetes**:
```bash
# View Netdata pods
kubectl get pods -n project-chimera -l app=netdata

# View logs from a specific pod
kubectl logs -n project-chimera netdata-xxxxx

# Restart Netdata on a node
kubectl delete pod -n project-chimera netdata-xxxxx
```

---

## Dashboard Navigation

### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Netdata Logo     Search Charts      Alerts   Settings      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  System Overview                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│  │    CPU     │ │   Memory   │ │    Disk    │                │
│  │   45%      │ │   2.1/8G   │ │  125 MB/s  │                │
│  └────────────┘ └────────────┘ └────────────┘                │
│                                                               │
│  Charts Section (scrollable)                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ CPU Total (all cores)                     [📊 Chart] │    │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │    │
│  │                                                      │    │
│  │ Memory Usage                                        │    │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Controls

| Action | Description |
|--------|-------------|
| **Click chart** | Expand to full-screen view with detailed stats |
| **Drag chart** | Reorder charts on dashboard |
| **Scroll** | Navigate through all charts |
| **Search** | Find specific metrics (top-right) |
| **Alarms** | View active and cleared alarms |
| **Settings** | Configure data collection, retention, alerts |

---

## Key Charts and Metrics

### Critical Charts for Project Chimera

#### 1. CPU Monitoring

**Chart**: `CPU Total (all cores)`

**What to Look For**:
- **Sustained >80%**: System is CPU-bound, may need scaling
- **High interrupt %**: Hardware issues or excessive I/O
- **High softirq %**: Network processing overhead

**Troubleshooting**:
```bash
# Check CPU usage by process (in Netdata)
# Navigate: Applications > Python >Processes
# Identify top CPU consumers

# Alternative: docker stats
docker stats --no-stream
```

#### 2. Memory Monitoring

**Chart**: `RAM Used`, `Swap Used`

**What to Look For**:
- **RAM >90%**: Approaching limit, risk of OOM
- **Swap usage increasing**: Memory pressure, may impact performance
- **Slab growth**: Possible memory leak in kernel modules

**Troubleshooting**:
```bash
# Check memory by container
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check for memory leaks
# In Netdata: Applications > Python > Memory
# Look for steady growth in RSS over time
```

#### 3. Disk I/O

**Chart**: `Disk I/O`, `Disk Backlog`, `Disk Utilization`

**What to Look For**:
- **Backlog >2**: I/O queue is building up, disk is bottleneck
- **Utilization >80%**: Disk is saturated
- **High latency**: Slow disk affecting performance

**Troubleshooting**:
```bash
# Check disk I/O by process (Netdata: Disk I/O > Applications)
# Identify which service is causing I/O load

# Check disk health
sudo smartctl -a /dev/sda
```

#### 4. Network Monitoring

**Chart**: `Network Interfaces`, `TCP Connections`

**What to Look For**:
- **Interface errors/drops**: Network issues, faulty hardware
- **Connection count**: Too many connections (resource leak?)
- **Bandwidth saturation**: Network bottleneck

**Troubleshooting**:
```bash
# Check connection count by service
sudo netstat -anp | grep :8000 | wc -l  # Orchestrator
sudo netstat -anp | grep :8004 | wc -l  # Sentiment

# Check for TCP resets (connection issues)
sudo netstat -s | grep "connections reset"
```

#### 5. GPU Monitoring

**Chart**: `GPU NVIDIA` (if GPU available)

**What to Look For**:
- **GPU utilization >90%**: GPU is bottleneck (ML models)
- **GPU memory >90%**: May need larger GPU or model optimization
- **High temperature**: Thermal throttling risk

**Troubleshooting**:
```bash
# Check GPU processes
nvidia-smi

# Check which container is using GPU
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

#### 6. Container Statistics

**Chart**: `Docker Container CPU`, `Docker Container Memory`

**What to Look For**:
- **Resource spikes**: Service under load
- **Consistent high usage**: May need resource limits adjustment
- **Container restarts**: Check health check failures

**Troubleshooting**:
```bash
# Check container resource limits
docker inspect chimera-orchestrator | grep -A 10 "Resources"

# Check container health
docker inspect chimera-orchestrator | grep -A 5 "Health"
```

---

## Alert Configuration

### Alert Levels

| Level | Description | Example |
|-------|-------------|---------|
| **Critical** | Immediate action required | Disk full, GPU overheating |
| **Error** | Service degradation | High latency, connection failures |
| **Warning** | Potential issue | Resource usage high |
| **Info** | Informational | Service restart, config change |

### Viewing Alerts

**In Dashboard**:
1. Click **Alarms** icon (bell) in top-right
2. View active alarms (red), warnings (yellow), info (blue)
3. Click alarm to see details and history

**Slack Notifications**:
- Critical alerts → `#chimera-critical`
- All other alerts → `#chimera-alerts`

### Alert Configuration Files

**Location**: `/config/netdata/health-alarm-notify.conf`

**Key Settings**:
```bash
# Slack webhook
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}"

# Channel mapping
role_recipients_slack[system critical]="#chimera-critical"
role_recipients_slack[system warning]="#chimera-alerts"
```

### Disabling Specific Alerts

To disable redundant alerts (already handled by Prometheus):

```bash
# Edit health-alarm-notify.conf
role_recipients_slack[cpu usage]="NO"
role_recipients_slash[ram usage]="NO"
```

---

## Integration with Prometheus/Grafana

### Netdata Metrics in Prometheus

Netdata exposes metrics in Prometheus format at:
```
http://netdata:19999/api/v1/allmetrics?format=prometheus
```

**Access in Grafana**:
1. Add Prometheus as data source (already configured)
2. Query Netdata metrics with prefix: `netdata_`
3. Example query: `rate(netdata_system_cpu_percentage[1m])`

### Cross-Correlation Workflows

**Example: High Latency Investigation**

1. **Grafana shows**: API latency increased for sentiment-agent
2. **Check Netdata**:
   - CPU: High? → Service is CPU-bound
   - Memory: Swapping? → Memory pressure
   - Disk I/O: Backlog? → Disk contention
   - GPU: High? → ML model loading issue
3. **Take action** based on Netdata findings

**Example: Resource Planning**

1. **Prometheus shows**: Trend of increasing memory usage
2. **Netdata confirms**: Memory breakdown (slab, cache, application)
3. **Decision**: Is more RAM needed or is there a leak?

---

## Troubleshooting

### Netdata Not Accessible

**Symptom**: `http://localhost:19999` doesn't load

**Diagnosis**:
```bash
# Check if Netdata container is running
docker ps | grep netdata

# Check Netdata logs
docker logs chimera-netdata

# Check if port is bound
sudo netstat -tulpn | grep 19999
```

**Resolution**:
```bash
# Restart Netdata
docker-compose restart netdata

# If still not working, recreate container
docker-compose up -d --force-recreate netdata
```

### No Metrics Showing

**Symptom**: Dashboard loads but charts are empty

**Diagnosis**:
```bash
# Check if host volumes are mounted
docker inspect chimera-netdata | grep Mounts -A 20

# Verify /proc, /sys are mounted
ls -la /host/proc  # From inside container
docker exec chimera-netdata ls -la /host/proc
```

**Resolution**:
```bash
# Ensure security options are set (docker-compose.yml)
cap_add:
  - SYS_PTRACE
  - SYS_ADMIN
security_opt:
  - apparmor:unconfined

# Restart Netdata
docker-compose restart netdata
```

### GPU Monitoring Not Working

**Symptom**: GPU charts not visible

**Diagnosis**:
```bash
# Check if nvidia-smi is available
docker exec chimera-netdata nvidia-smi

# Check if GPU plugin is enabled
docker exec chimera-netdata ls -la /var/lib/netdata/plugins.d/
```

**Resolution**:
```bash
# Ensure NVIDIA runtime is available
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# If nvidia-smi not found, install NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Alerts Not Sending to Slack

**Symptom**: Alarms triggered but no Slack notifications

**Diagnosis**:
```bash
# Check Netdata logs for Slack errors
docker logs chimera-netdata | grep -i slack

# Verify environment variables
docker exec chimera-netdata env | grep SLACK
```

**Resolution**:
```bash
# Set SLACK_WEBHOOK_URL in .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Restart Netdata
docker-compose restart netdata

# Test alert (trigger a manual alarm)
# In Netdata dashboard: Settings > Alarms > Test notification
```

### High Resource Usage by Netdata

**Symptom**: Netdata using >1% CPU or >500MB RAM

**Diagnosis**:
```bash
# Check Netdata resource usage
docker stats chimera-netdata

# Check collection frequency (should be 1 second by default)
docker exec chimera-netdata cat /etc/netdata/netdata.conf | grep "update every"
```

**Resolution**:
```bash
# Reduce collection frequency (trades detail for lower usage)
# Add to netdata.conf:
# [global]
#     update every = 2  # Collect every 2 seconds instead of 1

# Restart Netdata
docker-compose restart netdata
```

---

## Common Workflows

### Workflow 1: Investigate High CPU

1. Notice high CPU in Netdata dashboard
2. Click CPU chart to expand
3. Switch to "Per-Application" view
4. Identify which service/process is consuming CPU
5. Check corresponding Grafana dashboard for application metrics
6. Take action: scale service, optimize code, or add resources

### Workflow 2: Memory Leak Detection

1. Navigate to Memory section in Netdata
2. Expand "RAM Used" chart
3. Switch to "Per-Application" view
4. Look for steady growth in RSS over time
5. Identify container with leak
6. Restart affected service
7. Create ticket for code investigation

### Workflow 3: Disk I/O Bottleneck

1. Notice high latency in services (Prometheus)
2. Check Netdata Disk I/O section
3. Look for:
   - High backlog (>2)
   - High utilization (>80%)
   - High queue depth
4. Identify which container/process is causing I/O
5. Consider:
   - Moving to faster storage
   - Distributing I/O across disks
   - Caching frequently accessed data

### Workflow 4: GPU Saturation

1. Notice ML model latency increase
2. Check Netdata GPU charts
3. Look for:
   - High GPU utilization (>90%)
   - High GPU memory usage (>90%)
   - High temperature (>80°C)
4. Identify which service is using GPU
5. Consider:
   - Smaller batch size
   - Model optimization
   - Additional GPU resources

### Workflow 5: Network Troubleshooting

1. Notice connection failures in logs
2. Check Netdata Network section
3. Look for:
   - Interface errors/drops
   - TCP connection count (too high?)
   - Bandwidth saturation
4. Identify problematic service
5. Consider:
   - Connection pooling
   - Rate limiting
   - Network interface upgrade

---

## Additional Resources

### Documentation

- [Netdata Official Documentation](https://learn.netdata.cloud/)
- [Netdata GitHub](https://github.com/netdata/netdata)
- [Prometheus Integration](https://learn.netdata.cloud/docs/agent/collectors/prometheus.plugin)

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `docker-compose.yml` | `/` | Netdata service definition |
| `health-alarm-notify.conf` | `/config/netdata/` | Alert notification settings |
| `prometheus.yml` | `/config/` | Prometheus scrape configuration |

### Support

For issues specific to Project Chimera's Netdata integration:
1. Check this runbook first
2. Search existing issues in GitHub
3. Create new issue with:
   - Netdata screenshot
   - Prometheus/Grafana screenshots
   - Logs from Netdata container
   - Description of what you were investigating

---

**Next Steps**:
- Deploy Netdata to staging environment (Phase 2)
- Configure custom alerts for Project Chimera-specific metrics
- Train on-call team on Netdata usage
- Document service-specific baselines and thresholds
