# MVP Service Communication Integration Tests

This directory contains integration tests for verifying service-to-service communication within the Project Chimera MVP Docker network.

## Test Coverage

The tests verify:

1. **Service Reachability**: All services can reach their dependencies via HTTP
2. **DNS Resolution**: Service names resolve correctly within the Docker network
3. **Health Endpoints**: All services respond to health checks appropriately
4. **Redis Connectivity**: Services can connect to and interact with Redis
5. **Network Isolation**: Services are properly connected to the chimera-backend network

## Test Structure

- `test_service_communication.py`: Main test suite with 14 tests
  - `TestServiceCommunication`: Tests for service-to-service communication
  - `TestServiceHealthEndpoints`: Tests for individual service health endpoints

## Prerequisites

- Docker and Docker Compose installed
- MVP services running via `docker compose -f docker-compose.mvp.yml up -d`
- All services must be healthy (check with `docker compose -f docker-compose.mvp.yml ps`)

## Running the Tests

### Option 1: Using Docker (Recommended)

Build and run the test container:

```bash
cd <repo>/tests/integration/mvp
docker build -f Dockerfile.test -t chimera-mvp-tests .
docker run --rm --network chimera_chimera-backend chimera-mvp-tests
```

### Option 2: Using Local Python (Advanced)

Install dependencies and run tests:

```bash
cd <repo>/tests/integration/mvp
pip install -r requirements.txt
pytest test_service_communication.py -v
```

Note: This requires your host to be on the chimera-backend network or service names to be resolvable.

## Test Results

Expected output:
```
======================== 13 passed, 1 skipped in 0.15s =========================
```

- **13 passed**: All communication and health endpoint tests
- **1 skipped**: Network isolation test (requires Docker CLI access)

## Troubleshooting

### Services Not Accessible

Ensure all MVP services are running:
```bash
docker compose -f docker-compose.mvp.yml ps
```

All services should show "healthy" status.

### Network Connection Issues

Verify the test container is on the correct network:
```bash
docker network ls | grep chimera
```

The network should be named `chimera_chimera-backend`.

### Redis Connection Failures

Check if Redis is running:
```bash
docker compose -f docker-compose.mvp.yml logs redis
```

## Service URL Mapping

The tests use these internal service URLs:

| Service | Internal URL | Port |
|---------|--------------|------|
| openclaw-orchestrator | http://openclaw-orchestrator:8000 | 8000 |
| scenespeak-agent | http://scenespeak-agent:8001 | 8001 |
| translation-agent | http://translation-agent:8002 | 8002 |
| sentiment-agent | http://sentiment-agent:8004 | 8004 |
| safety-filter | http://safety-filter:8006 | 8006 |
| operator-console | http://operator-console:8007 | 8007 |
| hardware-bridge | http://hardware-bridge:8008 | 8008 |
| redis | redis:6379 | 6379 |

## Health Endpoint Paths

Different services use different health endpoint paths:

- Most services: `/health`
- Safety filter: `/health/live`
- Standard response: `{"status": "healthy"}`

## Dependencies

- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- httpx>=0.24.0
- redis>=4.5.0

## Maintenance

When adding new services:

1. Add service URL to `service_urls` fixture
2. Add test cases for the new service
3. Update health endpoint paths if different
4. Update this README with the new service information
