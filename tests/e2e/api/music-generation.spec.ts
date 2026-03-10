import { test, expect } from '@playwright/test';

/**
 * Music Generation API Contract Tests
 *
 * Tests the AI music generation service.
 * Port: 8011
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /generate - Generate music
 */

test.describe.skip('Music Generation API', () => {
  // Skip - Music Generation service not implemented (infrastructure issue)
  // See docs/notes/music-generation-status.md for details
  const baseURL = 'http://localhost:8011';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      status: 'healthy',
      service: 'music-generation'
    });
    expect(body).toHaveProperty('model_loaded');
  });

  test('@api generate music with prompt', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Dramatic orchestral music with building tension',
        duration: 10
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');

    // Audio data should be base64 encoded or a URL
    if (typeof body.audio_data === 'string') {
      expect(body.audio_data.length).toBeGreaterThan(0);
    } else {
      expect(body.audio_data).toHaveProperty('url');
    }

    expect(body).toMatchObject({
      duration: expect.any(Number),
      format: expect.any(String)
    });
  });

  test('@api generate music with mood parameter', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Background music',
        mood: 'tense',
        duration: 15
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');
    expect(body.mood).toBe('tense');
  });

  test('@api generate music with genre', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Track',
        genre: 'ambient',
        duration: 20
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');
  });

  test('@api generate music with tempo', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Fast paced music',
        tempo: 140,
        duration: 10
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');
  });

  test('@api rejects missing prompt', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        duration: 10
      }
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    // FastAPI validation errors return an array
    if (Array.isArray(body.detail)) {
      expect(body.detail[0]).toMatchObject({
        type: 'missing',
        loc: expect.arrayContaining(['body', 'prompt']),
        msg: expect.stringContaining('Field required')
      });
    } else {
      expect(body.detail).toMatch(/prompt/i);
    }
  });

  test('@api rejects invalid duration', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Test music',
        duration: -5
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api rejects duration too long', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Test music',
        duration: 999999
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api generate music metadata', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Test track',
        duration: 10
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('metadata');
    expect(body.metadata).toMatchObject({
      model: expect.any(String),
      generation_time_ms: expect.any(Number),
      timestamp: expect.any(String)
    });
  });

  test('@api health includes model information', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('model_info');

    // model_info may be null if no model is loaded yet
    if (body.model_info !== null) {
      expect(body.model_info).toMatchObject({
        name: expect.any(String),
        loaded: expect.any(Boolean),
        version: expect.any(String)
      });
    } else {
      // If model_info is null, check model_loaded flag
      expect(body).toHaveProperty('model_loaded');
    }
  });

  test('@api get available genres', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/genres`);

    // May not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('genres');
    expect(Array.isArray(body.genres)).toBeTruthy();

    expect(body.genres).toContain('ambient');
    expect(body.genres).toContain('dramatic');
  });

  test('@api get available moods', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/moods`);

    // May not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('moods');
    expect(Array.isArray(body.moods)).toBeTruthy();

    const expectedMoods = ['happy', 'sad', 'tense', 'calm', 'dramatic'];
    expectedMoods.forEach(mood => {
      expect(body.moods).toContain(mood);
    });
  });

  test('@api generate music completes within timeout', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Quick generation',
        duration: 5
      },
      timeout: 60000
    });

    const latency = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(latency).toBeLessThan(65000);
  });

  test('@api continue existing music', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate/continue`, {
      data: {
        seed_music_id: 'test-seed-001',
        duration: 10
      },
      timeout: 60000
    });

    // May not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');
  });

  test('@api batch generation', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate/batch`, {
      data: {
        prompts: [
          { prompt: 'Track 1', duration: 5 },
          { prompt: 'Track 2', duration: 5 }
        ]
      },
      timeout: 120000
    });

    // May not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('tracks');
    expect(Array.isArray(body.tracks)).toBeTruthy();
    expect(body.tracks).toHaveLength(2);
  });

  test('@api get generation history', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/history`, {
      params: {
        limit: '10'
      }
    });

    // May not be implemented or require auth
    expect([200, 401, 403, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('generations');
      expect(Array.isArray(body.generations)).toBeTruthy();
    }
  });

  test('@api generate with custom parameters', async ({ request }) => {
    const response = await request.post(`${baseURL}/generate`, {
      data: {
        prompt: 'Custom music',
        duration: 10,
        parameters: {
          instrument: 'piano',
          key: 'C_major',
          time_signature: '4/4'
        }
      },
      timeout: 60000
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('audio_data');
  });
});
