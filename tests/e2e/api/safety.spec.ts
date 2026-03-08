import { test, expect } from '@playwright/test';

/**
 * Safety Filter API Contract Tests
 *
 * Tests the content moderation and safety filtering service.
 * Port: 8006
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /api/moderate - Moderate content
 */

test.describe('Safety Filter API', () => {
  const baseURL = 'http://localhost:8006';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'safety-filter'
    });
    expect(body).toHaveProperty('model_loaded');
  });

  test('@api moderate safe content', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: 'Hello, welcome to the show!' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      safe: expect.any(Boolean),
      confidence: expect.any(Number),
      categories: expect.any(Object)
    });

    expect(body.confidence).toBeGreaterThan(0);
    expect(body.confidence).toBeLessThanOrEqual(1);
  });

  test('@api moderate unsafe content', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: 'This is terrible and everyone should die' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('safe');

    if (!body.safe) {
      expect(body).toHaveProperty('flagged_reason');
      expect(body).toHaveProperty('categories');
    }
  });

  test('@api moderate returns category scores', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: 'Test content for moderation' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.categories).toMatchObject({
      violence: expect.any(Number),
      hate: expect.any(Number),
      sexual: expect.any(Number),
      self_harm: expect.any(Number),
      harassment: expect.any(Number)
    });

    // All category scores should be between 0 and 1
    Object.values(body.categories).forEach((score: any) => {
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(1);
    });
  });

  test('@api moderate with threshold parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: {
        text: 'Test content',
        threshold: 0.8
      },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('safe');
  });

  test('@api rejects missing text parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: {}
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body.detail).toMatch(/text/i);
  });

  test('@api rejects empty text', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: '' }
    });

    expect(response.status()).toBe(422);
  });

  test('@api moderate includes metadata', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: 'Test for moderation metadata' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('metadata');
    expect(body.metadata).toMatchObject({
      model: expect.any(String),
      latency_ms: expect.any(Number),
      timestamp: expect.any(String)
    });
  });

  test('@api batch moderation', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate/batch`, {
      data: {
        texts: [
          'Safe content here',
          'Another safe message',
          'Test content three'
        ]
      },
      timeout: 25000
    });

    // Batch endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('results');
    expect(Array.isArray(body.results)).toBeTruthy();
    expect(body.results).toHaveLength(3);
  });

  test('@api health includes model information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('model_info');
    expect(body.model_info).toMatchObject({
      name: expect.any(String),
      loaded: expect.any(Boolean),
      version: expect.any(String)
    });
  });

  test('@api moderate completes within timeout', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${baseURL}/api/moderate`, {
      data: { text: 'Quick moderation test' },
      timeout: 10000
    });

    const latency = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(10000);
  });

  test('@api moderate with custom categories', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: {
        text: 'Test content',
        categories: ['violence', 'harassment']
      },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('safe');
  });

  test('@api content replacement suggestion', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate/replace`, {
      data: {
        text: 'This is [BAD] content',
        suggest_replacement: true
      },
      timeout: 15000
    });

    // Replacement endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('original');
    expect(body).toHaveProperty('replacement');
  });

  test('@api moderate with context awareness', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/moderate`, {
      data: {
        text: 'The character died in the scene',
        context: {
          type: 'theatrical',
          setting: 'performance'
        }
      },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    // Theatrical context should be more lenient
    expect(body).toHaveProperty('safe');
  });

  test('@api get moderation statistics', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/moderate/stats`);

    // Stats endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      total_moderated: expect.any(Number),
      flagged: expect.any(Number),
      safe: expect.any(Number)
    });
  });
});
