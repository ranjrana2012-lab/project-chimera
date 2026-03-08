# E2E Test Helper Reference Guide

Quick reference for using Project Chimera E2E test helpers.

## ChimeraTestHelper

Common utility methods for E2E tests.

### Constructor

```typescript
import { ChimeraTestHelper } from './helpers/test-utils';

// In test fixture
const helper = new ChimeraTestHelper(page, request);
```

### Methods

#### Service Health

```typescript
// Check if service is healthy (by service name)
await helper.checkServiceHealth('operator-console');
// Returns: true/false

// Check by port
await helper.checkServiceHealth('custom-service', 3000);
```

#### Service URLs

```typescript
// Get base URL for a service
const url = helper.getServiceUrl('openclaw-orchestrator');
// Returns: 'http://localhost:8000'

const url = helper.getServiceUrl('bsl-agent');
// Returns: 'http://localhost:8003'
```

#### WebSocket URLs

```typescript
// Get WebSocket URL with default path
const wsUrl = helper.getWebSocketUrl('operator-console');
// Returns: 'ws://localhost:8007/ws'

// Get WebSocket URL with custom path
const wsUrl = helper.getWebSocketUrl('bsl-agent', '/custom/path');
// Returns: 'ws://localhost:8003/custom/path'

// Create WebSocket client
const ws = await helper.createWebSocketClient('operator-console');
// Returns: Connected WebSocket

const ws = await helper.createWebSocketClient('ws://localhost:8003/ws/avatar');
// Also works with full URLs
```

#### UI State

```typescript
// Wait for show state
await helper.waitForShowState('active');
await helper.waitForShowState('ended');
await helper.waitForShowState('paused');

// Get current show state
const state = await helper.getCurrentShowState();
// Returns: 'active', 'ended', 'paused', or 'unknown'
```

#### Audience Interaction

```typescript
// Send audience reaction
await helper.sendAudienceReaction('I love this show!');
```

#### Console Control

```typescript
// Navigate to console
await helper.navigateToConsole();
// Default: http://localhost:8007/static/dashboard.html

// Start show
await helper.startShow();

// End show
await helper.endShow();
```

#### Metrics

```typescript
// Query Prometheus metric
const value = await helper.getMetric('chimera_requests_total');
// Returns: number
```

#### Service Waiting

```typescript
// Wait for service to be healthy
await helper.waitForService('scenespeak-agent');
// Default: 30 attempts, 2 second intervals

// Custom timeout
await helper.waitForService('captioning-agent', 60, 1000);
// 60 attempts, 1 second intervals
```

## ServiceHealthHelper

Manage service lifecycle for E2E tests.

### Static Methods

#### Service Information

```typescript
import { ServiceHealthHelper } from './helpers/service-health';

// Get all configured services
const services = ServiceHealthHelper.getServices();
// Returns: Array of {name, port, healthEndpoint}

// Get specific service
const orchestrator = ServiceHealthHelper.getService('openclaw-orchestrator');
// Returns: {name: 'openclaw-orchestrator', port: 8000, healthEndpoint: '/health/live'}
```

#### Health Checks

```typescript
// Check if services are already running
const running = await ServiceHealthHelper.areServicesRunning();
// Returns: true if orchestrator is healthy

// Check specific service health
const healthy = await ServiceHealthHelper.checkServiceHealth('safety-filter');
// Returns: true/false

// Wait for all services to be ready
await ServiceHealthHelper.ensureServicesReady(120000);
// Default timeout: 60000ms (1 minute)
```

#### Service Lifecycle

```typescript
// Start services via Docker Compose
await ServiceHealthHelper.startServices(
  ['docker-compose.yml', 'docker-compose.dev.yml'],
  '/path/to/project/root'
);

// Stop services
await ServiceHealthHelper.stopServices(
  '/path/to/project/root',
  false  // removeVolumes = false
);

// Restart specific service
await ServiceHealthHelper.restartService('scenespeak-agent', '/path/to/project');
```

#### Waiting

```typescript
// Wait for specific service
await ServiceHealthHelper.waitForService('captioning-agent', 8002);
// Default: 30 attempts, 2 second intervals

// Wait for multiple services (parallel)
await ServiceHealthHelper.waitForServices(
  ['bsl-agent', 'sentiment-agent'],
  30,    // maxAttempts
  2000   // interval (ms)
);
```

## WebSocketClient

Enhanced WebSocket client with automatic reconnection and message handling.

### Constructor

```typescript
import { WebSocketClient } from './helpers/websocket-client';

const client = new WebSocketClient('ws://localhost:8007/ws', {
  reconnectInterval: 2000,        // Default: 2000ms
  maxReconnectAttempts: 5,        // Default: 5
  connectionTimeout: 10000        // Default: 10000ms
});
```

### Methods

#### Connection

```typescript
// Connect to WebSocket
await client.connect();

// Check if connected
if (client.isConnected()) {
  // Connected
}

// Get ready state
const state = client.getReadyState();
// Returns: WebSocket.CONNECTING, OPEN, CLOSING, or CLOSED
```

#### Messaging

```typescript
// Send data
client.send({ type: 'ping', data: 'hello' });
client.send('raw string message');

// Wait for specific message type
const message = await client.waitForMessage('pong', 10000);
// Returns: { type: 'pong', ... }

// Wait for multiple messages (in order)
const messages = await client.waitForMessages(['connected', 'ready'], 15000);
// Returns: [{type: 'connected'}, {type: 'ready'}]
```

#### Message History

```typescript
// Get all messages
const all = client.getMessages();

// Get filtered messages
const pongs = client.getMessages('pong');

// Get last message of type
const lastPong = client.getLastMessage('pong');

// Clear history
client.clearMessages();
```

#### Event Handlers

```typescript
// Register handler for message type
client.on('update', (msg) => {
  console.log('Update:', msg);
});

// Remove handler
client.off('update', handler);
```

#### Cleanup

```typescript
// Close connection
client.close(1000, 'Normal closure');

// Manual close (prevents auto-reconnect)
client.close();
```

### Factory Function

```typescript
import { createWebSocketClient } from './helpers/websocket-client';

// Create and connect in one step
const client = await createWebSocketClient('ws://localhost:8007/ws');
```

## Service Names Reference

Available services for `getServiceUrl()`, `getWebSocketUrl()`, and `checkServiceHealth()`:

| Service Name | Port | Description |
|-------------|------|-------------|
| `openclaw-orchestrator` | 8000 | Main orchestrator service |
| `scenespeak-agent` | 8001 | Scene description agent |
| `captioning-agent` | 8002 | Caption generation service |
| `bsl-agent` | 8003 | BSL avatar service |
| `sentiment-agent` | 8004 | Sentiment analysis service |
| `lighting-sound-music` | 8005 | Lighting, sound, and music control |
| `safety-filter` | 8006 | Content moderation service |
| `operator-console` | 8007 | Operator dashboard |
| `music-generation` | 8011 | Music generation service |

## WebSocket Paths Reference

Default WebSocket paths for `getWebSocketUrl()`:

| Service | Default Path | Full URL |
|---------|-------------|----------|
| `operator-console` | `/ws` | `ws://localhost:8007/ws` |
| `bsl-agent` | `/ws/avatar` | `ws://localhost:8003/ws/avatar` |
| `captioning-agent` | `/v1/stream` | `ws://localhost:8002/v1/stream` |
| `openclaw-orchestrator` | `/ws` | `ws://localhost:8000/ws` |

## Common Patterns

### Test Fixture

```typescript
import { test, expect } from '@playwright/test';
import { ChimeraTestHelper } from '../helpers/test-utils';

test.beforeEach(async ({ page, request }) => {
  const helper = new ChimeraTestHelper(page, request);

  // Ensure service is healthy
  await helper.waitForService('operator-console');

  // Navigate to console
  await helper.navigateToConsole();
});

test('operator console loads', async ({ page, request }) => {
  const helper = new ChimeraTestHelper(page, request);

  // Test implementation
  await expect(page.locator('[data-testid="show-status"]')).toBeVisible();
});
```

### WebSocket Test

```typescript
test('WebSocket connection', async ({ page, request }) => {
  const helper = new ChimeraTestHelper(page, request);
  const ws = await helper.createWebSocketClient('operator-console');

  // Wait for connection message
  const msg = await ws.waitForMessage('connected');

  expect(msg.type).toBe('connected');

  ws.close();
});
```

### Service Health Test

```typescript
test('all services healthy', async () => {
  const helper = new ServiceHealthHelper();

  const services = helper.getServices();

  for (const service of services) {
    const healthy = await helper.checkServiceHealth(service.name);
    expect(healthy).toBe(true);
  }
});
```

### Service URL Test

```typescript
test('API endpoint works', async ({ page, request }) => {
  const helper = new ChimeraTestHelper(page, request);
  const url = helper.getServiceUrl('scenespeak-agent');

  const response = await request.get(`${url}/api/v1/status`);

  expect(response.ok()).toBe(true);
});
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BASE_URL` | Base URL for tests | `http://localhost:8007` |
| `STOP_SERVICES` | Stop services after tests | `false` |

## Troubleshooting

### Services Not Found

```typescript
// Check service name
const services = ServiceHealthHelper.getServices();
console.log(services.map(s => s.name));
// Use exact name from this list
```

### Health Check Failing

```typescript
// Check service health endpoint
const service = ServiceHealthHelper.getService('safety-filter');
console.log(`Health endpoint: http://localhost:${service.port}${service.healthEndpoint}`);

// Test manually
curl http://localhost:8006/health/live
```

### WebSocket Connection Failing

```typescript
// Verify WebSocket URL
const url = helper.getWebSocketUrl('bsl-agent');
console.log(`Connecting to: ${url}`);

// Check service is running
await helper.waitForService('bsl-agent');
```

### TypeScript Errors

```typescript
// Ensure proper imports
import { ChimeraTestHelper } from './helpers/test-utils';
import { ServiceHealthHelper } from './helpers/service-health';
import { WebSocketClient, createWebSocketClient } from './helpers/websocket-client';
```

## See Also

- [Test Infrastructure Fixes](./TEST_INFRASTRUCTURE_FIXES.md) - Details on recent fixes
- [E2E Testing Guide](../docs/testing/e2e-testing-guide.md) - Comprehensive testing guide
- [Playwright Documentation](https://playwright.dev/) - Official Playwright docs
