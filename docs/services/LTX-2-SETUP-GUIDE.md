# LTX-2 Integration Setup Guide

## Overview

This guide provides complete setup instructions for the Visual Services Layer that integrates LTX-2 video generation with Project Chimera. This includes the Visual Core service and enhanced Sentiment Agent with video briefing capabilities.

**Status:** Phase 1: Foundation - COMPLETE ✅
**Built:** March 15, 2026
**Services:** Visual Core (8014), Enhanced Sentiment Agent (8004)

---

## Quick Start Checklist

### Step 1: Obtain LTX-2 API Key ⚠️ REQUIRED

1. Visit https://console.ltx.video
2. Sign up for an account
3. Generate your API key
4. Save your API key - you'll need it for Step 4

**Expected Cost:** LTX-2 API pricing is per-second of video generated:
- 1080p Fast: ~$0.04/second
- 1080p Pro: ~$0.06/second
- 4K Pro: ~$0.24/second

### Step 2: Build Docker Images

```bash
# Navigate to Visual Core service
cd services/visual-core

# Build the Docker image (requires Docker access)
docker build -t visual-core:latest .
```

**Alternative:** If Docker is not available, use:
```bash
# Add yourself to docker group first
sudo usermod -aG docker $USER
# Then log out and back in
```

### Step 3: Update Kubernetes Secret

Replace the placeholder API key with your actual LTX-2 API key:

```bash
kubectl create secret generic visual-core-secrets \
  --from-literal=LTX_API_KEY='sk-YOUR_ACTUAL_API_KEY_HERE' \
  --dry-run=client -o yaml | kubectl apply -n project-chimera -f -
```

**⚠️ IMPORTANT:** Never commit your actual API key to git!

### Step 4: Deploy Services

```bash
# Deploy Visual Core service
kubectl apply -f services/visual-core/k8s-deployment.yaml

# Restart Sentiment Agent (already has video capability)
kubectl rollout restart deployment/sentiment-agent -n project-chimera
```

### Step 5: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n project-chimera -l 'app in (visual-core,sentiment-agent)'

# Expected output:
# visual-core-xxx-xxx  1/1  Running  ...
# sentiment-agent-xxx  1/1  Running  ...

# Check services
kubectl get svc -n project-chimera -l 'app in (visual-core,sentiment-agent)'

# Expected output:
# sentiment-agent    ClusterIP  10.43.128.95  <none>        8004/TCP
# visual-core        ClusterIP  10.43.169.16  <none>        8014/TCP
```

### Step 6: Test the Integration

```bash
# Run the demo
cd demos
python3 visual-intelligence-demo.py
```

**Expected Output:**
- Service health checks pass
- Video generation completes successfully
- Briefing ID and video URL returned

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Project Chimera                             │
│              Visual Services Layer                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Visual Core      │         │ Sentiment Agent  │         │
│  │ Port 8014        │         │ Port 8004        │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                           │                     │
│           │ HTTP                      │                     │
│           ▼                           ▼                     │
│     ┌─────────────────────────────────────┐                │
│     │      Kubernetes (project-chimera)      │                │
│     │   • ConfigMap: Configuration        │                │
│     │   • Secret: LTX API Key ⚠️           │                │
│     │   • PVC: 100Gi video cache           │                │
│     │   • HPA: 2-8 replicas               │                │
│     └───────────────────────────────────────┘                │
│                                                              │
│           │ HTTPS API Call                                      │
│           ▼                                                     │
│     ┌─────────────────┐                                        │
│     │   LTX-2 API     │  https://api.ltx.video/v1             │
│     │   (Lightricks)   │  Text → Video + Audio (4K@50fps)       │
│     └─────────────────┘                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Details

### Visual Core Service (Port 8014)

**Purpose:** LTX-2 video generation integration hub

**API Endpoints:**
- `POST /api/v1/generate/text` - Generate video from text prompt
- `POST /api/v1/generate/prompt` - Generate video with style template
- `POST /api/v1/video/stitch` - Stitch multiple videos together
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

**Configuration:**
```yaml
Environment Variables (from ConfigMap):
  LOG_LEVEL: "INFO"
  PORT: "8014"
  LTX_API_BASE: "https://api.ltx.video/v1"
  LTX_MODEL_DEFAULT: "ltx-2-3-pro"
  LTX_MODEL_FAST: "ltx-2-fast"
  MAX_CONCURRENT_REQUESTS: "5"
  CACHE_PATH: "/app/cache/videos"
  LORA_STORAGE_PATH: "/app/models/lora"
  FFMPEG_PATH: "ffmpeg"
  OTLP_ENDPOINT: "http://jaeger:4317"

Secret (required - add your key):
  LTX_API_KEY: "your-api-key-here"  # ⚠️ Replace this!
```

**Resources:**
- CPU: 500m - 2000m (autoscales 2-8 replicas)
- Memory: 1Gi - 4Gi
- Storage: 100Gi PVC for video cache

### Enhanced Sentiment Agent (Port 8004)

**Purpose:** Sentiment analysis with video briefing generation

**New API Endpoints:**
- `POST /api/v1/video/briefing` - Create sentiment briefing video
- `GET /api/v1/video/{briefing_id}` - Get briefing status

**Configuration:**
```yaml
Environment Variables (added to ConfigMap):
  VISUAL_CORE_URL: "http://visual-core:8014"
  ENABLE_VIDEO_BRIEFING: "true"
  ENABLE_VIDEO_TRENDS: "true"
  DEFAULT_BRIEFING_DURATION: "90"
  DEFAULT_BRIEFING_STYLE: "corporate-briefing"
```

---

## Visual Style Templates

The Prompt Factory includes 5 pre-configured visual styles:

| Style | Use Case | Description |
|-------|----------|-------------|
| `corporate_briefing` | Executive briefings | Professional, clean, authoritative |
| `documentary` | Storytelling | Cinematic, observational, authentic |
| `social_media` | Social content | Fast-paced, energetic, viral |
| `news_report` | Breaking news | Urgent, credible, journalistic |
| `analytical` | Data viz | Precise, technical, informative |

---

## API Usage Examples

### Generate Video from Text Prompt

```bash
curl -X POST "http://visual-core:8014/api/v1/generate/text" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Aerial shot of modern tech office with team collaborating",
    "duration": 10,
    "resolution": "1920x1080",
    "fps": 24,
    "model": "ltx-2-3-pro",
    "generate_audio": true,
    "camera_motion": "dolly_in"
  }'
```

### Generate Video with Style Template

```bash
curl -X POST "http://visual-core:8014/api/v1/generate/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Market analysis showing strong Q1 growth",
    "style": "corporate_briefing",
    "duration": 15,
    "resolution": "1920x1080"
  }'
```

### Create Sentiment Briefing Video

```bash
curl -X POST "http://sentiment-agent:8004/api/v1/video/briefing?topic=AcmeCorp&timeframe=30d&style=corporate_briefing&duration=90"
```

---

## Troubleshooting

### Pods Not Starting (ImagePullBackOff)

**Problem:** Pods show `ImagePullBackOff` status

**Solution:** The Docker image hasn't been built or pushed to the cluster

```bash
# Build the image
cd services/visual-core
docker build -t visual-core:latest .

# If using k3s, import the image
sudo docker save visual-core:latest | sudo ctr -n k8s.io image import -

# Restart the deployment
kubectl rollout restart deployment/visual-core -n project-chimera
```

### Video Generation Failing

**Problem:** API calls to LTX-2 fail with authentication errors

**Solution:** API key not configured or invalid

```bash
# Verify the secret exists
kubectl get secret visual-core-secrets -n project-chimera

# Update with correct key
kubectl create secret generic visual-core-secrets \
  --from-literal=LTX_API_KEY='sk-YOUR_ACTUAL_KEY' \
  --dry-run=client -o yaml | kubectl apply -n project-chimera -f -

# Restart deployment
kubectl rollout restart deployment/visual-core -n project-chimera
```

### Service Communication Issues

**Problem:** Services can't reach each other

**Solution:** Check service DNS and networking

```bash
# Check services are running
kubectl get svc -n project-chimera

# Test connectivity from Visual Core to Sentiment Agent
kubectl exec -n project-chimera deployment/visual-core -- \
  curl -s http://sentiment-agent:8004/health

# Test connectivity from Sentiment Agent to Visual Core
kubectl exec -n project-chimera deployment/sentiment-agent -- \
  curl -s http://visual-core:8014/health/live
```

### FFmpeg Errors

**Problem:** Video processing fails with FFmpeg errors

**Solution:** FFmpeg may not be installed in the container

```bash
# Check FFmpeg availability
kubectl exec -n project-chimera deployment/visual-core -- which ffmpeg

# Rebuild image with FFmpeg
cd services/visual-core
docker build -t visual-core:latest . --no-cache
kubectl rollout restart deployment/visual-core -n project-chimera
```

---

## Monitoring and Metrics

### Prometheus Metrics

Visual Core exposes metrics at `/metrics`:

- `visual_core_video_generation_total` - Total video generations
- `visual_core_video_generation_duration_seconds` - Generation time histogram
- `visual_core_cache_hits_total` - Cache hit counter
- `visual_core_cache_requests_total` - Cache request counter
- `visual_core_active_generations` - Currently active generations

### Distributed Tracing

Services use OpenTelemetry with Jaeger:
- Endpoint: `http://jaeger:4317`
- Traces all video generation requests
- Tracks API calls to LTX-2

### Logs

View logs for debugging:

```bash
# Visual Core logs
kubectl logs -n project-chimera deployment/visual-core -f

# Sentiment Agent logs
kubectl logs -n project-chimera deployment/sentiment-agent -f
```

---

## Cost Considerations

### LTX-2 API Usage

| Resolution | Model | Duration | Cost |
|------------|-------|----------|------|
| 1080p | Fast | 10s | ~$0.40 |
| 1080p | Pro | 10s | ~$0.60 |
| 4K | Pro | 10s | ~$2.40 |

**Estimated Monthly Costs** (assuming 100 briefings/month):
- 100 × 90s videos @ 1080p Pro: ~$90/month
- 100 × 90s videos @ 4K Pro: ~$360/month

### Kubernetes Resources

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| Visual Core (2-8 replicas) | 1-16 cores | 2-32 Gi | 100 Gi |
| Sentiment Agent | Existing | Existing | Existing |

---

## Security Notes

### ⚠️ IMPORTANT Security Practices

1. **Never commit API keys** - Use Kubernetes secrets only
2. **Rotate API keys regularly** - Monthly or if compromised
3. **Monitor usage** - Track generation costs and quotas
4. **Network policies** - Restrict egress to LTX-2 API only
5. **RBAC** - Limit who can view/update secrets

### Security Contexts

All services run with:
- `runAsNonRoot: true`
- `runAsUser: 1000`
- `seccompProfile.type: RuntimeDefault`
- `capabilities.drop: [ALL]`

---

## Next Phases

### Phase 2: Social Intelligence (Planned)
- Create Socials Agent (Port 8015)
- Social media monitoring and simulation
- Social narrative modeling products

### Phase 3: Simulation Engine (Planned)
- Deploy MiroFish agent swarm simulation
- GraphRAG knowledge graphs
- Scenario simulation services

### Phase 4: Content Orchestration (Planned)
- Multi-video content pipeline
- Batch processing workflows
- Quality control automation

### Phase 5: Revenue Launch (Planned)
- Visual Intelligence Reports product
- Scenario Simulation Services
- B2B Intelligence-as-a-Service

---

## File Reference

### Created Services

**Visual Core:** `/home/ranj/Project_Chimera/services/visual-core/`
- `main.py` - FastAPI application
- `config.py` - Configuration management
- `models.py` - Pydantic models
- `ltx_client.py` - LTX-2 API client
- `prompt_factory.py` - Prompt engineering templates
- `video_pipeline.py` - FFmpeg video processing
- `metrics.py` - Prometheus metrics
- `tracing.py` - OpenTelemetry tracing
- `Dockerfile` - Container definition
- `k8s-deployment.yaml` - Kubernetes manifests
- `requirements.txt` - Python dependencies

**Enhanced Sentiment Agent:** `/home/ranj/Project_Chimera/services/sentiment-agent/`
- `src/sentiment_agent/video/briefing.py` - Video briefing generator
- `src/sentiment_agent/video/integration.py` - Visual Core client
- `main.py` - Updated with video endpoints

### Demo Files

**Demos:** `/home/ranj/Project_Chimera/demos/`
- `visual-intelligence-demo.py` - End-to-end demo script
- `demo-data.py` - Sample scenarios and data
- `README.md` - Demo documentation

### Documentation

**Plans:**
- `docs/plans/2026-03-15-ltx-mirofish-integration-design.md` - Complete design document
- `docs/plans/2026-03-15-ltx-mirofish-integration-implementation.md` - Implementation plan

---

## Support

### Issues?
Check service logs first:
```bash
kubectl logs -n project-chimera deployment/visual-core
kubectl logs -n project-chimera deployment/sentiment-agent
```

### Documentation Links
- LTX-2 API: https://console.ltx.video
- LTX-2 Documentation: https://github.com/Lightricks/LTX-Video
- Project Chimera Docs: `/home/ranj/Project_Chimera/docs/`

---

**Last Updated:** March 15, 2026
**Phase:** 1 Complete / 5 Total
**Status:** Ready for LTX-2 API Key
