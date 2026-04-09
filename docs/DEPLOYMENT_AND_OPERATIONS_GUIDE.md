# Project Chimera Phase 2 - Deployment and Operations Guide

**Version:** 1.0.0
**Date:** April 9, 2026
**Target Audience:** DevOps Engineers, System Administrators, Technical Operators

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Deployment Procedures](#deployment-procedures)
5. [Operations Runbooks](#operations-runbooks)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Backup and Recovery](#backup-and-recovery)
8. [Maintenance Procedures](#maintenance-procedures)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Emergency Procedures](#emergency-procedures)

---

## Overview

This guide provides comprehensive procedures for deploying and operating Project Chimera Phase 2 services in production environments. It covers the complete lifecycle from initial deployment through ongoing operations and maintenance.

### Services Covered

- **DMX Controller Service** (Port 8001) - DMX512 lighting control
- **Audio Controller Service** (Port 8002) - Audio system control
- **BSL Avatar Service** (Port 8003) - British Sign Language translation
- **Monitoring Stack** - Prometheus (9090), Grafana (3000)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer / API Gateway               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌─────▼──────┐  ┌────────▼────────┐
│ DMX Controller │  │   Audio    │  │  BSL Avatar    │
│   :8001        │  │ Controller │  │   Service       │
│                │  │   :8002    │  │    :8003        │
└───────┬────────┘  └─────┬──────┘  └────────┬────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  ┌────────▼────────┐
                  │  Prometheus     │
                  │     :9090       │
                  └─────────────────┘
                           │
                  ┌────────▼────────┐
                  │    Grafana      │
                  │     :3000       │
                  └─────────────────┘
```

---

## Pre-Deployment Checklist

### Hardware Requirements

**Minimum Specifications:**
- CPU: 4 cores (x86_64)
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 1 Gbps

**Recommended Specifications:**
- CPU: 8 cores (x86_64)
- RAM: 16 GB
- Storage: 100 GB NVMe SSD
- Network: 10 Gbps

### Hardware Interfaces

**DMX Controller:**
- [ ] DMX512 USB interface installed and recognized
- [ ] DMX cables connected to fixtures
- [ ] DMX terminator installed at end of chain
- [ ] Fixtures properly addressed

**Audio Controller:**
- [ ] Audio interface detected
- [ ] Speakers/amplifiers connected
- [ ] Audio files present in `/assets/audio`

**BSL Avatar Service:**
- [ ] Gesture library file present
- [ ] Sufficient storage for gesture data

### Software Prerequisites

**Operating System:**
- [ ] Ubuntu 22.04 LTS or newer
- [ ] All security patches applied
- [ ] Docker installed (v24.0+)
- [ ] Docker Compose installed (v2.20+)

**Network Configuration:**
- [ ] Firewall rules configured (see below)
- [ ] DNS entries configured
- [ ] SSL/TLS certificates obtained
- [ ] Time synchronization (NTP) configured

**Required Ports:**
```
8001 - DMX Controller API
8002 - Audio Controller API
8003 - BSL Avatar Service API
9090 - Prometheus
3000 - Grafana
```

### Security Checklist

- [ ] SSL certificates installed and valid
- [ ] Firewall configured (see Firewall Rules below)
- [ ] Rate limiting enabled
- [ ] Authentication configured
- [ ] Monitoring configured
- [ ] Log aggregation enabled
- [ ] Backup systems configured
- [ ] Emergency procedures tested

### Documentation

- [ ] This deployment guide reviewed
- [ ] Security documentation reviewed
- [ ] API documentation available
- [ ] Runbooks accessible to operations team
- [ ] Emergency contact list distributed

---

## Environment Setup

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git nginx python3-pip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. User and Group Setup

```bash
# Create chimera user
sudo useradd -m -s /bin/bash chimera

# Add to required groups
sudo usermod -aG docker,audio,dialout chimera
```

### 3. Directory Structure

```bash
# Create directory structure
sudo mkdir -p /opt/chimera
sudo mkdir -p /opt/chimera/services
sudo mkdir -p /opt/chimera/config
sudo mkdir -p /opt/chimera/logs
sudo mkdir -p /opt/chimera/data/gestures
sudo mkdir -p /opt/chimera/assets/audio
sudo mkdir -p /opt/chimera/backups
sudo mkdir -p /opt/chimera/monitoring

# Set permissions
sudo chown -R chimera:chimera /opt/chimera
chmod 750 /opt/chimera
chmod 750 /opt/chimera/services
chmod 770 /opt/chimera/data
```

### 4. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Allow Chimera service ports
sudo ufw allow 8001/tcp  # DMX Controller
sudo ufw allow 8002/tcp  # Audio Controller
sudo ufw allow 8003/tcp  # BSL Avatar Service
sudo ufw allow 9090/tcp  # Prometheus (restrict in production)
sudo ufw allow 3000/tcp  # Grafana (restrict in production)

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 5. SSL/TLS Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d chimera.example.com

# Auto-renewal (configured by default)
sudo certbot renew --dry-run
```

### 6. Environment Variables

Create `/opt/chimera/.env`:

```bash
# Service Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production

# DMX Configuration
DMX_UNIVERSE=1
DMX_REFRESH_RATE=44
DMX_INTERFACE=/dev/ttyUSB0

# Audio Configuration
AUDIO_SAMPLE_RATE=48000
AUDIO_BIT_DEPTH=24
AUDIO_MAX_VOLUME_DB=-6

# BSL Configuration
GESTURE_LIBRARY_PATH=/opt/chimera/data/gestures/gestures.json

# Monitoring
PROMETHEUS_RETENTION=200h
GRAFANA_ADMIN_PASSWORD=CHANGE_ME

# Security
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

Set secure permissions:
```bash
chmod 600 /opt/chimera/.env
chown chimera:chimera /opt/chimera/.env
```

---

## Deployment Procedures

### Option 1: Docker Compose Deployment (Recommended)

#### 1. Clone Repository

```bash
cd /opt/chimera
sudo -u chimera git clone https://github.com/ranjrana2012-lab/project-chimera.git .
```

#### 2. Build Services

```bash
cd /opt/chimera/services
sudo -u chimera docker-compose -f docker-compose.phase2.yml build
```

#### 3. Start Services

```bash
# Start all services
sudo -u chimera docker-compose -f docker-compose.phase2.yml up -d

# Check status
sudo -u chimera docker-compose -f docker-compose.phase2.yml ps

# View logs
sudo -u chimera docker-compose -f docker-compose.phase2.yml logs -f
```

#### 4. Verify Deployment

```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health
```

### Option 2: Systemd Service Deployment

#### 1. Create Systemd Service Files

**DMX Controller** (`/etc/systemd/system/chimera-dmx.service`):

```ini
[Unit]
Description=Project Chimera DMX Controller
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/chimera/services/dmx-controller
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=chimera
Group=chimera

[Install]
WantedBy=multi-user.target
```

**Audio Controller** (`/etc/systemd/system/chimera-audio.service`):

```ini
[Unit]
Description=Project Chimera Audio Controller
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/chimera/services/audio-controller
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=chimera
Group=chimera

[Install]
WantedBy=multi-user.target
```

**BSL Avatar Service** (`/etc/systemd/system/chimera-bsl.service`):

```ini
[Unit]
Description=Project Chimera BSL Avatar Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/chimera/services/bsl-avatar-service
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=chimera
Group=chimera

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable chimera-dmx.service
sudo systemctl enable chimera-audio.service
sudo systemctl enable chimera-bsl.service

# Start services
sudo systemctl start chimera-dmx.service
sudo systemctl start chimera-audio.service
sudo systemctl start chimera-bsl.service

# Check status
sudo systemctl status chimera-dmx.service
sudo systemctl status chimera-audio.service
sudo systemctl status chimera-bsl.service
```

### Option 3: Kubernetes Deployment

For large-scale deployments, use the provided Kubernetes manifests:

```bash
# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/dmx-controller.yaml
kubectl apply -f k8s/audio-controller.yaml
kubectl apply -f k8s/bsl-avatar-service.yaml

# Apply monitoring
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml

# Verify deployment
kubectl get pods -n chimera
kubectl get services -n chimera
```

### Post-Deployment Steps

#### 1. Configure Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/chimera
upstream dmx_controller {
    server localhost:8001;
}

upstream audio_controller {
    server localhost:8002;
}

upstream bsl_avatar {
    server localhost:8003;
}

server {
    listen 80;
    server_name chimera.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chimera.example.com;

    ssl_certificate /etc/letsencrypt/live/chimera.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chimera.example.com/privkey.pem;

    # DMX Controller
    location /api/dmx/ {
        proxy_pass http://dmx_controller/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Audio Controller
    location /api/audio/ {
        proxy_pass http://audio_controller/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # BSL Avatar Service
    location /api/bsl/ {
        proxy_pass http://bsl_avatar/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/chimera /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 2. Configure Monitoring

Import Grafana dashboards:
```bash
# Access Grafana at http://localhost:3000
# Login with admin/admin (change password)

# Add Prometheus data source
# URL: http://prometheus:9090

# Import dashboards from monitoring/grafana/dashboards/
```

#### 3. Setup Log Rotation

Create `/etc/logrotate.d/chimera`:

```
/opt/chimera/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 chimera chimera
    sharedscripts
    postrotate
        docker-compose -f /opt/chimera/services/docker-compose.phase2.yml exec -T chimera-dmx-controller kill -USR1 1
    endscript
}
```

#### 4. Configure Automated Backups

Create backup script `/opt/chimera/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/chimera/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup configuration
cp -r /opt/chimera/config "$BACKUP_DIR/$DATE/"
cp /opt/chimera/.env "$BACKUP_DIR/$DATE/"

# Backup data
cp -r /opt/chimera/data "$BACKUP_DIR/$DATE/"

# Backup databases (if applicable)
# docker exec chimera-db pg_dump -U chimera chimera_db > "$BACKUP_DIR/$DATE/database.sql"

# Compress backup
tar -czf "$BACKUP_DIR/chimera_backup_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"

# Clean old backups
find "$BACKUP_DIR" -name "chimera_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: chimera_backup_$DATE.tar.gz"
```

Make executable and add to crontab:
```bash
chmod +x /opt/chimera/scripts/backup.sh
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/chimera/scripts/backup.sh >> /opt/chimera/logs/backup.log 2>&1
```

---

## Operations Runbooks

### Daily Operations

#### Morning Checklist

- [ ] Check service status: `docker-compose ps`
- [ ] Review logs for errors: `docker-compose logs --tail=100`
- [ ] Check Grafana dashboards for anomalies
- [ ] Verify disk space: `df -h`
- [ ] Check backup completion: `tail /opt/chimera/logs/backup.log`

#### Health Monitoring

```bash
# All-in-one health check
#!/bin/bash
services=("dmx-controller:8001" "audio-controller:8002" "bsl-avatar-service:8003")

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"
    if curl -sf "http://localhost:$port/health" > /dev/null; then
        echo "✓ $name is healthy"
    else
        echo "✗ $name is UNHEALTHY"
    fi
done
```

### Weekly Operations

#### Review Metrics

- Check Prometheus for service performance
- Review error rates and response times
- Analyze resource utilization trends
- Verify alert configurations

#### Security Audit

- Review authentication logs
- Check for failed login attempts
- Verify SSL certificate expiration
- Review rate limiting violations

#### Backup Verification

- Test restore procedure
- Verify backup integrity
- Confirm backup retention policy

### Monthly Operations

#### Maintenance Tasks

- Apply security patches
- Update Docker images
- Review and update documentation
- Conduct disaster recovery drill

#### Performance Review

- Analyze service performance trends
- Identify optimization opportunities
- Review capacity planning
- Update resource allocations if needed

---

## Monitoring and Alerting

### Prometheus Metrics

Each service exposes the following metrics:

**DMX Controller:**
- `dmx_controller_state` - Service state (1=running, 0=stopped)
- `dmx_controller_fixture_count` - Number of configured fixtures
- `dmx_controller_scene_count` - Number of scenes
- `dmx_controller_channel_changes_total` - Total channel changes
- `dmx_controller_scene_activations_total` - Total scene activations
- `dmx_controller_emergency_stop_total` - Emergency stop count

**Audio Controller:**
- `audio_controller_state` - Service state
- `audio_controller_track_count` - Number of tracks
- `audio_controller_playing_tracks` - Currently playing tracks
- `audio_controller_muted_tracks` - Currently muted tracks
- `audio_controller_master_volume_db` - Master volume level
- `audio_controller_track_volume_db` - Per-track volume
- `audio_controller_emergency_mute_total` - Emergency mute count

**BSL Avatar Service:**
- `bsl_avatar_service_state` - Service state
- `bsl_avatar_service_gesture_library_size` - Number of gestures
- `bsl_avatar_service_translation_total` - Total translations
- `bsl_avatar_service_translation_gestures_from_library_total` - Library hits
- `bsl_avatar_service_translation_gestures_fingerspelled_total` - Fingerspelling count
- `bsl_avatar_service_translation_duration_seconds` - Translation duration

### Alerting Rules

Key alerts configured in `monitoring/alerting_rules.yml`:

1. **Service Down Alert**
   - Trigger: Service health check fails for 2 minutes
   - Severity: Critical
   - Action: Page on-call engineer

2. **High Error Rate**
   - Trigger: Error rate > 5% for 5 minutes
   - Severity: Warning
   - Action: Investigate logs

3. **Emergency Stop/Mute**
   - Trigger: Emergency stop/mute activated
   - Severity: Critical
   - Action: Immediate notification

4. **High Response Time**
   - Trigger: p95 response time > 1 second
   - Severity: Warning
   - Action: Performance investigation

5. **Disk Space Low**
   - Trigger: Disk usage > 80%
   - Severity: Warning
   - Action: Plan capacity expansion

### Grafana Dashboards

Pre-configured dashboards available:

1. **Service Overview** (`service-overview.json`)
   - Overall service health
   - Request rates
   - Response times
   - Error rates

2. **DMX Controller** (`dmx-controller.json`)
   - Fixture status
   - Scene activations
   - Channel change rates
   - Emergency stop events

3. **Audio Controller** (`audio-controller.json`)
   - Track status
   - Volume levels
   - Muted tracks
   - Emergency mute events

4. **BSL Avatar Service** (`bsl-avatar-service.json`)
   - Translation rates
   - Library hit rates
   - Fingerspelling usage
   - Translation duration

---

## Backup and Recovery

### Backup Strategy

**What to Backup:**
- Configuration files (`/opt/chimera/config/`)
- Environment variables (`/opt/chimera/.env`)
- Data files (`/opt/chimera/data/`)
- Audio assets (`/opt/chimera/assets/audio/`)
- Gesture library (`/opt/chimera/data/gestures/`)
- Docker volumes (if using persistent volumes)

**Backup Schedule:**
- **Daily**: Incremental backups
- **Weekly**: Full backups
- **Monthly**: Archive to off-site storage

**Backup Retention:**
- Daily backups: 14 days
- Weekly backups: 8 weeks
- Monthly backups: 12 months

### Recovery Procedures

#### Service Recovery

```bash
# Stop affected services
docker-compose -f docker-compose.phase2.yml stop <service>

# Restore from backup
tar -xzf /opt/chimera/backups/chimera_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/
cp -r /tmp/YYYYMMDD_HHMMSS/config/* /opt/chimera/config/
cp -r /tmp/YYYYMMDD_HHMMSS/data/* /opt/chimera/data/

# Restart service
docker-compose -f docker-compose.phase2.yml start <service>
```

#### Complete System Recovery

```bash
# Stop all services
docker-compose -f docker-compose.phase2.yml down

# Restore system configuration
tar -xzf /opt/chimera/backups/chimera_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/

# Restore configuration
cp -r /tmp/YYYYMMDD_HHMMSS/config/* /opt/chimera/config/
cp /tmp/YYYYMMDD_HHMMSS/.env /opt/chimera/.env

# Restore data
cp -r /tmp/YYYYMMDD_HHMMSS/data/* /opt/chimera/data/
cp -r /tmp/YYYYMMDD_HHMMSS/assets/* /opt/chimera/assets/

# Restart all services
docker-compose -f docker-compose.phase2.yml up -d
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours

**Disaster Recovery Site:**
- Maintain hot standby at secondary location
- Replicate backups to off-site storage
- Test disaster recovery procedures quarterly

---

## Maintenance Procedures

### Rolling Updates

#### 1. Update One Service at a Time

```bash
# Pull latest image
docker-compose -f docker-compose.phase2.yml pull dmx-controller

# Stop service
docker-compose -f docker-compose.phase2.yml stop dmx-controller

# Backup current version
docker-compose -f docker-compose.phase2.yml ps dmx-controller

# Start updated service
docker-compose -f docker-compose.phase2.yml up -d dmx-controller

# Verify health
curl http://localhost:8001/health

# Repeat for other services
```

#### 2. Rollback Procedure

```bash
# Stop current version
docker-compose -f docker-compose.phase2.yml stop dmx-controller

# Revert to previous image
docker tag chimera-dmx-controller:previous chimera-dmx-controller:latest

# Start previous version
docker-compose -f docker-compose.phase2.yml up -d dmx-controller

# Verify rollback
curl http://localhost:8001/health
```

### Service Migration

#### Moving to New Host

```bash
# On old host: Stop services and export data
docker-compose -f docker-compose.phase2.yml down
tar -czf chimera_migration.tar.gz /opt/chimera

# Transfer to new host
scp chimera_migration.tar.gz user@new-host:/tmp/

# On new host: Extract and start
cd /opt
tar -xzf /tmp/chimera_migration.tar.gz
cd /opt/chimera/services
docker-compose -f docker-compose.phase2.yml up -d
```

### Database Maintenance

If using databases:

```bash
# Connect to database
docker exec -it chimera-db psql -U chimera chimera_db

# Run maintenance queries
VACUUM ANALYZE;
REINDEX DATABASE chimera_db;

# Check database size
SELECT pg_size_pretty(pg_database_size('chimera_db'));
```

---

## Troubleshooting Guide

### Common Issues

#### Service Won't Start

**Symptoms:**
- Container exits immediately
- Health check fails
- Port already in use

**Diagnosis:**
```bash
# Check container logs
docker-compose logs dmx-controller

# Check port usage
sudo netstat -tulpn | grep 8001

# Check container status
docker ps -a
```

**Solutions:**
1. Check logs for error messages
2. Verify configuration files
3. Ensure required hardware is connected
4. Check port availability
5. Verify environment variables

#### High Memory Usage

**Symptoms:**
- Container OOM killed
- System swapping
- Slow response times

**Diagnosis:**
```bash
# Check container resource usage
docker stats

# Check system memory
free -h

# Check memory limits
docker inspect chimera-dmx-controller | grep Memory
```

**Solutions:**
1. Increase container memory limits
2. Restart affected services
3. Investigate memory leaks
4. Scale horizontally if needed

#### DMX Fixtures Not Responding

**Symptoms:**
- Commands sent but no response
- Fixtures not changing state
- Inconsistent behavior

**Diagnosis:**
```bash
# Check DMX interface
ls -l /dev/ttyUSB*

# Check service logs
docker-compose logs dmx-controller | grep DMX

# Test DMX connection
python -c "import serial; s = serial.Serial('/dev/ttyUSB0'); print(s.isOpen())"
```

**Solutions:**
1. Verify DMX interface connection
2. Check fixture addressing
3. Verify DMX terminator installed
4. Restart DMX controller service
5. Check for cable faults

#### Audio Not Playing

**Symptoms:**
- No sound output
- Audio errors in logs
- Track won't play

**Diagnosis:**
```bash
# Check audio devices
aplay -l

# Check audio service logs
docker-compose logs audio-controller

# Test audio playback
aplay /opt/chimera/assets/audio/test.wav
```

**Solutions:**
1. Verify audio device permissions
2. Check audio files exist and are readable
3. Test audio device directly
4. Restart audio controller service
5. Check volume levels

### Performance Issues

#### Slow Response Times

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" http://localhost:8001/api/status

# Check container stats
docker stats

# Check system load
uptime
```

**Solutions:**
1. Identify bottlenecks with profiling
2. Optimize database queries
3. Add caching if applicable
4. Scale resources
5. Implement rate limiting

#### High CPU Usage

**Diagnosis:**
```bash
# Check CPU usage
top

# Check container CPU
docker stats --no-stream

# Identify CPU-intensive processes
docker exec chimera-dmx-controller top
```

**Solutions:**
1. Profile application code
2. Optimize algorithms
3. Implement caching
4. Scale horizontally

---

## Emergency Procedures

### Emergency Stop (DMX)

**When to Use:**
- Unsafe lighting conditions
- Fixtures malfunctioning
- Audience safety concern
- Equipment failure

**Procedure:**

1. **Physical Emergency Stop** (Preferred)
   - Locate physical emergency stop button
   - Press and hold until all fixtures reset
   - Verify all fixtures are off

2. **Software Emergency Stop**
   ```bash
   # Via API
   curl -X POST http://localhost:8001/api/emergency_stop

   # Via Docker
   docker exec chimera-dmx-controller python -c "from dmx_controller import DMXController; c = DMXController(); c.emergency_stop()"
   ```

3. **Post-Emergency Actions**
   - Identify cause of emergency
   - Rectify unsafe condition
   - Reset from emergency state
   - Test fixtures before resuming
   - Document incident

### Emergency Mute (Audio)

**When to Use:**
- Audio malfunction
- Inappropriate content playing
- Equipment feedback
- Audience disturbance

**Procedure:**

1. **Physical Mute** (Preferred)
   - Locate audio mixer mute button
   - Press to mute all outputs
   - Verify silence

2. **Software Emergency Mute**
   ```bash
   # Via API
   curl -X POST http://localhost:8002/api/emergency_mute

   # Via Docker
   docker exec chimera-audio-controller python -c "from audio_controller import AudioController; c = AudioController(); c.emergency_mute()"
   ```

3. **Post-Emergency Actions**
   - Identify cause
   - Fix audio issue
   - Reset from mute state
   - Test audio before resuming
   - Document incident

### Service Outage

**Procedure:**

1. **Assess Impact**
   - Determine affected services
   - Check user impact
   - Estimate recovery time

2. **Communicate**
   - Notify stakeholders
   - Provide status updates
   - Set expectations

3. **Restore Service**
   - Follow recovery procedures
   - Verify functionality
   - Monitor for issues

4. **Post-Incident**
   - Document root cause
   - Implement preventive measures
   - Update runbooks if needed

### Security Incident

**Procedure:**

1. **Contain**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

2. **Assess**
   - Determine scope of breach
   - Identify affected data
   - Preserve evidence

3. **Remediate**
   - Patch vulnerabilities
   - Restore from clean backups
   - Reset all credentials

4. **Report**
   - Document incident
   - Notify authorities if required
   - Communicate with stakeholders

---

## Appendix

### A. Command Reference

**Docker Compose Commands:**
```bash
# Start services
docker-compose -f docker-compose.phase2.yml up -d

# Stop services
docker-compose -f docker-compose.phase2.yml down

# Restart service
docker-compose -f docker-compose.phase2.yml restart dmx-controller

# View logs
docker-compose -f docker-compose.phase2.yml logs -f dmx-controller

# Check status
docker-compose -f docker-compose.phase2.yml ps
```

**Systemd Commands:**
```bash
# Check service status
sudo systemctl status chimera-dmx.service

# Restart service
sudo systemctl restart chimera-dmx.service

# View logs
sudo journalctl -u chimera-dmx.service -f
```

### B. Network Configuration

**Default Ports:**
- DMX Controller: 8001
- Audio Controller: 8002
- BSL Avatar Service: 8003
- Prometheus: 9090
- Grafana: 3000

**Firewall Rules:**
```bash
# Allow service communication
sudo ufw allow from 10.0.0.0/8 to any port 8001:8003 proto tcp

# Restrict monitoring to admin network
sudo ufw allow from 10.0.1.0/24 to any port 9090 proto tcp
sudo ufw allow from 10.0.1.0/24 to any port 3000 proto tcp
```

### C. Resource Limits

**Recommended Resource Limits:**

```yaml
# docker-compose.override.yml
services:
  dmx-controller:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  audio-controller:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  bsl-avatar-service:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
```

### D. Contact Information

**Emergency Contacts:**
- Technical Lead: [Name] - [Phone] - [Email]
- System Administrator: [Name] - [Phone] - [Email]
- On-Call Engineer: [Rotation Schedule]

**Vendor Contacts:**
- DMX Equipment Vendor: [Contact]
- Audio Equipment Vendor: [Contact]
- IT Support: [Contact]

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026
**Next Review:** July 9, 2026

**Owner:** Project Chimera Operations Team
**Approvers:** Technical Lead, DevOps Manager
