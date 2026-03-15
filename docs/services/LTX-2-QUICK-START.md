# LTX-2 Integration - Quick Start Card

## 🚀 5 Steps to Video Intelligence

### 1️⃣ Get Your API Key
```
https://console.ltx.video
→ Sign up → Generate API Key → Save it
```

### 2️⃣ Build & Deploy
```bash
# Build image
cd services/visual-core
docker build -t visual-core:latest .

# Deploy to k8s
kubectl apply -f k8s-deployment.yaml
```

### 3️⃣ Add Your API Key
```bash
kubectl create secret generic visual-core-secrets \
  --from-literal=LTX_API_KEY='sk-YOUR_KEY_HERE' \
  --dry-run=client -o yaml | kubectl apply -n project-chimera -f -
```

### 4️⃣ Verify Services
```bash
kubectl get pods -n project-chimera -l 'app in (visual-core,sentiment-agent)'
# Expected: Running state
```

### 5️⃣ Test It Out
```bash
cd demos
python3 visual-intelligence-demo.py
```

---

## 📋 What You Get

| Feature | Endpoint | Purpose |
|---------|----------|---------|
| Text → Video | `POST /api/v1/generate/text` | Raw video generation |
| Styled Video | `POST /api/v1/generate/prompt` | Template-based video |
| Video Stitching | `POST /api/v1/video/stitch` | Combine multiple clips |
| Sentiment Briefing | `POST /api/v1/video/briefing` | AI-powered analysis video |

---

## 🔑 API Keys

⚠️ **NEVER COMMIT ACTUAL KEYS TO GIT**

**Secret Name:** `visual-core-secrets` (namespace: project-chimera)

**Update Key:**
```bash
kubectl create secret generic visual-core-secrets \
  --from-literal=LTX_API_KEY='new-key' \
  --dry-run=client -o yaml | kubectl apply -n project-chimera -f -
```

**View Current:**
```bash
kubectl get secret visual-core-secrets -n project-chimera \
  -o jsonpath='{.data.LTX_API_KEY}'
```

---

## 🧪 Test Commands

### Health Checks
```bash
# Visual Core
curl http://visual-core:8014/health/live

# Sentiment Agent
curl http://sentiment-agent:8004/health
```

### Generate Test Video
```bash
curl -X POST "http://visual-core:8014/api/v1/generate/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test video generation",
    "style": "corporate_briefing",
    "duration": 10
  }'
```

### Briefing Video
```bash
curl -X POST "http://sentiment-agent:8004/api/v1/video/briefing?topic=Test&timeframe=7d"
```

---

## 📊 Metrics

**Access:** `http://visual-core:8014/metrics`

**Key Metrics:**
- `visual_core_video_generation_total` - Total generations
- `visual_core_video_generation_duration_seconds` - Generation time
- `visual_core_active_generations` - Concurrent generations

---

## 🐛 Debug

### Pods Not Running?
```bash
kubectl get pods -n project-chimera -l app=visual-core
kubectl logs -n project-chimera deployment/visual-core
```

### API Key Issues?
```bash
kubectl get secret visual-core-secrets -n project-chimera
```

### Service Connectivity?
```bash
kubectl exec -n project-chimera deployment/visual-core -- \
  curl -s http://sentiment-agent:8004/health
```

---

## 💰 Cost Estimates

| Video Type | Cost | Example |
|------------|------|--------|
| 10s @ 1080p Fast | ~$0.40 | Quick preview |
| 90s @ 1080p Pro | ~$5.40 | Executive briefing |
| 90s @ 4K Pro | ~$21.60 | Premium report |

**Monthly:** 100 briefings ≈ $90-360/month

---

## 📚 Full Documentation

See: `/home/ranj/Project_Chimera/docs/services/LTX-2-SETUP-GUIDE.md`

---

**Built:** March 15, 2026
**Status:** Ready for your API key! 🚀
