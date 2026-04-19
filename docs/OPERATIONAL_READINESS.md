# Project Chimera - Operational Readiness Guide

## System Persistence & Recovery

### Docker Restart Persistence

**Current Status:** ✅ Configured with `restart: unless-stopped`

All MVP services will automatically restart after system reboot.

**Verify persistence:**
```bash
# Check restart policy
docker inspect chimera-openclaw-orchestrator | grep -A 5 RestartPolicy

# Simulate reboot (test persistence)
sudo systemctl restart docker
docker compose -f docker-compose.mvp.yml ps

# All services should be running
./scripts/verify-stack-health.sh
```

### Service Recovery Order

Services start in this order (defined by `depends_on`):

1. **redis** - Infrastructure
2. **openclaw-orchestrator** - Core orchestration
3. **scenespeak-agent** - LLM dialogue
4. **sentiment-agent** - Sentiment analysis
5. **safety-filter** - Content moderation
6. **translation-agent** - Translation
7. **operator-console** - Web UI
8. **hardware-bridge** - DMX simulation

**Total startup time:** ~45-60 seconds (ML model loading adds 30+ seconds)

### Data Persistence

| Data Type | Storage | Persistence | Backup |
|-----------|---------|-------------|---------|
| Redis cache | Docker volume `chimera-redis-data` | ✅ Yes | Manual |
| ML models | Host mount `/app/models_cache` | ✅ Yes | Git LFS |
| Logs | Docker container | ❌ No | See below |

## Logging & Monitoring

### Current Logging Setup

**Log locations:**
```bash
# View service logs
docker compose -f docker-compose.mvp.yml logs [service-name]

# Follow logs in real-time
docker compose -f docker-compose.mvp.yml logs -f [service-name]

# All service logs
docker compose -f docker-compose.mvp.yml logs
```

**Log levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error conditions
- `CRITICAL` - Critical conditions

**Configure log level:**
```bash
# In .env file
LOG_LEVEL=DEBUG

# In docker-compose.mvp.yml
environment:
  - LOG_LEVEL=INFO
```

### Centralized Logging Setup

**Option 1: Docker Log Driver**

```bash
# Create logging directory
mkdir -p /var/log/chimera

# Update docker-compose.yml with log driver
services:
  openclaw-orchestrator:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)**

```bash
# Add to docker-compose.yml
elasticsearch:
  image: elasticsearch:8.0.0
  ports:
    - "9200:9200"
  environment:
    - discovery.type=single-node
  volumes:
    - es-data:/usr/share/elasticsearch/data

kibana:
  image: kibana:8.0.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

**Option 3: Loki + Grafana**

```bash
# Add Loki for log aggregation
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  command: -config.file=/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

### Monitoring Setup

**Health Check Script**

Already created: `scripts/verify-stack-health.sh`

**Schedule automated checks:**

```bash
# Add to crontab for every 5 minutes
crontab -e

# Add line:
*/5 * * * * /home/ranj/Project_Chimera/scripts/verify-stack-health.sh >> /var/log/chimera-health.log 2>&1
```

**Create systemd service for monitoring:**

```bash
# Create service file
sudo nano /etc/systemd/system/chimera-monitor.service
```

Content:
```ini
[Unit]
Description=Project Chimera Health Monitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/home/ranj/Project_Chimera/scripts/verify-stack-health.sh
WorkingDirectory=/home/ranj/Project_Chimera

[Install]
WantedBy=multi-user.target
```

**Create timer for periodic checks:**

```bash
sudo nano /etc/systemd/system/chimera-monitor.timer
```

Content:
```ini
[Unit]
Description=Run Chimera health check every 5 minutes
Requires=chimera-monitor.service

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable chimera-monitor.timer
sudo systemctl start chimera-monitor.timer
```

### Metrics Collection

**Prometheus + Grafana Setup**

```bash
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=chimera
  volumes:
    - grafana-data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
```

**Prometheus configuration:**

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'chimera'
    static_configs:
      - targets:
        - 'orchestrator:8000'
        - 'scenespeak:8001'
        - 'sentiment:8004'
        - 'safety:8006'
        - 'console:8007'
```

### Alerting Setup

**Email alerts (Postfix + sendmail):**

```bash
# Install mail utilities
sudo apt-get install mailutils postfix

# Test email
echo "Chimera alert test" | mail -s "Test Alert" your@email.com

# Add alert to health check script
if [ $UNHEALTHY_COUNT -gt 0 ]; then
  echo "Chimera services unhealthy: ${FAILED_SERVICES[*]}" | \
    mail -s "Chimera Alert: Services Down" your@email.com
fi
```

**Slack alerts:**

```bash
# Install webhook
pip install slackweb

# Add to health check
if [ $UNHEALTHY_COUNT -gt 0 ]; then
  curl -X POST $SLACK_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"Chimera alert: Services down - ${FAILED_SERVICES[*]}\"}"
fi
```

## Service Maintenance

### Service Health Commands

```bash
# Check all services
docker compose -f docker-compose.mvp.yml ps

# Check resource usage
docker stats

# Check specific service logs
docker logs chimera-openclaw-orchestrator --tail 100 -f

# Restart single service
docker compose -f docker-compose.mvp.yml restart sentiment-agent

# Rebuild and restart
docker compose -f docker-compose.mvp.yml up -d --build scenespeak-agent
```

### Cleanup Commands

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a

# Remove unused volumes (BE CAREFUL - deletes data!)
docker volume prune

# Clean logs older than 7 days
find /var/log/chimera -name "*.log" -mtime +7 -delete
```

## Backup & Recovery

### Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/chimera/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup Redis data
docker run --rm \
  -v chimera-redis-data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Backup models cache
docker run --rm \
  -v chimera-sentiment-models:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/models-backup.tar.gz -C /data .

# Backup configuration
cp .env "$BACKUP_DIR/"
cp docker-compose.mvp.yml "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### Restore Script

Create `scripts/restore.sh`:

```bash
#!/bin/bash
BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi

# Stop services
docker compose -f docker-compose.mvp.yml down

# Restore Redis data
docker run --rm \
  -v chimera-redis-data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar xzf /backup/redis-backup.tar.gz -C /data

# Restore models
docker run --rm \
  -v chimera-sentiment-models:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar xzf /backup/models-backup.tar.gz -C /data

# Start services
docker compose -f docker-compose.mvp.yml up -d

echo "Restore completed from: $BACKUP_DIR"
```

---

**Next Steps:**
- See `docs/DEPLOYMENT.md` for deployment procedures
- See `docs/RUNBOOK.md` for troubleshooting procedures
