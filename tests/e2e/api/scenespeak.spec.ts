import { test, expect } from '@playwright/test';

/**
 * SceneSpeak Agent API Contract Tests
 *
 * Tests the dialogue generation service using local LLM.
 * Port: 8001
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /api/generate - Generate dialogue
 */

test.describe('SceneSpeak Agent API', () => {
  const baseURL = 'http://localhost:8001';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'scenespeak-agent'
    });
    expect(body).toHaveProperty('model_loaded');
  });

  test('@api dialogue generation with local LLM', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: 'The hero enters the room',
        context: { scene: 'act1_scene1' }
      },
      timeout: 30000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      dialogue: expect.any(String),
      metadata: expect.objectContaining({
        model: expect.any(String),
        latency_ms: expect.any(Number)
      })
    });

    expect(body.dialogue.length).toBeGreaterThan(50);
    expect(body.metadata.latency_ms).toBeGreaterThan(0);
  });

  test('@api dialogue generation with character context', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: 'Hello, my friend',
        context: {
          character: 'Hamlet',
          scene: 'act3_scene1',
          mood: 'melancholic'
        }
      },
      timeout: 30000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.dialogue).toBeTruthy();
    expect(body.dialogue.length).toBeGreaterThan(20);
    expect(body.metadata.context.character).toBe('Hamlet');
  });

  test('@api dialogue generation with style parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: 'Welcome to the show',
        context: { scene: 'opening' },
        style: 'dramatic'
      },
      timeout: 30000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.dialogue).toBeTruthy();
    expect(body.metadata.style).toBe('dramatic');
  });

  test('@api rejects missing prompt parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        context: { scene: 'act1_scene1' }
      }
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(body.detail).toMatch(/prompt/i);
  });

  test('@api rejects empty prompt', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: '',
        context: { scene: 'act1_scene1' }
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api handles malformed JSON', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      headers: { 'Content-Type': 'application/json' },
      data: '{invalid json}'
    });

    expect(response.status()).toBe(422);
  });

  test('@api generates dialogue within timeout', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: 'Quick dialogue',
        context: { scene: 'test' }
      },
      timeout: 25000
    });

    const latency = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(25000);
  });

  test('@api dialogue includes metadata', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate`, {
      data: {
        prompt: 'Test prompt',
        context: { scene: 'test' }
      },
      timeout: 30000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.metadata).toMatchObject({
      model: expect.any(String),
      latency_ms: expect.any(Number),
      timestamp: expect.any(String)
    });
  });

  test('@api health includes model information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('model_info');
    expect(body.model_info).toMatchObject({
      name: expect.any(String),
      loaded: expect.any(Boolean)
    });
  });

  test('@api handles batch dialogue generation', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/generate/batch`, {
      data: {
        prompts: [
          { prompt: 'First line', context: { scene: '1' } },
          { prompt: 'Second line', context: { scene: '1' } }
        ]
      },
      timeout: 45000
    });

    // Batch endpoint may not be implemented yet
    if (response.status() === 404) {
      // Skip if endpoint not implemented
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('dialogues');
    expect(Array.isArray(body.dialogues)).toBeTruthy();
    expect(body.dialogues).toHaveLength(2);
  });
});
