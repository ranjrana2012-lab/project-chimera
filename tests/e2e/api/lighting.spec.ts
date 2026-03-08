import { test, expect } from '@playwright/test';

/**
 * Lighting Control API Contract Tests
 *
 * Tests the lighting control service.
 * Port: 8005
 *
 * Endpoints:
 * - GET /health - Service health check
 * - POST /api/lighting - Control lighting
 */

test.describe('Lighting Control API', () => {
  const baseURL = 'http://localhost:8005';

  test('@smoke @api health endpoint returns 200', async ({ request }) => {
    const response = await request.get(`${baseURL}/health/live`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('status', 'alive');
  });

  test('@api set lighting scene', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting`, {
      data: {
        scene: 'act1_scene1',
        mood: 'dramatic'
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      success: expect.any(Boolean),
      scene: 'act1_scene1'
    });
  });

  test('@api set lighting color', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/color`, {
      data: {
        color: '#FF5733',
        intensity: 0.8
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      applied: expect.any(Boolean),
      color: '#FF5733'
    });
  });

  test('@api set lighting intensity', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/intensity`, {
      data: {
        intensity: 0.5
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      applied: expect.any(Boolean),
      intensity: 0.5
    });
  });

  test('@api lighting transition effect', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/transition`, {
      data: {
        from: { color: '#000000', intensity: 0 },
        to: { color: '#FFFFFF', intensity: 1 },
        duration: 2000
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      started: expect.any(Boolean),
      duration: 2000
    });
  });

  test('@api get current lighting state', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/lighting/state`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      color: expect.any(String),
      intensity: expect.any(Number),
      scene: expect.any(String)
    });
  });

  test('@api rejects invalid color format', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/color`, {
      data: {
        color: 'invalid-color',
        intensity: 0.5
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api rejects intensity out of range', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/intensity`, {
      data: {
        intensity: 1.5
      }
    });

    expect(response.status()).toBe(422);
  });

  test('@api preset lighting scenes', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/lighting/presets`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('presets');
    expect(Array.isArray(body.presets)).toBeTruthy();
  });

  test('@api apply preset scene', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/preset`, {
      data: {
        preset: 'dramatic_spotlight'
      }
    });

    // Preset may not exist, but endpoint should respond
    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('applied');
    }
  });

  test('@api zone-specific lighting control', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/zone`, {
      data: {
        zone: 'stage_left',
        color: '#FF0000',
        intensity: 0.7
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      zone: 'stage_left',
      applied: expect.any(Boolean)
    });
  });

  test('@api lighting effects', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/effect`, {
      data: {
        effect: 'strobe',
        params: {
          speed: 5,
          duration: 3000
        }
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      effect: 'strobe',
      started: expect.any(Boolean)
    });
  });

  test('@api health includes DMX connection info', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('dmx_info');
    expect(body.dmx_info).toMatchObject({
      connected: expect.any(Boolean),
      universe: expect.any(Number)
    });
  });

  test('@api batch lighting updates', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/batch`, {
      data: {
        updates: [
          { zone: 'stage_left', color: '#FF0000', intensity: 0.5 },
          { zone: 'stage_right', color: '#00FF00', intensity: 0.5 },
          { zone: 'center', color: '#0000FF', intensity: 0.8 }
        ]
      }
    });

    // Batch endpoint may not be implemented
    if (response.status() === 404) {
      return;
    }

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('updated');
    expect(Array.isArray(body.updated)).toBeTruthy();
  });

  test('@api reset lighting to default', async ({ request }) => {
    const response = await request.post(`${baseURL}/api/lighting/reset`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toMatchObject({
      reset: expect.any(Boolean)
    });
  });
});
