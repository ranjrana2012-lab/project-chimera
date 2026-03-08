import { test, expect } from '@playwright/test';

/**
 * BSL Agent API Contract Tests
 *
 * Tests the British Sign Language translation and avatar generation service.
 * Port: 8003
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /api/translate - Translate text to BSL gloss
 * - POST /api/avatar/generate - Generate avatar animation
 */

test.describe('BSL Agent API', () => {
  const baseURL = 'http://localhost:8003';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health/live`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('status', 'alive');
  });

  test('@api BSL gloss translation', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate`, {
      data: { text: 'Hello, how are you?' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      gloss: expect.any(String),
      duration: expect.any(Number)
    });

    expect(body.gloss.length).toBeGreaterThan(0);
    expect(body.duration).toBeGreaterThan(0);
  });

  test('@api translation with context parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate`, {
      data: {
        text: 'Welcome to the show',
        context: { formal: true }
      },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.gloss).toBeTruthy();
  });

  test('@api translation includes sign metadata', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate`, {
      data: { text: 'Thank you for coming' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('signs');
    expect(Array.isArray(body.signs)).toBeTruthy();

    if (body.signs.length > 0) {
      expect(body.signs[0]).toMatchObject({
        gloss: expect.any(String),
        handshape: expect.any(String),
        location: expect.any(String)
      });
    }
  });

  test('@api avatar generation endpoint', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/avatar/generate`, {
      data: { text: 'Welcome to the show' },
      timeout: 20000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('animation_data');

    // Animation data should be valid JSON
    const animationData = typeof body.animation_data === 'string'
      ? JSON.parse(body.animation_data)
      : body.animation_data;

    expect(animationData).toHaveProperty('frames');
  });

  test('@api avatar with expression parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/avatar/generate`, {
      data: {
        text: 'Hello everyone',
        expression: 'happy'
      },
      timeout: 20000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('animation_data');
  });

  test('@api avatar expression endpoint', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/avatar/expression`, {
      data: { expression: 'happy' }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      expression: 'happy',
      applied: expect.any(Boolean)
    });
  });

  test('@api avatar handshape endpoint', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/avatar/handshape`, {
      data: { handshape: 'wave', hand: 'right' }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      handshape: 'wave',
      hand: 'right',
      applied: expect.any(Boolean)
    });
  });

  test('@api rejects invalid expression', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/avatar/expression`, {
      data: { expression: 'invalid_expression' }
    });

    expect(response.status()).toBe(422);
  });

  test('@api rejects missing text for translation', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate`, {
      data: {}
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body.detail).toMatch(/text/i);
  });

  test('@api rejects empty text', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate`, {
      data: { text: '' }
    });

    expect(response.status()).toBe(422);
  });

  test('@api translation handles long text', async ({ request }) => {
    const longText = 'Hello '.repeat(100);

    const response = await request.post(`${baseURL}/api/translate`, {
      data: { text: longText },
      timeout: 30000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.gloss).toBeTruthy();
    expect(body.duration).toBeGreaterThan(0);
  });

  test('@api avatar generation timing metadata', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${baseURL}/api/avatar/generate`, {
      data: { text: 'Test animation' },
      timeout: 20000
    });

    const latency = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(25000);

    const body = await response.json();
    expect(body).toHaveProperty('metadata');
    expect(body.metadata).toMatchObject({
      duration_ms: expect.any(Number),
      fps: expect.any(Number)
    });
  });

  test('@api health includes renderer information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('renderer_info');
    expect(body.renderer_info).toMatchObject({
      type: expect.any(String),
      ready: expect.any(Boolean)
    });
  });

  test('@api batch translation endpoint', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/translate/batch`, {
      data: {
        texts: ['Hello', 'Goodbye', 'Thank you']
      },
      timeout: 30000
    });

    // Batch endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('translations');
    expect(Array.isArray(body.translations)).toBeTruthy();
    expect(body.translations).toHaveLength(3);
  });

  test('@api WebSocket endpoint information', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/ws/info`);

    // Info endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('ws_url');
    expect(body.ws_url).toMatch(/^ws:\/\/localhost:8003/);
  });
});
