# Performance Testing

Project Chimera performance tests to validate TRD latency requirements.

## TRD Latency Requirements

| Service | p95 Latency Requirement |
|---------|------------------------|
| SceneSpeak | < 2s |
| BSL | < 1s |
| Captioning | < 500ms |
| Sentiment | < 200ms |
| End-to-end | < 5s |

## Tests

### Latency Tests (Playwright)

Tests that measure actual API response times and validate they meet TRD requirements.

```bash
# Run all latency tests
cd tests/e2e
npm run test:performance

# Or run with playwright
npx playwright test tests/performance/latency.spec.ts

# Run with UI
npx playwright test tests/performance/latency.spec.ts --ui
```

### Load Tests (k6)

Tests system performance under load with 50 concurrent users.

```bash
# Run load test (requires k6)
k6 run tests/performance/load/concurrent-users.js

# Run with custom parameters
k6 run --vus 100 --duration 10m tests/performance/load/concurrent-users.js

# Run with output to JSON
k6 run --out json=test-results.json tests/performance/load/concurrent-users.js
```

## Test Reports

Test results are saved to `test-results/` directory:

- `performance-summary-*.json` - Latency test summary
- `load-test-*.json` - Load test results (if JSON output enabled)

## Setup

### Install k6 for Load Tests

```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6

# Or download from https://k6.io/docs/getting-started/installation/
```

### Start Services

```bash
# Start all services
docker-compose up -d

# Or use the development script
./scripts/start-dev.sh
```

## Interpreting Results

### Latency Test Results

The tests will output:

```
SceneSpeak Latency Statistics:
  Average: 1234.56ms
  p95: 1890.12ms
  p99: 2100.34ms
  Min: 890.12ms
  Max: 2500.56ms
```

- **p95**: 95th percentile latency - must be below TRD requirement
- **p99**: 99th percentile latency - useful for identifying outliers
- **Average**: Mean latency for all requests

### Load Test Results

k6 will output:

```
✓ SceneSpeak status is 200
✓ BSL status is 200
✓ Sentiment status is 200
✓ End-to-end completed

checks.........................: 95.00% ✓ 2850  ✗ 150
data_received..................: 12 MB  40 kB/s
data_sent......................: 15 MB  50 kB/s
http_req_blocked...............: avg=10ms    min=1ms    med=8ms     max=100ms   p(95)=20ms    p(99)=50ms
http_req_connecting............: avg=5ms     min=0ms    med=4ms     max=50ms    p(95)=10ms    p(99)=20ms
http_req_duration..............: avg=800ms   min=50ms   med=600ms   max=3000ms  p(95)=1500ms  p(99)=2000ms
```

Key metrics:
- **checks**: Percentage of checks that passed (should be >95%)
- **http_req_duration**: Request latency metrics
- **http_req_failed**: Error rate (should be <5%)

## Performance Troubleshooting

If tests fail:

1. **Check service health**:
   ```bash
   curl http://localhost:8001/health  # SceneSpeak
   curl http://localhost:8003/health  # BSL
   curl http://localhost:8004/health  # Sentiment
   ```

2. **Check resource usage**:
   ```bash
   docker stats
   ```

3. **Review logs**:
   ```bash
   docker-compose logs scenespeak-agent
   docker-compose logs bsl-agent
   ```

4. **Check OpenTelemetry traces** (if enabled):
   - Jaeger UI: http://localhost:16686
   - Grafana: http://localhost:3000

## Continuous Performance Monitoring

For ongoing monitoring, see:

- [Observability Platform](../../docs/observability/README.md)
- [SLO Framework](../../docs/observability/slo-framework.md)
- [OpenTelemetry](../../docs/observability/opentelemetry.md)
