# Visual Intelligence Report Demo

## Overview

This demo showcases the Visual Intelligence Report capability, generating executive video briefings from sentiment analysis.

## Prerequisites

1. All services running:
   ```bash
   kubectl get pods -n project-chimera
   ```

2. Services healthy:
   - sentiment-agent (port 8004)
   - visual-core (port 8014)

3. LTX-2 API key configured in visual-core-secrets

## Running the Demo

### Quick Start

```bash
cd demos
python3 visual-intelligence-demo.py
```

### What to Expect

The demo will:
1. Check service availability
2. Generate sentiment briefing video
3. Return video URL and report metadata

### Demo Scenario

**Topic:** "TechGiant Inc. Q1 Brand Sentiment Analysis"

**Output:**
- 90-second executive briefing video
- PDF summary report
- Generation metrics

### Verification

To verify the generated video:

```bash
# Download and play video
curl -O demo.mp4 {VIDEO_URL}
ffprobe demo.mp4
vlc demo.mp4  # or your preferred player
```

### Troubleshooting

**Services not responding:**
```bash
kubectl get pods -n project-chimera
kubectl logs -n project-chimera deployment/sentiment-agent
kubectl logs -n project-chimera deployment/visual-core
```

**Video generation failed:**
```bash
# Check Visual Core logs
kubectl logs -n project-chimera deployment/visual-core | grep ERROR
```

**API key issues:**
```bash
kubectl get secret visual-core-secrets -n project-chimera
```
