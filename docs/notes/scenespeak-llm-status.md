# SceneSpeak Agent LLM Status

## Current State

The SceneSpeak agent requires a local LLM (Ollama) or GLM API key to function. Neither is configured.

### Health Check Status
```json
{
  "model_available": false,
  "local_llm_available": false,
  "glm_api_available": false
}
```

### E2E Tests
- **7 tests skipped** - SceneSpeak LLM-dependent tests
- **Reason**: LLM not configured (infrastructure issue)

## Infrastructure Requirements

### Option 1: Run Ollama as Docker Service (Recommended)

Add an `ollama` service to `docker-compose.yml`:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: chimera-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - chimera-backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

volumes:
  ollama_models:
```

Then pull the model:
```bash
docker compose exec ollama ollama pull llama3.2
```

### Option 2: Use Host's Ollama

If Ollama is running on the host:

1. Add `extra_hosts` to scenespeak-agent service:
```yaml
  scenespeak-agent:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

2. Set environment variable:
```bash
export SCENESPEAK_LOCAL_LLM_URL=http://host.docker.internal:11434
```

3. Ensure llama3.2 model is pulled on host:
```bash
curl http://localhost:11434/api/pull -d '{"name": "llama3.2"}'
```

### Option 3: Configure GLM API

Set the API key in `.env`:
```bash
export SCENESPEAK_GLM_API_KEY=your_api_key_here
```

## Current Configuration

- **Local LLM URL**: `http://ollama:11434` (expected Docker service)
- **Model**: `llama3.2`
- **GLM API Fallback**: enabled (but no API key configured)

## Next Steps

To enable the 7 skipped SceneSpeak E2E tests:

1. Choose one of the infrastructure options above
2. Update `docker-compose.yml` accordingly
3. Restart services: `docker compose up -d`
4. Verify: `curl http://localhost:8001/health | jq .`
5. Run E2E tests to verify

## Notes

- The llama3.2 model is ~2GB and will take time to download
- ARM64 architecture is assumed (llama3.2 has good ARM64 support)
- GPU acceleration requires nvidia-docker runtime (see docker-compose.gpu.yml)
