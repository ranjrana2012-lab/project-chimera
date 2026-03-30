# Production Environment Configuration Guide

**Date**: 2026-03-30
**Purpose**: Secure production deployment configuration for Project Chimera

---

## Overview

This guide provides the complete production environment configuration for deploying Project Chimera securely. Follow these steps before deploying to production.

---

## Pre-Deployment Checklist

### Security Configuration

#### 1. Generate Secure Passwords

Generate unique, strong passwords for all production systems:

```bash
# Grafana admin password
openssl rand -base64 32

# Neo4j database password
openssl rand -base64 32

# PostgreSQL database password (if using)
openssl rand -base64 32

# Redis password (if using AUTH)
openssl rand -base64 32

# JWT secret keys
openssl rand -hex 32
```

#### 2. Configure Environment Variables

Create a production `.env` file:

```bash
# Copy the example file
cp .env.example .env.production

# Edit with production values
nano .env.production
```

### Required Production Variables

```bash
# ============================================================================
# ENVIRONMENT
# ============================================================================
ENVIRONMENT=production
LOG_LEVEL=WARNING  # Reduce logging in production

# ============================================================================
# SECURITY
# ============================================================================
# CORS Configuration (comma-separated list of allowed origins)
CORS_ORIGINS=https://chimera.example.com,https://admin.chimera.example.com

# ============================================================================
# DATABASES
# ============================================================================
GRAFANA_ADMIN_PASSWORD=YOUR_GENERATED_PASSWORD_HERE
GRAPH_DB_PASSWORD=YOUR_GENERATED_PASSWORD_HERE
POSTGRES_PASSWORD=YOUR_GENERATED_PASSWORD_HERE
REDIS_PASSWORD=YOUR_GENERATED_PASSWORD_HERE

# ============================================================================
# API KEYS (Never commit these to git!)
# ============================================================================
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ZAI_API_KEY=your-zai-api-key-here

# ============================================================================
# SECRETS
# ============================================================================
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# ============================================================================
# RATE LIMITING
# ============================================================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ============================================================================
# MONITORING
# ============================================================================
OTLP_ENDPOINT=http://jaeger:4317
ENABLE_TRACING=true
PROMETHEUS_RETENTION_TIME=30d
```

### Forbidden Variables (Never use in production)

```bash
# ❌ NEVER USE THESE IN PRODUCTION
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
ALLOWED_HOSTS=*
```

---

## Service-Specific Configuration

### OpenClaw Orchestrator (Port 8000)

```bash
SERVICE_NAME=openclaw-orchestrator
PORT=8000
WORKERS=4
MAX_REQUEST_SIZE=10485760  # 10MB

# Agent URLs (use service names for Kubernetes)
SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
CAPTIONING_AGENT_URL=http://captioning-agent:8002
BSL_AGENT_URL=http://bsl-agent:8003
SENTIMENT_AGENT_URL=http://sentiment-agent:8004
LIGHTING_SOUND_MUSIC_URL=http://lighting-sound-music:8005
SAFETY_FILTER_URL=http://safety-filter:8006
```

### Neo4j Graph Database (Port 7474/7687)

```bash
NEO4J_AUTH=neo4j/YOUR_SECURE_PASSWORD
NEO4J_dbms_memory_heap_initial__size=512m
NEO4J_dbms_memory_heap_max__size=2G
NEO4J_dbms_memory_pagecache_size=1g
```

### Grafana (Port 3000)

```bash
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=YOUR_SECURE_PASSWORD
GF_USERS_ALLOW_SIGN_UP=false
GF_INSTALL_PLUGINS=
GF_SERVER_ROOT_URL=https://grafana.chimera.example.com
```

### Prometheus (Port 9090)

```bash
# Retention
PROMETHEUS_RETENTION_TIME=15d
PROMETHEUS_RETENTION_SIZE=10GB

# Storage
PROMETHEUS_STORAGE_TSDB_RETENTION_TIME=15d
PROMETHEUS_STORAGE_TSDB_PATH=/prometheus
```

---

## Network Configuration

### Firewall Rules

```bash
# UFW Rules (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw enable

# Docker-specific rules (CRITICAL for security)
sudo iptables -I DOCKER-USER -i eth0 -j DROP
sudo iptables -I DOCKER-USER -i eth0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo netfilter-persistent save
```

### Tailscale VPN (for admin access)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Enable SSH through Tailscale
sudo tailscale up --ssh
```

---

## TLS/SSL Configuration

### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate for your domain
sudo certbot certonly --standalone -d chimera.example.com

# Certificate location
/etc/letsencrypt/live/chimera.example.com/fullchain.pem
/etc/letsencrypt/live/chimera.example.com/privkey.pem
```

### Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/chimera
server {
    listen 80;
    server_name chimera.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chimera.example.com;

    ssl_certificate /etc/letsencrypt/live/chimera.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chimera.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to OpenClaw Orchestrator
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Kubernetes Configuration

### Namespace and Resource Limits

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chimera-production
  labels:
    name: chimera-production
    environment: production

---
# kubernetes/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: chimera-production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi

---
# kubernetes/limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: chimera-production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

### Pod Security Policies

```yaml
# kubernetes/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: chimera-restricted
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfiles: 'runtime/default'
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
```

---

## Secrets Management

### Using Kubernetes Secrets

```bash
# Create secrets from files
kubectl create secret generic chimera-secrets \
  --from-literal=grafana-admin-password='YOUR_PASSWORD' \
  --from-literal=neo4j-password='YOUR_PASSWORD' \
  --from-literal=jwt-secret='YOUR_SECRET' \
  --namespace=chimera-production

# Create TLS secret
kubectl create secret tls chimera-tls \
  --cert=/path/to/fullchain.pem \
  --key=/path/to/privkey.pem \
  --namespace=chimera-production
```

### Environment Variables from Secrets

```yaml
# kubernetes/deployment-with-secrets.yaml
env:
  - name: GRAFANA_ADMIN_PASSWORD
    valueFrom:
      secretKeyRef:
        name: chimera-secrets
        key: grafana-admin-password
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: chimera-secrets
        key: jwt-secret
```

---

## Monitoring & Alerting

### Prometheus Alerts

```yaml
# prometheus/alerts.yaml
groups:
  - name: chimera_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: ServiceDown
        expr: up{job="chimera-*"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
```

### Grafana Dashboards

Import the following dashboards:
- `config/grafana/dashboards/service-health.json`
- `config/grafana/dashboards/infrastructure.json`
- `config/grafana/dashboards/incident-response.json`

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Neo4j backup
docker exec neo4j neo4j-admin backup --backup-dir=/backups --from=all

# Prometheus backup
kubectl exec -n chimera-production prometheus-0 -- tar -czf /tmp/prometheus-backup.tar.gz /prometheus
kubectl cp chimera-production/prometheus-0:/tmp/prometheus-backup.tar.gz ./backups/
```

### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup-production.sh

BACKUP_DIR="/backups/chimera/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup Neo4j
docker exec neo4j neo4j-admin backup --backup-dir=/tmp/backup --from=all
docker cp neo4j:/tmp/backup "$BACKUP_DIR/neo4j-backup"

# Backup Grafana
kubectl get configmap chimera-grafana -o yaml > "$BACKUP_DIR/grafana-configmap.yaml"

# Encrypt backup
gpg --encrypt --recipient admin@chimera.example.com "$BACKUP_DIR/*"
rm -rf "$BACKUP_DIR"/*.yaml "$BACKUP_DIR"/*-backup

# Upload to S3
aws s3 sync "$BACKUP_DIR" s3://chimera-backups/$(date +%Y%m%d)/
```

---

## Incident Response

### Emergency Contacts

```bash
# On-call rotation
ON_CALL_EMAIL=oncall@chimera.example.com
ON_CALL_PHONE=+1234567890

# Alerting channels
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
PAGERDUTY_API_KEY=your-pagerduty-key
```

### Incident Severity Levels

| Level | Response Time | Examples |
|-------|---------------|----------|
| **P1 - Critical** | 15 minutes | Service down, data loss, security breach |
| **P2 - High** | 1 hour | Degraded performance, partial outage |
| **P3 - Medium** | 4 hours | Non-critical bugs, UI issues |
| **P4 - Low** | 1 day | Minor issues, documentation updates |

---

## Post-Deployment Verification

```bash
# Health check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8011; do
  curl -sf http://localhost:$port/health/live || echo "FAIL: Port $port"
done

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Grafana dashboards
curl http://localhost:3000/api/search

# Check security headers
curl -I http://localhost:8000/health | grep -E "X-Frame-Options|X-Content-Type-Options"

# Test CORS (should not return Access-Control-Allow-Origin for evil.com)
curl -H "Origin: http://evil.com" http://localhost:8000/health -I
```

---

## Rollback Procedure

If deployment fails:

```bash
# Rollback to previous version
kubectl rollout undo deployment/chimera-orchestrator -n chimera-production

# Check rollout status
kubectl rollout status deployment/chimera-orchestrator -n chimera-production

# If complete rollback needed
helm rollback chimera-production --namespace chimera-production
```

---

**Generated**: 2026-03-30
**Status**: ✅ Ready for Production Deployment
**Version**: 1.0.0
