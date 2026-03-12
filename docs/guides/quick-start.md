# Quick Start Guide

Get Project Chimera up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Git
- 8GB RAM minimum (16GB recommended for ML features)

## Step 1: Clone the Repository

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

## Step 2: Start Services

```bash
docker compose up -d
```

This starts all 9 services in the background.

**Services started:**
- OpenClaw Orchestrator (8000)
- SceneSpeak Agent (8001)
- Captioning Agent (8002)
- BSL Agent (8003)
- Sentiment Agent (8004)
- Lighting-Sound-Music (8005)
- Safety Filter (8006)
- Operator Console (8007)
- Music Generation (8011)

## Step 3: Verify Services are Ready

Wait for all services to be healthy (may take 1-2 minutes):

```bash
# Check all service health
curl http://localhost:8000/health/live  # Orchestrator
curl http://localhost:8003/health/live  # BSL Agent
curl http://localhost:8007/health/live  # Operator Console
```

Expected response: `{"status": "alive"}`

**Alternative**: Use the health check script:

```bash
./scripts/health-check.sh
```

## Step 4: Open Operator Console

Open your browser and navigate to:

```
http://localhost:8007
```

You should see the Operator Console dashboard with all services showing as healthy.

## Step 5: Try a Feature

### Translate Text to BSL

```bash
curl -X POST http://localhost:8003/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?"}'
```

### Generate BSL Avatar

```bash
curl -X POST http://localhost:8003/api/avatar/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello"}'
```

Then visit the avatar viewer:
```
http://localhost:8007/static/avatar-enhanced.html
```

### Analyze Sentiment

```bash
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I am happy today!"}'
```

### Generate Dialogue

```bash
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A character enters the stage and greets the audience"}'
```

## Troubleshooting

### Services not starting?

Check port conflicts:

```bash
netstat -tlnp | grep -E ':(8000|8001|8002|8003|8004|8005|8006|8007|8011)'
```

### Services not healthy?

Check service logs:

```bash
docker compose logs orchestrator
docker compose logs bsl-agent
docker compose logs operator-console
```

### Can't access Operator Console?

1. Verify service is running:
   ```bash
   curl http://localhost:8007/health/live
   ```

2. Check browser console for errors

3. Try clearing browser cache

### BSL Avatar not loading?

1. Check browser supports WebGL:
   ```
   https://get.webgl.org/
   ```

2. Check for JavaScript errors in browser console

3. Verify BSL Agent is healthy:
   ```bash
   curl http://localhost:8003/health/live
   ```

## Next Steps

- Read [Development Setup](../development/setup.md) for local development
- Explore [BSL Avatar Guides](bsl-avatar/) for avatar features
- Check [Architecture Overview](../architecture/overview.md) for system design
- See [API Endpoint Catalog](../api/endpoints.md) for all available endpoints

## Getting Help

- **Documentation**: Check [docs/index.md](../index.md) for full documentation
- **Issues**: Create an issue on GitHub
- **Community**: Join our Discord/community platform
