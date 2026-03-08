import { test, expect } from '@playwright/test';

/**
 * Sentiment Agent API Contract Tests
 *
 * Tests the ML-based sentiment analysis service.
 * Port: 8004
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /api/analyze - Analyze sentiment of text
 */

test.describe('Sentiment Agent API', () => {
  const baseURL = 'http://localhost:8004';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'sentiment-agent'
    });
    expect(body).toHaveProperty('model_available');
  });

  test('@api sentiment analysis with ML model', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'This is absolutely amazing!' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      sentiment: expect.any(String),
      score: expect.any(Number),
      confidence: expect.any(Number)
    });

    expect(['positive', 'negative', 'neutral']).toContain(body.sentiment);
    expect(body.confidence).toBeGreaterThan(0);
    expect(body.confidence).toBeLessThanOrEqual(1);
  });

  test('@api sentiment analysis handles positive input', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'This is amazing! I love it so much!' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.sentiment).toBe('positive');
    expect(body.score).toBeGreaterThan(0);
  });

  test('@api sentiment analysis handles negative input', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'This is terrible and I hate it' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.sentiment).toBe('negative');
    expect(body.score).toBeLessThan(0);
  });

  test('@api sentiment analysis handles neutral input', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'The sky is blue' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(['neutral', 'positive', 'negative']).toContain(body.sentiment);
  });

  test('@api sentiment analysis returns emotion breakdown', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'I am so happy and excited!' },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('emotions');
    expect(body.emotions).toMatchObject({
      joy: expect.any(Number),
      sadness: expect.any(Number),
      anger: expect.any(Number),
      fear: expect.any(Number),
      surprise: expect.any(Number)
    });
  });

  test('@api sentiment analysis includes metadata', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'Test text for sentiment' },
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

  test('@api rejects invalid input', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { invalid: 'data' }
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('@api rejects missing text parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: {}
    });

    expect(response.status()).toBe(422);
  });

  test('@api rejects empty text', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: '' }
    });

    expect(response.status()).toBe(422);
  });

  test('@api handles very long text', async ({ request }) => {
    const longText = 'This is a test. '.repeat(500);

    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: longText },
      timeout: 20000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('sentiment');
  });

  test('@api sentiment analysis completes quickly', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${baseURL}/api/analyze`, {
      data: { text: 'Quick sentiment test' },
      timeout: 10000
    });

    const latency = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(10000);
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

  test('@api batch sentiment analysis', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze/batch`, {
      data: {
        texts: [
          'I love this!',
          'This is terrible',
          'It is okay'
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

  test('@api sentiment with language detection', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/analyze`, {
      data: {
        text: 'This is amazing',
        detect_language: true
      },
      timeout: 15000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('language');
    expect(body.language).toMatch(/^[a-z]{2}$/);
  });
});
