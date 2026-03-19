# Migration Guide: Nemo Claw Orchestrator

This guide covers migrating to the Nemo Claw Orchestrator on DGX Spark GB0 ARM64 hardware.

## Prerequisites

### Hardware Requirements
- **DGX Spark GB0** with ARM64 architecture
- **GPU**: NVIDIA GPU with CUDA support
- **Memory**: Minimum 16GB RAM recommended
- **Storage**: 50GB free disk space

### Software Requirements
- **Docker**: 20.10+ with ARM64 support
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.25+ (if using K8s deployment)
- **Redis**: 6.0+ for state persistence
- **Nemo Claw**: Latest version installed on DGX

### Network Requirements
- All agent services must be reachable from orchestrator
- Redis port 6379 accessible
- OpenTelemetry endpoint (Jaeger) available

### Agent Services
Ensure the following services are deployed and accessible:
- SceneSpeak Agent (port 8001)
- Captioning Agent (port 8002)
- BSL Agent (port 8003)
- Sentiment Agent (port 8004)
- Lighting Agent (port 8005)
- Safety Filter (port 8006)
- Operator Console (port 8007)
- Music Generation (port 8011)
- Autonomous Agent (port 8008)

## Migration Steps

### Phase 1: Preparation

#### 1.1 Backup Current Configuration
```bash
# Backup existing orchestrator configuration
cp -r /path/to/current/orchestrator /path/to/backup/orchestrator-$(date +%Y%m%d)

# Backup Redis data (if using state persistence)
redis-cli --rdb /path/to/backup/redis-$(date +%Y%m%d).rdb
```

#### 1.2 Verify DGX Access
```bash
# Test DGX endpoint
curl http://localhost:8000/health

# Verify GPU availability
nvidia-smi

# Check Nemo Claw installation
python -c "import nvidia_nemoclaw; print(nvidia_nemoclaw.__version__)"
```

#### 1.3 Prepare Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit with your specific configuration
nano .env
```

Required environment variables:
- `DGX_ENDPOINT`: URL to DGX Nemotron service
- `REDIS_URL`: Redis connection string
- Agent URLs for all downstream services
- `NEMOTRON_MODEL`: Model name (default: nemotron-8b)

### Phase 2: Deployment

#### 2.1 Build Docker Image (ARM64)
```bash
cd services/nemoclaw-orchestrator

# Build for ARM64 architecture
docker build -t nemoclaw-orchestrator:latest --platform linux/arm64 .

# Verify image architecture
docker inspect nemoclaw-orchestrator:latest | grep Architecture
```

#### 2.2 Deploy with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f nemoclaw-orchestrator
```

#### 2.3 Deploy with Kubernetes (Alternative)
```bash
# Create namespace
kubectl apply -f manifests/deployment.yaml

# Verify deployment
kubectl get pods -n chimera

# Check service status
kubectl get svc -n chimera
```

### Phase 3: Verification

#### 3.1 Health Checks
```bash
# Liveness check
curl http://localhost:8000/health/live

# Readiness check
curl http://localhost:8000/health/ready
```

Expected responses:
```json
// Liveness
{"status": "alive", "service": "nemoclaw-orchestrator"}

// Readiness
{
  "status": "ready",
  "service": "nemoclaw-orchestrator",
  "components": {
    "policy_engine": true,
    "privacy_router": true,
    "state_machine": true,
    "state_store": true,
    "agent_coordinator": true,
    "websocket_manager": true
  }
}
```

#### 3.2 Component Verification
```bash
# Verify Redis connection
redis-cli -h localhost ping

# Check agent connectivity
curl http://localhost:8001/health
curl http://localhost:8002/health
# ... check all agents

# Verify GPU access
docker exec nemoclaw-orchestrator nvidia-smi
```

### Phase 4: Testing

#### 4.1 Orchestration Test
```bash
# Test orchestration endpoint
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Nemo Claw!"}'
```

#### 4.2 Show State Management Test
```bash
# Start a show
curl -X POST http://localhost:8000/api/show/start

# Get show state
curl http://localhost:8000/api/show/state

# End show
curl -X POST http://localhost:8000/api/show/end
```

#### 4.3 WebSocket Test
```bash
# Install websocat for testing
# cargo install websocat

# Test WebSocket connection
websocat ws://localhost:8000/ws/show
```

Send test message:
```json
{"action": "ping", "data": {}}
```

### Phase 5: Cutover

#### 5.1 Switch Traffic
```bash
# Update load balancer/proxy to point to new orchestrator
# Example for NGINX:
nano /etc/nginx/conf.d/chimera.conf

# Reload NGINX
nginx -t && nginx -s reload
```

#### 5.2 Monitor Performance
```bash
# Monitor logs
docker-compose logs -f --tail=100

# Check metrics
curl http://localhost:8000/metrics

# Monitor resource usage
docker stats nemoclaw-orchestrator
```

### Phase 6: Post-Migration

#### 6.1 Validation Checklist
- [ ] All health checks passing
- [ ] Agent connectivity verified
- [ ] Redis state persistence working
- [ ] WebSocket connections stable
- [ ] GPU accessible and utilized
- [ ] Error rates within acceptable bounds
- [ ] Performance benchmarks met

#### 6.2 Performance Benchmarks
Target metrics:
- **Orchestration latency**: < 500ms (p95)
- **Agent response time**: < 2s (p95)
- **WebSocket latency**: < 100ms
- **Memory usage**: < 4GB per instance
- **CPU usage**: < 70% average

#### 6.3 Monitoring Setup
```bash
# Configure OpenTelemetry export
export OTLP_ENDPOINT=http://jaeger:4317

# View traces in Jaeger UI
# Navigate to http://localhost:16686
```

## Rollback Procedure

If issues arise during migration:

### Immediate Rollback
```bash
# Stop new orchestrator
docker-compose down

# Restore previous version
cd /path/to/backup/orchestrator-YYYYMMDD
docker-compose up -d
```

### Database Rollback (if needed)
```bash
# Restore Redis data
redis-cli --rdb /path/to/backup/redis-YYYYMMDD.rdb
```

### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/nemoclaw-orchestrator -n chimera

# Verify rollback
kubectl get pods -n chimera
```

## Troubleshooting

### Common Issues

#### Issue: GPU Not Accessible
**Symptoms**: Errors in logs about GPU access
**Solution**:
```bash
# Verify NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Add GPU configuration to docker-compose.yml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

#### Issue: Redis Connection Failed
**Symptoms**: "Redis connection failed" in logs
**Solution**:
```bash
# Verify Redis is running
docker ps | grep redis

# Test connection
redis-cli -h localhost -p 6379 ping

# Check REDIS_URL in .env
```

#### Issue: Agent Unreachable
**Symptoms**: Agent coordinator errors
**Solution**:
```bash
# Verify agent service is running
curl http://localhost:8001/health

# Check network connectivity
docker network inspect chimera-network

# Verify agent URLs in .env
```

#### Issue: High Memory Usage
**Symptoms**: OOMKilled or high memory consumption
**Solution**:
```bash
# Increase memory limits in docker-compose.yml
services:
  nemoclaw-orchestrator:
    deploy:
      resources:
        limits:
          memory: 8Gi

# Or adjust Redis TTL
export REDIS_SHOW_STATE_TTL=3600
```

## Post-Migration Tasks

### 1. Update Documentation
- Update runbooks with new architecture
- Document any custom configurations
- Record performance baselines

### 2. Train Operations Team
- New health check procedures
- Rollback procedures
- Monitoring dashboards

### 3. Cleanup
```bash
# Remove old containers after validation
docker system prune -a

# Remove old backups (after 30 days)
find /path/to/backup -mtime +30 -delete
```

### 4. Optimize Configuration
- Tune `LOCAL_RATIO` based on privacy requirements
- Adjust agent timeouts based on observed latency
- Configure autoscaling thresholds based on load

## Support

For issues or questions:
- **Documentation**: /docs/superpowers/
- **Issues**: GitHub Issues
- **Emergency**: Contact infrastructure team

## Appendix

### A. Environment Variables Reference
See `.env.example` for complete list of environment variables.

### B. Port Mapping
| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Orchestrator | 8000 | 8000 |
| Redis | 6379 | 6379 |
| DGX Nemotron | 8000 | 8000 |

### C. Resource Requirements
| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 4GB | 8GB |
| GPU | 1 | 1 |
| Storage | 10GB | 50GB |
